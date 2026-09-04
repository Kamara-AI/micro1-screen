#!/usr/bin/env python3
"""
WHY: This script is the automated regression gate for SCREEN. It runs evaluation
batches as subprocesses, parses accuracy from their stdout, compares against a
known-good baseline, and flags regressions. The subprocess-based design ensures
we test the exact same invocation path a developer would use manually.

HOW: Each batch is run via `python -m evaluation.runner --batch{N}`. Accuracy is
extracted from stdout using regex. Results are written to evaluation/results/ as a
JSON summary. A Rich table makes the output scannable at a glance.

Usage:
    python scripts/run_evals.py                          # run all 4 batches
    python scripts/run_evals.py --batch 1 2 3            # run specific batches
    python scripts/run_evals.py --fail-on-regression     # exit 1 on regression
    python scripts/run_evals.py --output-dir /tmp/evals  # custom output dir
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

# ── Baseline constants ─────────────────────────────────────────────────────────

# WHY: Hard-coded baseline from the last confirmed good run. Any accuracy drop
# beyond REGRESSION_THRESHOLD_PP from these values triggers a regression alert.
# Update these via `python scripts/update_baseline.py` after a calibration round.
BASELINE_ACCURACY: dict[str, float] = {
    "batch1": 80.0,   # Senior SWE — 10 candidates
    "batch2": 88.0,   # Senior Data Scientist — 8 candidates
    "batch3": 75.0,   # FMCG Ops Manager — 20 candidates
    "batch4": 70.0,   # Digital Marketing — 33 candidates (calibration anchors: Phase 5, range 70-76%)
}

# WHY: 5pp is a meaningful signal — within-run variance for LLM-based evaluation is
# typically 1–3pp, so 5pp indicates a real regression rather than model temperature noise.
REGRESSION_THRESHOLD_PP: float = 5.0

# ── Batch metadata for display ─────────────────────────────────────────────────

BATCH_DOMAINS: dict[str, str] = {
    "batch1": "SWE",
    "batch2": "Data Science",
    "batch3": "FMCG Ops",
    "batch4": "Marketing",
}

RESULTS_DIR = Path(__file__).parent.parent / "evaluation" / "results"


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_batch(batch_num: int) -> tuple[Optional[float], str, str]:
    """
    WHY: Running each batch as a subprocess (rather than importing the runner
    directly) tests the real invocation path and isolates batch environments —
    a failing import in one batch cannot contaminate another.

    HOW: Uses subprocess.run with capture_output=True. Parses the accuracy line
    from stdout using regex. The runner writes JSON results to evaluation/results/
    as a side effect; we read the latest JSON after the subprocess completes.

    Args:
        batch_num: Integer 1–4 identifying the batch to run.

    Returns:
        Tuple of (accuracy_float_or_None, stdout_str, stderr_str).
        accuracy is None if parsing fails (e.g. runner crashed).
    """
    cmd = [
        sys.executable, "-m", "evaluation.runner",
        f"--batch{batch_num}",
    ]

    console = Console()
    console.print(f"  [dim]Running: {' '.join(cmd)}[/dim]")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    stdout = result.stdout
    stderr = result.stderr

    if result.returncode != 0:
        console.print(f"  [red]Batch {batch_num} runner exited with code {result.returncode}[/red]")
        if stderr:
            console.print(f"  [dim red]{stderr[:500]}[/dim red]")

    # WHY: Parse "SCREEN exact match:      42%  (14/33)" from the text report
    # written to stdout. This is the canonical accuracy number — exact match only,
    # not directional. The runner writes this line to the report file and stdout.
    accuracy: Optional[float] = None
    match = re.search(r"SCREEN exact match:\s+(\d+)%", stdout)
    if match:
        accuracy = float(match.group(1))

    return accuracy, stdout, stderr


def find_latest_results_json(before_mtime: Optional[float] = None) -> Optional[Path]:
    """
    WHY: After the runner subprocess completes, it writes a timestamped JSON file
    to evaluation/results/. We find the latest one by mtime to get per-candidate data
    from the run we just triggered (not a stale file from a previous run).

    Args:
        before_mtime: If provided, only return files created after this mtime.
            Pass the mtime captured before the subprocess started.

    Returns:
        Path to the latest JSON results file, or None if no files found.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_files = sorted(
        [f for f in RESULTS_DIR.glob("*_results.json")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not json_files:
        return None

    if before_mtime is not None:
        # Return the first file newer than before_mtime
        for f in json_files:
            if f.stat().st_mtime > before_mtime:
                return f
        # Fall back to the most recent overall
        return json_files[0]

    return json_files[0]


def check_regression(
    batch_key: str,
    accuracy: float,
    baseline: float,
    threshold: float = REGRESSION_THRESHOLD_PP,
) -> bool:
    """
    WHY: A regression is defined as accuracy dropping more than threshold pp below
    the known-good baseline. The threshold accounts for LLM temperature variance
    while still catching genuine degradation.

    Args:
        batch_key: e.g. "batch1" — used to look up baseline.
        accuracy: Measured accuracy in percentage points (e.g. 80.0 for 80%).
        baseline: Baseline accuracy in percentage points.
        threshold: Max allowable drop in pp before flagging regression.

    Returns:
        True if this is a regression, False if within tolerance.
    """
    return accuracy < (baseline - threshold)


# ── Output ─────────────────────────────────────────────────────────────────────

def build_summary_table(
    results: dict[str, dict],
    run_date: str,
) -> Table:
    """
    WHY: A Rich table is scannable in seconds — the primary output for CI logs
    and local developer runs. Green/red status makes pass/fail immediately clear.

    Args:
        results: Dict keyed by batch key (e.g. "batch1") with accuracy, baseline,
            delta, and status fields.
        run_date: ISO date string for the table title.

    Returns:
        Configured Rich Table ready to print.
    """
    table = Table(
        title=f"SCREEN Eval Summary — {run_date}",
        box=box.HEAVY_OUTLINE,
        show_header=True,
        header_style="bold blue",
        show_lines=False,
    )

    table.add_column("Batch", width=10)
    table.add_column("Domain", width=14)
    table.add_column("Baseline", width=12, justify="right")
    table.add_column("This Run", width=12, justify="right")
    table.add_column("Delta", width=10, justify="right")
    table.add_column("Status", width=16)

    for batch_key, data in sorted(results.items()):
        batch_label = batch_key.replace("batch", "Batch ")
        domain = BATCH_DOMAINS.get(batch_key, "Unknown")
        baseline_str = f"{data['baseline']:.1f}%"
        accuracy_str = f"{data['accuracy']:.1f}%" if data["accuracy"] is not None else "ERROR"
        delta = data.get("delta")
        delta_str = f"{delta:+.1f}%" if delta is not None else "N/A"
        status = data["status"]

        if status == "pass":
            status_text = "[bold green]✓ PASS[/bold green]"
            delta_style = "green" if (delta is not None and delta >= 0) else "yellow"
        elif status == "regression":
            status_text = "[bold red]✗ REGRESSION[/bold red]"
            delta_style = "red"
        else:
            status_text = "[yellow]⚠ ERROR[/yellow]"
            delta_style = "red"

        table.add_row(
            batch_label,
            domain,
            baseline_str,
            accuracy_str,
            f"[{delta_style}]{delta_str}[/{delta_style}]",
            status_text,
        )

    return table


def write_summary_json(
    results: dict[str, dict],
    output_dir: Path,
    timestamp: str,
) -> Path:
    """
    WHY: A machine-readable JSON summary enables downstream CI tooling to parse
    regression status without screen-scraping Rich table output.

    Args:
        results: Per-batch result dicts with accuracy, baseline, delta, status.
        output_dir: Directory to write the summary file to.
        timestamp: ISO timestamp string for the filename.

    Returns:
        Path to the written JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    regressions = [k for k, v in results.items() if v["status"] == "regression"]
    overall_status = "regression" if regressions else "pass"

    payload = {
        "run_date": timestamp,
        "batches": results,
        "overall_status": overall_status,
        "regressions": regressions,
    }

    # Use a filesystem-safe timestamp for the filename
    safe_ts = timestamp.replace(":", "").replace("-", "").replace("T", "T")[:17] + "Z"
    out_path = output_dir / f"eval_summary_{safe_ts}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return out_path


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    WHY: argparse gives us a self-documenting CLI with --help support. The batch
    argument accepts multiple values so CI can run any subset without multiple
    script invocations.

    Returns:
        Parsed argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run SCREEN evaluation batches, detect regressions against baseline, "
            "and write a structured summary JSON."
        )
    )
    parser.add_argument(
        "--batch",
        nargs="+",
        type=int,
        choices=[1, 2, 3, 4],
        default=[1, 2, 3, 4],
        metavar="N",
        help="Batch numbers to run (default: all 4). Example: --batch 1 2 3",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Path to a JSON file with baseline accuracy overrides. "
            "Keys must match batch keys (e.g. 'batch1'). "
            "If not provided, uses the hard-coded BASELINE_ACCURACY dict."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_DIR,
        metavar="PATH",
        help=f"Directory to write eval_summary_*.json (default: {RESULTS_DIR})",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with code 1 if any batch is flagged as a regression.",
    )
    return parser.parse_args()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    WHY: The main orchestration function runs each requested batch sequentially
    (not in parallel) so CI logs are readable and so per-batch console output
    from the runner subprocess appears in order.

    Returns:
        Exit code: 0 for pass, 1 for regression (when --fail-on-regression is set).
    """
    args = parse_args()
    console = Console()

    # Load baseline — file overrides hard-coded values if provided
    baseline: dict[str, float] = dict(BASELINE_ACCURACY)
    if args.baseline_file is not None:
        if not args.baseline_file.exists():
            console.print(f"[red]Baseline file not found: {args.baseline_file}[/red]")
            return 1
        with open(args.baseline_file, encoding="utf-8") as f:
            overrides = json.load(f)
        baseline.update(overrides)
        console.print(f"[dim]Loaded baseline overrides from {args.baseline_file}[/dim]")

    now = datetime.now(timezone.utc)
    run_date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    console.print(f"\n[bold blue]SCREEN Eval Pipeline — {run_date}[/bold blue]")
    console.print(f"Batches requested: {args.batch}\n")

    results: dict[str, dict] = {}

    for batch_num in args.batch:
        batch_key = f"batch{batch_num}"
        console.print(f"[bold]Running {batch_key}...[/bold]")

        # Capture mtime before subprocess so we can find the newest results file
        pre_run_mtime = datetime.now(timezone.utc).timestamp()

        accuracy, stdout, stderr = run_batch(batch_num)

        # Find per-candidate JSON written by the runner
        latest_json = find_latest_results_json(before_mtime=pre_run_mtime)

        baseline_val = baseline.get(batch_key, 0.0)

        if accuracy is None:
            console.print(f"  [red]Could not parse accuracy from runner output.[/red]")
            if stdout:
                console.print(f"  [dim]stdout tail: {stdout[-300:]}[/dim]")
            results[batch_key] = {
                "accuracy": None,
                "baseline": baseline_val,
                "delta": None,
                "status": "error",
                "results_file": str(latest_json) if latest_json else None,
            }
        else:
            delta = accuracy - baseline_val
            is_regression = check_regression(batch_key, accuracy, baseline_val)
            status = "regression" if is_regression else "pass"

            if is_regression:
                console.print(
                    f"  [bold red]WARNING: {batch_key} regression detected! "
                    f"Accuracy {accuracy:.1f}% vs baseline {baseline_val:.1f}% "
                    f"(Δ={delta:+.1f}pp)[/bold red]"
                )
            else:
                console.print(
                    f"  [green]PASS: {batch_key} accuracy {accuracy:.1f}% "
                    f"(baseline {baseline_val:.1f}%, Δ={delta:+.1f}pp)[/green]"
                )

            results[batch_key] = {
                "accuracy": accuracy,
                "baseline": baseline_val,
                "delta": round(delta, 2),
                "status": status,
                "results_file": str(latest_json) if latest_json else None,
            }

    # ── Print summary table ────────────────────────────────────────────────────
    console.print()
    table = build_summary_table(results, run_date)
    console.print(table)

    # ── Write JSON summary ─────────────────────────────────────────────────────
    summary_path = write_summary_json(results, args.output_dir, timestamp)
    console.print(f"\n[dim]Summary written to: {summary_path}[/dim]")

    # ── Determine exit code ────────────────────────────────────────────────────
    regressions = [k for k, v in results.items() if v["status"] == "regression"]
    if regressions:
        console.print(
            f"\n[bold red]Regressions detected in: {', '.join(regressions)}[/bold red]"
        )
        if args.fail_on_regression:
            return 1
    else:
        console.print("\n[bold green]All batches passed.[/bold green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
