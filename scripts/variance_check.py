#!/usr/bin/env python3
"""
WHY: LLM-based evaluation systems have inherent non-determinism from temperature
sampling. Before trusting accuracy numbers, we need to know: how stable are the
verdicts across repeated runs? If a batch fluctuates ±10pp between runs, a 5pp
regression threshold is meaningless.

HOW: Runs the same batch N times as subprocesses, collects per-candidate verdicts
from each run's JSON output, then computes:
  - Per-candidate stability: what % of runs agree on the same verdict?
  - Overall accuracy variance in pp across runs.
  - A flag if variance exceeds the acceptable threshold (default: 5pp).

This script is a diagnostic tool — run it once per batch after any significant
prompt or model change to re-establish confidence in the regression threshold.

Usage:
    python scripts/variance_check.py --batch 4 --runs 3
    python scripts/variance_check.py --batch 1 --runs 5 --variance-threshold 3.0
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

# ── Paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"

# ── Helpers ────────────────────────────────────────────────────────────────────

DEFAULT_VARIANCE_THRESHOLD_PP: float = 5.0


def run_batch_once(batch_num: int) -> tuple[Optional[float], Optional[Path]]:
    """
    WHY: Each run is a fresh subprocess invocation — identical to how the CI
    pipeline calls the runner. This ensures variance measurements reflect real
    production variance, not in-process caching or state leakage.

    Args:
        batch_num: Batch to run (1–4).

    Returns:
        Tuple of (accuracy_or_None, results_json_path_or_None).
    """
    pre_run_mtime = datetime.now(timezone.utc).timestamp()

    cmd = [
        sys.executable, "-m", "evaluation.runner",
        f"--batch{batch_num}",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )

    stdout = result.stdout
    accuracy: Optional[float] = None

    match = re.search(r"SCREEN exact match:\s+(\d+)%", stdout)
    if match:
        accuracy = float(match.group(1))

    # Find the JSON file written by this run
    json_files = sorted(
        [
            f for f in RESULTS_DIR.glob("*_results.json")
            if f.stat().st_mtime > pre_run_mtime
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    latest_json = json_files[0] if json_files else None

    return accuracy, latest_json


def load_candidate_verdicts(json_path: Path) -> dict[str, str]:
    """
    WHY: Per-candidate verdict stability requires knowing what verdict each
    candidate received in each run. The runner saves this in the results JSON.

    Args:
        json_path: Path to a *_results.json file written by evaluation.runner.

    Returns:
        Dict mapping candidate_id → verdict string for SCREEN results.
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    screen_results: list[Optional[dict]] = data.get("screen", [])
    candidate_ids: list[str] = data.get("candidate_ids", [])

    verdicts: dict[str, str] = {}
    for i, cid in enumerate(candidate_ids):
        sr = screen_results[i] if i < len(screen_results) else None
        verdicts[cid] = sr["verdict"] if sr else "UNKNOWN"

    return verdicts


def compute_candidate_stability(
    all_verdicts: list[dict[str, str]],
) -> dict[str, float]:
    """
    WHY: Stability = what fraction of runs agree on the majority verdict. A
    candidate with 3/3 run agreement is stable; 2/3 is borderline; 1/3 means
    the verdict is essentially random for that candidate.

    HOW: For each candidate, find the most common verdict across runs and compute
    the fraction of runs that returned it. This is a simple plurality-agreement metric.

    Args:
        all_verdicts: List of (run → {candidate_id: verdict}) dicts, one per run.

    Returns:
        Dict mapping candidate_id → stability fraction (0.0–1.0).
    """
    if not all_verdicts:
        return {}

    all_candidate_ids = sorted(set().union(*[d.keys() for d in all_verdicts]))
    stability: dict[str, float] = {}

    for cid in all_candidate_ids:
        run_verdicts = [d.get(cid, "UNKNOWN") for d in all_verdicts]
        # Find plurality verdict
        verdict_counts: dict[str, int] = {}
        for v in run_verdicts:
            verdict_counts[v] = verdict_counts.get(v, 0) + 1
        majority_count = max(verdict_counts.values())
        stability[cid] = majority_count / len(run_verdicts)

    return stability


def build_variance_table(
    stability: dict[str, float],
    all_verdicts: list[dict[str, str]],
    runs: int,
) -> Table:
    """
    WHY: A per-candidate table surfaces which specific candidates are unstable,
    guiding targeted prompt improvements rather than blanket model changes.

    Args:
        stability: Dict mapping candidate_id → stability fraction.
        all_verdicts: List of per-run verdict dicts for showing the verdicts.
        runs: Total number of runs (for column headers).

    Returns:
        Configured Rich Table.
    """
    table = Table(
        title="Per-Candidate Verdict Stability",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
        show_lines=True,
    )

    table.add_column("Candidate ID", width=24)
    for i in range(runs):
        table.add_column(f"Run {i + 1}", width=12)
    table.add_column("Stability", width=10, justify="right")
    table.add_column("Stable?", width=9, justify="center")

    for cid in sorted(stability.keys()):
        stab = stability[cid]
        run_verdicts = [d.get(cid, "UNKNOWN") for d in all_verdicts]
        stable = stab >= 1.0  # All runs agreed

        row = [cid] + run_verdicts + [
            f"{stab:.0%}",
            "[green]YES[/green]" if stable else "[red]NO[/red]",
        ]
        table.add_row(*row)

    return table


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    WHY: --batch and --runs are the primary controls; --variance-threshold lets
    CI or calibration workflows set a stricter bar than the default 5pp.

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run a single SCREEN batch multiple times and measure accuracy variance "
            "and per-candidate verdict stability."
        )
    )
    parser.add_argument(
        "--batch",
        type=int,
        choices=[1, 2, 3, 4],
        required=True,
        help="Batch number to test (1–4).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        metavar="N",
        help="Number of times to run the batch (default: 3).",
    )
    parser.add_argument(
        "--variance-threshold",
        type=float,
        default=DEFAULT_VARIANCE_THRESHOLD_PP,
        metavar="PP",
        help=(
            f"Max acceptable accuracy variance in percentage points "
            f"(default: {DEFAULT_VARIANCE_THRESHOLD_PP}pp). "
            "Variance above this is flagged as UNSTABLE."
        ),
    )
    return parser.parse_args()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    WHY: Variance is measured as the range (max - min) of accuracy across runs,
    not standard deviation, because with 3 runs stdev is poorly estimated. Range
    gives an upper bound on the spread that CI can reason about conservatively.

    Returns:
        Exit code: 0 if variance is within threshold, 1 if UNSTABLE.
    """
    args = parse_args()
    console = Console()

    console.print(
        f"\n[bold blue]Variance Check — Batch {args.batch} × {args.runs} runs[/bold blue]"
    )
    console.print(
        f"Variance threshold: {args.variance_threshold:.1f}pp\n"
    )

    accuracies: list[float] = []
    all_verdicts: list[dict[str, str]] = []

    for run_idx in range(args.runs):
        console.print(f"[bold]Run {run_idx + 1}/{args.runs}...[/bold]")
        accuracy, json_path = run_batch_once(args.batch)

        if accuracy is None:
            console.print(f"  [red]Could not parse accuracy from run {run_idx + 1}[/red]")
        else:
            console.print(f"  Accuracy: {accuracy:.1f}%")
            accuracies.append(accuracy)

        if json_path is not None:
            try:
                verdicts = load_candidate_verdicts(json_path)
                all_verdicts.append(verdicts)
                console.print(f"  Results: {json_path.name}")
            except (json.JSONDecodeError, KeyError) as exc:
                console.print(f"  [yellow]Could not load per-candidate verdicts: {exc}[/yellow]")
        else:
            console.print(f"  [yellow]No JSON results file found for run {run_idx + 1}[/yellow]")

    console.print()

    # ── Accuracy variance summary ──────────────────────────────────────────────
    if len(accuracies) < 2:
        console.print("[red]Not enough successful runs to compute variance.[/red]")
        return 1

    acc_range = max(accuracies) - min(accuracies)
    acc_mean = mean(accuracies)
    acc_stdev = stdev(accuracies) if len(accuracies) >= 2 else 0.0

    unstable = acc_range > args.variance_threshold

    console.print("[bold]Accuracy Summary[/bold]")
    console.print(f"  Runs:   {[f'{a:.1f}%' for a in accuracies]}")
    console.print(f"  Mean:   {acc_mean:.1f}%")
    console.print(f"  Range:  {acc_range:.1f}pp  (max {max(accuracies):.1f}% - min {min(accuracies):.1f}%)")
    console.print(f"  StdDev: {acc_stdev:.1f}pp")

    if unstable:
        console.print(
            f"\n  [bold red]UNSTABLE: Accuracy range {acc_range:.1f}pp exceeds "
            f"threshold {args.variance_threshold:.1f}pp[/bold red]"
        )
        console.print(
            "  The regression threshold in run_evals.py may not be meaningful "
            "until variance is reduced."
        )
    else:
        console.print(
            f"\n  [bold green]STABLE: Accuracy range {acc_range:.1f}pp is within "
            f"threshold {args.variance_threshold:.1f}pp[/bold green]"
        )

    # ── Per-candidate stability table ──────────────────────────────────────────
    if all_verdicts:
        console.print()
        stability = compute_candidate_stability(all_verdicts)

        unstable_candidates = [cid for cid, s in stability.items() if s < 1.0]
        console.print(
            f"[bold]Candidate Stability[/bold] — "
            f"{len(unstable_candidates)}/{len(stability)} candidates have inconsistent verdicts"
        )

        table = build_variance_table(stability, all_verdicts, len(all_verdicts))
        console.print(table)

        if unstable_candidates:
            console.print(
                f"\n[yellow]Unstable candidates ({len(unstable_candidates)}): "
                f"{', '.join(unstable_candidates)}[/yellow]"
            )

    return 1 if unstable else 0


if __name__ == "__main__":
    sys.exit(main())
