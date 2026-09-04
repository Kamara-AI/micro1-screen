"""
WHY: The runner orchestrates the full evaluation: run all 10 candidates through
SCREEN, run all 10 through the baseline, compare verdicts against ground truth,
compute metrics, and produce a formatted comparison report.

This is the demo entry point for the hackathon. Run it with:
    python -m evaluation.runner

HOW: Async runner using asyncio.gather() for parallel execution. Rich-formatted
output table for hackathon demo. Writes results to evaluation/results/ as JSON.

The runner is deliberately separated from the metrics computation (metrics.py)
and the baseline (baseline.py) so each can be tested independently and the runner
remains a thin orchestration layer — it does not contain business logic.

SCREEN integration: calls screen.agent.graph.screening_graph with initial_state()
and extracts Decision from the final state. If SCREEN is not yet importable
(e.g. dependencies not installed), the runner falls back to placeholder output
for SCREEN results and still runs the full baseline comparison.
"""

import os
os.environ.setdefault("ENV", "dev")

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from evaluation.candidates import ALL_CANDIDATES
from evaluation.candidates.batch2 import ALL_CANDIDATES_B2
from evaluation.candidates.batch3 import ALL_CANDIDATES_B3
from evaluation.candidates.batch4 import ALL_CANDIDATES_B4
from evaluation.baseline import run_baseline_async
from evaluation.metrics import (
    verdict_accuracy,
    escalation_precision,
    escalation_recall,
    calibration_score,
    avg_cost_per_candidate,
    generate_comparison_report,
)

# ── Constants ──────────────────────────────────────────────────────────────────

RESULTS_DIR = Path(__file__).parent / "results"

# WHY: Verdict colour coding makes the Rich table scannable at a glance
# during a live hackathon demo where judges are reading from a distance.
_VERDICT_STYLES: dict[str, str] = {
    "STRONG_YES": "bold green",
    "YES": "green",
    "AMBIGUOUS": "yellow",
    "NO": "red",
    "STRONG_NO": "bold red",
    "ESCALATE": "bold magenta",
    "UNKNOWN": "dim",
}


# ── SCREEN runner ──────────────────────────────────────────────────────────────

async def _run_screen_candidate(candidate_dict: dict) -> Optional[dict]:
    """
    WHY: Wraps a single SCREEN pipeline invocation in an async function so
    asyncio.gather() can run all 10 in parallel. The graph is sync (LangGraph
    invoke), so we use asyncio.to_thread to avoid blocking the event loop.

    HOW: Imports the screening_graph and initial_state at call time (not module
    level) so the runner degrades gracefully if SCREEN's dependencies are missing —
    it returns None for that candidate rather than crashing the whole evaluation.

    Args:
        candidate_dict: One entry from ALL_CANDIDATES — contains candidate_input,
            ground_truth_verdict, cv_text, job_description.

    Returns:
        Dict with candidate_id, verdict, confidence_pct, cost_usd,
        processing_time_ms, escalation_category, primary_evidence, error.
        Returns None if SCREEN raised an unrecoverable error.
    """
    candidate_input = candidate_dict["candidate_input"]

    try:
        from screen.agent.graph import screening_graph
        from screen.schemas.state import initial_state
    except ImportError as exc:
        return {
            "candidate_id": candidate_input.candidate_id,
            "verdict": "UNKNOWN",
            "confidence_pct": 0.0,
            "cost_usd": 0.0,
            "processing_time_ms": 0,
            "escalation_category": None,
            "primary_evidence": [],
            "error": f"SCREEN import failed: {exc}",
        }

    def _run_once() -> tuple[dict, object]:
        """Run one pipeline pass. Returns (result_dict, decision_object)."""
        state = initial_state(candidate_input)
        result = screening_graph.invoke(state)
        decision = result.get("decision")
        if decision is None:
            return (
                {
                    "candidate_id": candidate_input.candidate_id,
                    "verdict": "UNKNOWN",
                    "confidence_pct": 0.0,
                    "cost_usd": result.get("total_cost_usd", 0.0),
                    "processing_time_ms": 0,
                    "escalation_category": None,
                    "primary_evidence": [],
                    "error": "Pipeline completed but decision is None",
                },
                None,
            )
        return (
            {
                "candidate_id": candidate_input.candidate_id,
                "verdict": decision.verdict,
                "confidence_pct": decision.confidence_pct,
                "cost_usd": decision.estimated_cost_usd,
                "processing_time_ms": decision.processing_time_ms,
                "escalation_category": decision.escalation_category,
                "primary_evidence": list(decision.primary_evidence),
                "error": None,
            },
            decision,
        )

    def _invoke() -> dict:
        """
        WHY: Ensemble voting is applied to candidates in the 45–92% confidence band.
        Previously the upper bound was 75%, which left STRONG_YES/YES boundary
        candidates (75–92%) on single-run scoring — LLM temperature fluctuations
        of ±5pp flipped their verdict between YES and STRONG_YES every run.

        Extending to 92% captures all threshold-adjacent verdicts:
          - 45–65%: AMBIGUOUS/YES boundary
          - 65–75%: YES borderline
          - 75–92%: YES/STRONG_YES boundary (new — was previously unprotected)

        Candidates outside this band (hard rejects at 100%, clear STRONG_NO <45%)
        are deterministic — ensemble adds no value and wastes cost.
        """
        # WHY: Ensemble band now spans 45–92% to cover the YES/STRONG_YES boundary.
        ENSEMBLE_LOW = 45.0
        ENSEMBLE_HIGH = 92.0
        ENSEMBLE_RUNS = 3

        start = time.monotonic()
        try:
            r1, d1 = _run_once()
            if d1 is None or r1["error"]:
                r1["processing_time_ms"] = int((time.monotonic() - start) * 1000)
                return r1

            conf1 = d1.confidence_pct

            # Outside ensemble band — single run is reliable
            if conf1 < ENSEMBLE_LOW or conf1 >= ENSEMBLE_HIGH:
                r1["processing_time_ms"] = int((time.monotonic() - start) * 1000)
                return r1

            # Inside band — run 2 more times, take majority verdict
            extra_results = []
            for _ in range(ENSEMBLE_RUNS - 1):
                try:
                    r_extra, d_extra = _run_once()
                    if d_extra is not None and not r_extra["error"]:
                        extra_results.append((r_extra, d_extra))
                except Exception:
                    pass  # Partial ensemble failure — use what we have

            all_pairs = [(r1, d1)] + extra_results
            verdicts = [r["verdict"] for r, _ in all_pairs]

            from collections import Counter
            counter = Counter(verdicts)
            top_verdict, top_count = counter.most_common(1)[0]

            if top_count >= 2:
                # Majority found — pick highest-confidence run with that verdict
                # WHY: explicit key= prevents dict comparison when confidence_pct values
                # are tied — default tuple sort falls through to dict.__lt__ which fails.
                majority = [(r["confidence_pct"], r) for r, _ in all_pairs if r["verdict"] == top_verdict]
                majority.sort(key=lambda x: x[0], reverse=True)
                winner = majority[0][1]
            else:
                # No majority — pick median confidence run
                sorted_by_conf = sorted(all_pairs, key=lambda x: x[0]["confidence_pct"])
                winner = sorted_by_conf[len(sorted_by_conf) // 2][0]

            winner["processing_time_ms"] = int((time.monotonic() - start) * 1000)
            return winner

        except Exception as exc:
            return {
                "candidate_id": candidate_input.candidate_id,
                "verdict": "UNKNOWN",
                "confidence_pct": 0.0,
                "cost_usd": 0.0,
                "processing_time_ms": int((time.monotonic() - start) * 1000),
                "escalation_category": None,
                "primary_evidence": [],
                "error": str(exc),
            }

    return await asyncio.to_thread(_invoke)


async def _run_baseline_candidate(candidate_dict: dict) -> dict:
    """
    WHY: Wraps baseline execution in an async function for parallel gather().
    The baseline is already async-wrapped in baseline.py — this function adds
    the candidate_id field to the returned dict so the runner can correlate results.

    Args:
        candidate_dict: One entry from ALL_CANDIDATES.

    Returns:
        Baseline result dict with candidate_id added.
    """
    candidate_input = candidate_dict["candidate_input"]
    result = await run_baseline_async(
        cv_text=candidate_dict["cv_text"],
        job_description=candidate_dict["job_description"],
    )
    result["candidate_id"] = candidate_input.candidate_id
    return result


# ── Rich display ───────────────────────────────────────────────────────────────

def _build_results_table(
    screen_results: list[Optional[dict]],
    baseline_results: list[dict],
    ground_truths: list[str],
    candidate_ids: list[str],
) -> Table:
    """
    WHY: The Rich table is the primary visual output for the hackathon demo.
    Judges should be able to scan it in 30 seconds and understand: SCREEN got more
    right, escalated the right cases, and has meaningful confidence scores.

    HOW: Builds a Rich Table with colour-coded verdicts and tick/cross indicators
    for correctness. Confidence is shown only for SCREEN (baseline has no structured
    confidence output).

    Args:
        screen_results: List of SCREEN result dicts (or None if SCREEN failed).
        baseline_results: List of baseline result dicts.
        ground_truths: List of ground truth verdict strings.
        candidate_ids: List of candidate ID strings.

    Returns:
        A configured Rich Table ready to print.
    """
    table = Table(
        title="SCREEN vs Baseline — Candidate Verdicts",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
        show_lines=True,
    )

    table.add_column("ID", style="dim", width=22)
    table.add_column("Ground Truth", width=12)
    table.add_column("SCREEN", width=12)
    table.add_column("SCR OK", width=7, justify="center")
    table.add_column("Confidence", width=10, justify="right")
    table.add_column("Baseline", width=12)
    table.add_column("BAS OK", width=7, justify="center")
    table.add_column("Cost (SCREEN)", width=13, justify="right")

    for i, cid in enumerate(candidate_ids):
        gt = ground_truths[i]
        sr = screen_results[i]
        br = baseline_results[i]

        sv = sr["verdict"] if sr else "UNKNOWN"
        bv = br["verdict"] if br else "UNKNOWN"

        scr_ok = sv == gt
        bas_ok = bv == gt

        scr_ok_text = Text("[OK]" if scr_ok else "[X]", style="green" if scr_ok else "red")
        bas_ok_text = Text("[OK]" if bas_ok else "[X]", style="green" if bas_ok else "red")

        conf_str = f"{sr['confidence_pct']:.0f}%" if sr and sr["confidence_pct"] > 0 else "—"
        cost_str = f"${sr['cost_usd']:.4f}" if sr and sr.get("cost_usd") else "—"

        table.add_row(
            cid,
            Text(gt, style=_VERDICT_STYLES.get(gt, "")),
            Text(sv, style=_VERDICT_STYLES.get(sv, "")),
            scr_ok_text,
            conf_str,
            Text(bv, style=_VERDICT_STYLES.get(bv, "")),
            bas_ok_text,
            cost_str,
        )

    return table


def _build_metrics_panel(
    screen_results: list[Optional[dict]],
    baseline_results: list[dict],
    ground_truths: list[str],
    candidate_ids: list[str],
) -> Panel:
    """
    WHY: A summary panel below the table gives judges the headline numbers
    without needing to count the table rows. The accuracy delta is the most
    important single number in the demo.

    Args:
        screen_results: SCREEN result dicts.
        baseline_results: Baseline result dicts.
        ground_truths: Ground truth verdict strings.
        candidate_ids: Candidate IDs (for escalation set building).

    Returns:
        Rich Panel containing the summary metrics.
    """
    n = len(ground_truths)

    screen_verdicts = [r["verdict"] if r else "UNKNOWN" for r in screen_results]
    baseline_verdicts = [r["verdict"] if r else "UNKNOWN" for r in baseline_results]

    screen_acc = verdict_accuracy(screen_verdicts, ground_truths)
    baseline_acc = verdict_accuracy(baseline_verdicts, ground_truths)
    delta = screen_acc - baseline_acc

    screen_correct = [v == gt for v, gt in zip(screen_verdicts, ground_truths)]
    baseline_correct = [v == gt for v, gt in zip(baseline_verdicts, ground_truths)]

    screen_confs = [r["confidence_pct"] if r else 50.0 for r in screen_results]
    calibration = calibration_score(screen_confs, screen_correct)

    # Escalation metrics
    gt_escalate_ids = [candidate_ids[i] for i in range(n) if ground_truths[i] == "ESCALATE"]
    screen_escalate_ids = [candidate_ids[i] for i in range(n) if screen_verdicts[i] == "ESCALATE"]
    baseline_escalate_ids = [
        candidate_ids[i] for i in range(n) if baseline_verdicts[i] == "ESCALATE"
    ]

    scr_esc_prec = escalation_precision(screen_escalate_ids, gt_escalate_ids)
    scr_esc_rec = escalation_recall(screen_escalate_ids, gt_escalate_ids)
    bas_esc_prec = escalation_precision(baseline_escalate_ids, gt_escalate_ids)
    bas_esc_rec = escalation_recall(baseline_escalate_ids, gt_escalate_ids)

    screen_costs = [r.get("cost_usd", 0.0) if r else 0.0 for r in screen_results]
    avg_screen_cost = avg_cost_per_candidate(screen_costs)

    delta_colour = "green" if delta >= 0 else "red"
    delta_symbol = "+" if delta >= 0 else ""

    lines = [
        f"[bold]Accuracy[/bold]",
        f"  SCREEN:   [bold]{screen_acc:.0%}[/bold]  ({sum(screen_correct)}/{n} correct)",
        f"  Baseline: [bold]{baseline_acc:.0%}[/bold]  ({sum(baseline_correct)}/{n} correct)",
        f"  Delta:    [{delta_colour}][bold]{delta_symbol}{delta:.0%}[/bold][/{delta_colour}]",
        "",
        f"[bold]Escalation (SCREEN)[/bold]",
        f"  Precision: {scr_esc_prec:.0%}  |  Recall: {scr_esc_rec:.0%}",
        f"[bold]Escalation (Baseline)[/bold]",
        f"  Precision: {bas_esc_prec:.0%}  |  Recall: {bas_esc_rec:.0%}",
        "",
        f"[bold]Calibration (SCREEN, Brier-based)[/bold]  {calibration:.3f}",
        f"  (1.0 = perfect, 0.75 = random baseline)",
        "",
        f"[bold]Avg cost/candidate (SCREEN)[/bold]  ${avg_screen_cost:.4f}",
    ]

    return Panel("\n".join(lines), title="Summary Metrics", border_style="blue")


# ── Save results ───────────────────────────────────────────────────────────────

def _save_results(
    screen_results: list[Optional[dict]],
    baseline_results: list[dict],
    ground_truths: list[str],
    candidate_ids: list[str],
    report: str,
) -> Path:
    """
    WHY: Persisting results to JSON enables post-demo analysis and iteration.
    If we want to improve SCREEN's accuracy, we need the historical baseline
    to compare against — not just the terminal output.

    HOW: Writes three files to evaluation/results/:
      - {timestamp}_screen.json — all SCREEN results
      - {timestamp}_baseline.json — all baseline results
      - {timestamp}_report.txt — the text comparison report

    Args:
        screen_results: SCREEN result dicts.
        baseline_results: Baseline result dicts.
        ground_truths: Ground truth strings.
        candidate_ids: Candidate IDs for correlation.
        report: Formatted text report from generate_comparison_report().

    Returns:
        Path to the results directory where files were written.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    payload = {
        "timestamp": timestamp,
        "n_candidates": len(ground_truths),
        "ground_truths": ground_truths,
        "candidate_ids": candidate_ids,
        "screen": screen_results,
        "baseline": baseline_results,
    }

    results_path = RESULTS_DIR / f"{timestamp}_results.json"
    report_path = RESULTS_DIR / f"{timestamp}_report.txt"

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return RESULTS_DIR


# ── Main orchestrator ──────────────────────────────────────────────────────────

async def run_evaluation(
    run_screen: bool = True,
    run_baseline: bool = True,
    save: bool = True,
    batch: str = "1",
) -> dict:
    """
    WHY: The top-level async orchestrator. Separated from the main guard so it
    can be called programmatically (e.g. from a test or a Jupyter notebook) without
    subprocess overhead.

    HOW: Uses asyncio.gather() to run all 10 SCREEN candidates in parallel and
    all 10 baseline candidates in parallel. The two batches themselves run
    sequentially (baseline after SCREEN) to make console output readable.

    Args:
        run_screen: Whether to run the SCREEN pipeline. Set to False to compare
            only the baseline against ground truth (useful when SCREEN is not yet
            fully wired).
        run_baseline: Whether to run the baseline. Set to False for SCREEN-only
            evaluation.
        save: Whether to persist results to evaluation/results/.

    Returns:
        Dict containing:
            - screen_results: list of SCREEN result dicts
            - baseline_results: list of baseline result dicts
            - ground_truths: list of ground truth strings
            - candidate_ids: list of candidate ID strings
            - report: formatted text report string
            - results_dir: str path to where results were saved (or None)
    """
    console = Console()
    if batch == "2":
        candidates = ALL_CANDIDATES_B2
    elif batch == "3":
        candidates = ALL_CANDIDATES_B3
    elif batch == "4":
        candidates = ALL_CANDIDATES_B4
    else:
        candidates = ALL_CANDIDATES
    n = len(candidates)

    ground_truths = [c["ground_truth_verdict"] for c in candidates]
    candidate_ids = [c["candidate_input"].candidate_id for c in candidates]

    console.print(
        Panel(
            f"Running SCREEN evaluation suite — [bold]{n} candidates[/bold]",
            border_style="blue",
        )
    )

    # ── Run SCREEN ─────────────────────────────────────────────────────────────
    screen_results: list[Optional[dict]]
    if run_screen:
        console.print("\n[bold blue]Running SCREEN pipeline (parallel)...[/bold blue]")
        start = time.monotonic()
        screen_results = list(
            await asyncio.gather(*[_run_screen_candidate(c) for c in candidates])
        )
        elapsed = time.monotonic() - start
        errors = [r for r in screen_results if r and r.get("error")]
        console.print(
            f"  SCREEN complete: {n} candidates in {elapsed:.1f}s "
            f"({'[red]' + str(len(errors)) + ' errors[/red]' if errors else '[green]no errors[/green]'})"
        )
        if errors:
            for r in errors:
                console.print(f"    [red]  {r['candidate_id']}: {r['error']}[/red]")
    else:
        console.print("[dim]Skipping SCREEN pipeline (run_screen=False)[/dim]")
        screen_results = [None] * n

    # ── Run baseline ───────────────────────────────────────────────────────────
    baseline_results: list[dict]
    if run_baseline:
        console.print("\n[bold blue]Running baseline (parallel)...[/bold blue]")
        start = time.monotonic()
        baseline_results = list(
            await asyncio.gather(*[_run_baseline_candidate(c) for c in candidates])
        )
        elapsed = time.monotonic() - start
        errors_b = [r for r in baseline_results if r.get("error")]
        console.print(
            f"  Baseline complete: {n} candidates in {elapsed:.1f}s "
            f"({'[red]' + str(len(errors_b)) + ' errors[/red]' if errors_b else '[green]no errors[/green]'})"
        )
    else:
        console.print("[dim]Skipping baseline (run_baseline=False)[/dim]")
        baseline_results = [{"candidate_id": cid, "verdict": "UNKNOWN", "cost_usd": 0.0}
                            for cid in candidate_ids]

    # ── Display results ────────────────────────────────────────────────────────
    console.print()
    table = _build_results_table(screen_results, baseline_results, ground_truths, candidate_ids)
    console.print(table)
    console.print()

    metrics_panel = _build_metrics_panel(
        screen_results, baseline_results, ground_truths, candidate_ids
    )
    console.print(metrics_panel)

    # ── Generate text report ───────────────────────────────────────────────────
    screen_for_report = [
        r if r else {"candidate_id": candidate_ids[i], "verdict": "UNKNOWN",
                     "confidence_pct": 0.0, "cost_usd": 0.0}
        for i, r in enumerate(screen_results)
    ]
    report = generate_comparison_report(screen_for_report, baseline_results, ground_truths)

    # ── Save ───────────────────────────────────────────────────────────────────
    results_dir_path: Optional[str] = None
    if save:
        results_dir_path = str(
            _save_results(screen_results, baseline_results, ground_truths, candidate_ids, report)
        )
        console.print(f"\n[dim]Results saved to: {results_dir_path}[/dim]")

    return {
        "screen_results": screen_results,
        "baseline_results": baseline_results,
        "ground_truths": ground_truths,
        "candidate_ids": candidate_ids,
        "report": report,
        "results_dir": results_dir_path,
    }


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    WHY: Direct execution via `python -m evaluation.runner` is the hackathon
    demo entry point. Command-line flags control which systems are evaluated
    so judges can see baseline-only, SCREEN-only, or full comparison modes.

    Usage:
        python -m evaluation.runner                  # full comparison
        python -m evaluation.runner --no-screen      # baseline only
        python -m evaluation.runner --no-baseline    # SCREEN only
        python -m evaluation.runner --no-save        # don't write files
    """
    import sys

    args = sys.argv[1:]
    do_screen = "--no-screen" not in args
    do_baseline = "--no-baseline" not in args
    do_save = "--no-save" not in args
    do_batch = "4" if "--batch4" in args else ("3" if "--batch3" in args else ("2" if "--batch2" in args else "1"))

    asyncio.run(
        run_evaluation(
            run_screen=do_screen,
            run_baseline=do_baseline,
            save=do_save,
            batch=do_batch,
        )
    )
