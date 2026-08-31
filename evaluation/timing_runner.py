"""
WHY: A sequential timing harness for batch4 that simulates real-world candidate
arrival — one application at a time, f01 through f50. Unlike runner.py which
uses asyncio.gather() for parallel evaluation, this runner processes each
candidate serially so we can measure per-candidate latency as it would appear
in a live screening queue.

HOW: Each candidate is processed with asyncio.to_thread (same pattern as
runner.py's _run_screen_candidate) to keep the event loop non-blocking while
the synchronous LangGraph graph.invoke() runs in a thread. After each candidate
completes, a live result line is printed immediately. After all 50, a Rich
summary table with timing buckets (hard-gate vs LLM-path) is rendered.

Usage:
    python -m evaluation.timing_runner
"""

import os
os.environ.setdefault("ENV", "dev")

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from evaluation.candidates.batch4 import ALL_CANDIDATES_B4

# ── Constants ──────────────────────────────────────────────────────────────────

# WHY: Same verdict colour map as runner.py — visual consistency across all
# evaluation entry points so engineers aren't context-switching between tools.
_VERDICT_STYLES: dict[str, str] = {
    "STRONG_YES": "bold green",
    "YES": "green",
    "AMBIGUOUS": "yellow",
    "NO": "red",
    "STRONG_NO": "bold red",
    "ESCALATE": "bold magenta",
    "UNKNOWN": "dim",
}

# WHY: STRONG_NO candidates that skip the LLM path are handled by a hard gate
# in the SCREEN pipeline. We track them separately because their latency profile
# is fundamentally different — milliseconds vs seconds — and mixing them into
# the mean would obscure the LLM-path performance.
_HARD_GATE_VERDICTS = {"STRONG_NO"}


# ── Core candidate runner ──────────────────────────────────────────────────────

async def _run_one(candidate_dict: dict) -> dict:
    """
    WHY: Wraps a single SCREEN pipeline invocation for sequential processing.
    Uses asyncio.to_thread so the synchronous LangGraph invoke() does not block
    the event loop. Returns a result dict regardless of pipeline errors so the
    harness always produces 50 rows.

    Args:
        candidate_dict: One entry from ALL_CANDIDATES_B4.

    Returns:
        Dict with candidate_id, verdict, confidence_pct, cost_usd,
        processing_time_s (float seconds), ground_truth_verdict, error.
    """
    candidate_input = candidate_dict["candidate_input"]
    ground_truth = candidate_dict["ground_truth_verdict"]

    try:
        from screen.agent.graph import screening_graph
        from screen.schemas.state import initial_state
    except ImportError as exc:
        return {
            "candidate_id": candidate_input.candidate_id,
            "verdict": "UNKNOWN",
            "confidence_pct": 0.0,
            "cost_usd": 0.0,
            "processing_time_s": 0.0,
            "ground_truth_verdict": ground_truth,
            "error": f"SCREEN import failed: {exc}",
        }

    def _invoke() -> dict:
        """
        WHY: Isolated sync function for asyncio.to_thread. The try/except ensures
        a single candidate failure is captured and surfaced, not silently swallowed.
        wall_start uses time.monotonic() for reliable elapsed measurement across
        thread boundaries.
        """
        wall_start = time.monotonic()
        state = initial_state(candidate_input)
        try:
            result = screening_graph.invoke(state)
            elapsed_s = time.monotonic() - wall_start

            decision = result.get("decision")
            if decision is None:
                return {
                    "candidate_id": candidate_input.candidate_id,
                    "verdict": "UNKNOWN",
                    "confidence_pct": 0.0,
                    "cost_usd": result.get("total_cost_usd", 0.0),
                    "processing_time_s": elapsed_s,
                    "ground_truth_verdict": ground_truth,
                    "error": "Pipeline completed but decision is None",
                }

            return {
                "candidate_id": candidate_input.candidate_id,
                "verdict": decision.verdict,
                "confidence_pct": decision.confidence_pct,
                "cost_usd": decision.estimated_cost_usd,
                "processing_time_s": elapsed_s,
                "ground_truth_verdict": ground_truth,
                "error": None,
            }
        except Exception as exc:
            elapsed_s = time.monotonic() - wall_start
            return {
                "candidate_id": candidate_input.candidate_id,
                "verdict": "UNKNOWN",
                "confidence_pct": 0.0,
                "cost_usd": 0.0,
                "processing_time_s": elapsed_s,
                "ground_truth_verdict": ground_truth,
                "error": str(exc),
            }

    return await asyncio.to_thread(_invoke)


# ── Live result line ───────────────────────────────────────────────────────────

def _format_live_line(
    result: dict,
    wall_elapsed_s: float,
    module_name: str,
) -> Text:
    """
    WHY: Printing a result immediately after each candidate finishes gives the
    operator real-time visibility into screening progress — they don't have to
    wait for all 50 to complete before seeing any output.

    Format: [HH:MM:SS elapsed] f01_strong_yes → STRONG_YES (96%, $0.006, 4.2s) [OK]

    Args:
        result: The result dict from _run_one().
        wall_elapsed_s: Seconds since the first candidate started.
        module_name: Short module name like "f01_strong_yes".

    Returns:
        A Rich Text object with colour styling applied.
    """
    hours = int(wall_elapsed_s // 3600)
    minutes = int((wall_elapsed_s % 3600) // 60)
    seconds = int(wall_elapsed_s % 60)
    elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    verdict = result["verdict"]
    conf = result["confidence_pct"]
    cost = result["cost_usd"]
    proc_s = result["processing_time_s"]
    gt = result["ground_truth_verdict"]

    correct = verdict == gt
    indicator = "[OK]" if correct else "[!!]"
    indicator_style = "bold green" if correct else "bold red"

    verdict_style = _VERDICT_STYLES.get(verdict, "")

    line = Text()
    line.append(f"[{elapsed_str}] ", style="dim")
    line.append(f"{module_name}", style="bold")
    line.append(" → ", style="dim")
    line.append(verdict, style=verdict_style)
    line.append(f" ({conf:.0f}%, ${cost:.3f}, {proc_s:.1f}s) ", style="dim")
    line.append(indicator, style=indicator_style)

    if result.get("error"):
        line.append(f"  ERR: {result['error'][:60]}", style="red dim")

    return line


# ── Summary table ──────────────────────────────────────────────────────────────

def _build_summary_panel(results: list[dict], total_wall_s: float) -> Panel:
    """
    WHY: The summary panel gives the engineering team the headline timing and
    accuracy numbers they need to decide whether SCREEN's sequential throughput
    is acceptable for a real production queue. Hard-gate vs LLM-path split is
    the key diagnostic — if hard-gate is slow, the rule engine has a problem;
    if LLM-path is slow, the model or prompt is the bottleneck.

    Args:
        results: All 50 result dicts in order.
        total_wall_s: Total wall clock time from first candidate start to last finish.

    Returns:
        Rich Panel containing the formatted summary.
    """
    n = len(results)
    if n == 0:
        return Panel("No results.", title="Timing Summary", border_style="blue")

    processing_times = [r["processing_time_s"] for r in results]
    costs = [r["cost_usd"] for r in results]

    # WHY: Separate hard-gate (STRONG_NO, no LLM spend) from LLM-path so
    # we can give meaningful averages for each processing mode rather than
    # a blended mean that obscures where time is actually going.
    hard_gate_times = [
        r["processing_time_s"]
        for r in results
        if r["verdict"] in _HARD_GATE_VERDICTS and r["cost_usd"] == 0.0
    ]
    llm_path_times = [
        r["processing_time_s"]
        for r in results
        if r["verdict"] not in _HARD_GATE_VERDICTS or r["cost_usd"] > 0.0
    ]

    mean_time = sum(processing_times) / n
    min_time = min(processing_times)
    max_time = max(processing_times)

    hard_gate_mean = (sum(hard_gate_times) / len(hard_gate_times)) if hard_gate_times else 0.0
    llm_path_mean = (sum(llm_path_times) / len(llm_path_times)) if llm_path_times else 0.0

    # Throughput: candidates per minute using total wall clock time
    throughput = (n / total_wall_s) * 60.0 if total_wall_s > 0 else 0.0

    # Accuracy
    correct = [r for r in results if r["verdict"] == r["ground_truth_verdict"]]
    accuracy = len(correct) / n

    mean_cost = sum(costs) / n

    # Format total wall time as mm:ss
    wall_m = int(total_wall_s // 60)
    wall_s = total_wall_s % 60

    lines = [
        f"[bold]Wall clock time[/bold]         {wall_m}m {wall_s:.1f}s",
        "",
        f"[bold]Per-candidate processing[/bold]",
        f"  Mean:  {mean_time:.2f}s",
        f"  Min:   {min_time:.2f}s",
        f"  Max:   {max_time:.2f}s",
        "",
        f"[bold]Path breakdown[/bold]",
        f"  Hard-gate (n={len(hard_gate_times)}):  {hard_gate_mean:.3f}s avg",
        f"  LLM-path  (n={len(llm_path_times)}):  {llm_path_mean:.2f}s avg",
        "",
        f"[bold]Throughput[/bold]              {throughput:.1f} candidates/min",
        "",
        f"[bold]Accuracy[/bold]               "
        f"[{'green' if accuracy >= 0.8 else 'yellow' if accuracy >= 0.6 else 'red'}]"
        f"{accuracy:.0%} ({len(correct)}/{n})[/{'green' if accuracy >= 0.8 else 'yellow' if accuracy >= 0.6 else 'red'}]",
        "",
        f"[bold]Cost/candidate (mean)[/bold]   ${mean_cost:.4f}",
    ]

    return Panel("\n".join(lines), title="Timing Summary — Batch 4", border_style="blue")


def _build_verdict_breakdown_table(results: list[dict]) -> Table:
    """
    WHY: A per-verdict breakdown shows where the batch4 population sits on the
    STRONG_YES→STRONG_NO spectrum and how many of each the pipeline got right —
    useful for diagnosing verdict-specific accuracy problems.

    Args:
        results: All 50 result dicts.

    Returns:
        Rich Table with verdict rows.
    """
    from collections import defaultdict

    verdict_buckets: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        verdict_buckets[r["verdict"]].append(r)

    table = Table(
        title="Verdict Breakdown",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Verdict", width=14)
    table.add_column("Count", width=7, justify="right")
    table.add_column("Correct", width=8, justify="right")
    table.add_column("Avg Time", width=10, justify="right")
    table.add_column("Avg Cost", width=10, justify="right")

    verdict_order = ["STRONG_YES", "YES", "AMBIGUOUS", "NO", "STRONG_NO", "ESCALATE", "UNKNOWN"]
    for v in verdict_order:
        if v not in verdict_buckets:
            continue
        bucket = verdict_buckets[v]
        count = len(bucket)
        correct = sum(1 for r in bucket if r["verdict"] == r["ground_truth_verdict"])
        avg_time = sum(r["processing_time_s"] for r in bucket) / count
        avg_cost = sum(r["cost_usd"] for r in bucket) / count
        style = _VERDICT_STYLES.get(v, "")
        table.add_row(
            Text(v, style=style),
            str(count),
            f"{correct}/{count}",
            f"{avg_time:.2f}s",
            f"${avg_cost:.4f}",
        )

    return table


# ── Main sequential loop ───────────────────────────────────────────────────────

async def run_timing() -> None:
    """
    WHY: The top-level coroutine. Iterates over ALL_CANDIDATES_B4 sequentially
    (not parallel gather) to simulate a real queue where applications arrive one
    at a time. Each iteration awaits the previous result before starting the next,
    giving an accurate picture of serial throughput and per-candidate latency.

    HOW: Module names are derived from each candidate dict's module.__name__
    attribute (e.g. "evaluation.candidates.batch4.f01_strong_yes") — we take only
    the last segment for the live output line.
    """
    console = Console()
    candidates = ALL_CANDIDATES_B4
    n = len(candidates)

    console.print(
        Panel(
            f"[bold]SCREEN Timing Runner — Batch 4[/bold]\n"
            f"Sequential processing: {n} candidates, f01 → f50\n"
            f"[dim]Simulates real-world application arrival (one at a time)[/dim]",
            border_style="blue",
        )
    )
    console.print()

    results: list[dict] = []
    suite_start = time.monotonic()

    for i, candidate_dict in enumerate(candidates, start=1):
        # Derive short module name from the module object's __name__ attribute
        module = candidate_dict["module"]
        module_name = module.__name__.split(".")[-1]

        result = await _run_one(candidate_dict)
        results.append(result)

        wall_elapsed = time.monotonic() - suite_start
        live_line = _format_live_line(result, wall_elapsed, module_name)
        console.print(live_line)

    total_wall_s = time.monotonic() - suite_start

    console.print()
    console.print(_build_verdict_breakdown_table(results))
    console.print()
    console.print(_build_summary_panel(results, total_wall_s))


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    WHY: Direct execution via `python -m evaluation.timing_runner` always runs
    batch4 sequentially. No flags needed — this script has a single purpose:
    measure per-candidate latency under realistic serial load.
    """
    asyncio.run(run_timing())
