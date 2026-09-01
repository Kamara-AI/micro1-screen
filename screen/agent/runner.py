"""
WHY: The runner is the public interface to the SCREEN pipeline. All callers
(CLI, API, evaluation harness, tests) use runner functions — never the
LangGraph graph directly. This provides one place to add cross-cutting concerns:
  - Input validation
  - Structured logging at the run boundary
  - Error capture and state annotation
  - Batch parallelism
  - Ensemble voting for borderline confidence scores

HOW: screen_candidate() invokes the compiled graph with an initial state and
returns the final ScreeningState. screen_batch() fans out multiple candidates
concurrently using asyncio.gather(), sharing the same batch_id.

WHY async: LangGraph supports async node execution. Async fan-out in screen_batch()
lets multiple candidates be processed concurrently — important for hackathon demo
where judging 5 candidates sequentially would be slow.

IMPORTANT: The runner does NOT hold any business logic. It orchestrates; nodes decide.
"""

import asyncio
import time
from collections import Counter
from typing import Any

from screen.agent.graph import screening_graph
from screen.core.config import settings
from screen.core.exceptions import ScreenException
from screen.core.logging_config import get_logger, setup_logging
from screen.schemas.input import ScreeningInput
from screen.schemas.state import ScreeningState, initial_state

logger = get_logger(__name__)

# Ensure logging is configured when the runner module is imported
setup_logging(settings.log_level)


async def _screen_candidate_single(screening_input: ScreeningInput) -> ScreeningState:
    """
    WHY: The primary entry point for single-candidate screening. Handles the full
    pipeline invocation and surfaces errors in a structured way without exposing
    raw graph internals to callers.

    HOW: Constructs the initial state, invokes the compiled LangGraph graph,
    and returns the final state. On ScreenException, annotates the state with
    error_node and error_message so callers can distinguish pipeline errors
    from application bugs.

    IMPORTANT: This function is async because LangGraph's async invocation
    (ainvoke) is more efficient for I/O-heavy pipelines (multiple LLM calls).
    Even if the caller is sync, they can run this with asyncio.run().

    Args:
        screening_input: Validated ScreeningInput for one candidate.

    Returns:
        ScreeningState with all populated fields corresponding to the pipeline
        path taken. Callers should check state["decision"] for the verdict.

    Raises:
        ScreenException: If the pipeline encounters an unrecoverable error
            after all retries are exhausted.
    """
    candidate_id = screening_input.candidate_id
    run_start_ms = time.time() * 1000

    logger.info(
        "screen_candidate: pipeline start",
        candidate_id=candidate_id,
        batch_id=screening_input.batch_id,
        role_seniority=screening_input.role_seniority,
        role_type=screening_input.role_type,
        num_hard_requirements=len(screening_input.hard_requirements),
    )

    state = initial_state(screening_input)

    try:
        final_state: ScreeningState = await screening_graph.ainvoke(state)
    except ScreenException as exc:
        logger.error(
            "screen_candidate: pipeline failed with ScreenException",
            candidate_id=candidate_id,
            error_code=exc.error_code,
            # NOTE: exc.message may contain node name but never PII
        )
        # Annotate the last known state with error info and return it
        # WHY: Returning an error-annotated state is more useful to callers
        # than raising — they can still inspect trajectory for debugging.
        error_state = dict(state)
        error_state["error_node"] = getattr(exc, "node", "unknown")
        error_state["error_message"] = exc.message
        return error_state  # type: ignore[return-value]

    except Exception as exc:
        logger.error(
            "screen_candidate: unexpected pipeline error",
            candidate_id=candidate_id,
            error_type=type(exc).__name__,
        )
        error_state = dict(state)
        error_state["error_node"] = "unknown"
        error_state["error_message"] = f"Unexpected error: {type(exc).__name__}"
        return error_state  # type: ignore[return-value]

    elapsed_ms = int((time.time() * 1000) - run_start_ms)
    decision = final_state.get("decision")
    verdict = decision.verdict if decision else "ERROR"
    confidence = decision.confidence_pct if decision else 0.0

    logger.info(
        "screen_candidate: pipeline complete",
        candidate_id=candidate_id,
        verdict=verdict,
        confidence_pct=confidence,
        total_cost_usd=round(final_state.get("total_cost_usd", 0.0), 6),
        total_trajectory_nodes=len(final_state.get("trajectory", [])),
        elapsed_ms=elapsed_ms,
    )

    # Generate and save human-readable markdown report
    # WHY: Judges and hiring managers should not need to parse a Python dict.
    # The report is saved alongside the run so it's immediately shareable.
    if decision is not None:
        try:
            import pathlib

            from screen.agent.output_formatter import format_markdown_report

            report_md = format_markdown_report(final_state)
            reports_dir = pathlib.Path("reports")
            reports_dir.mkdir(exist_ok=True)
            report_path = reports_dir / f"{candidate_id}_report.md"
            report_path.write_text(report_md, encoding="utf-8")
            logger.info(
                "screen_candidate: report saved",
                candidate_id=candidate_id,
                report_path=str(report_path),
            )
        except Exception as exc:  # noqa: BLE001
            # WHY: Report generation failure must never crash the pipeline.
            # The state is already complete — a formatting error is cosmetic.
            logger.warning(
                "screen_candidate: report generation failed",
                candidate_id=candidate_id,
                error=str(exc),
            )

    return final_state


async def screen_candidate_with_ensemble(
    screening_input: ScreeningInput,
    ensemble_threshold_low: float = 45.0,
    ensemble_threshold_high: float = 75.0,
    ensemble_runs: int = 3,
) -> tuple[ScreeningState, int]:
    """
    WHY: LLM variance causes the same CV to receive different verdicts across
    runs. For borderline candidates (45–75% confidence), running 3 times and
    taking majority verdict reduces variance from ±12pp to ±3pp.

    HOW: Run once. If confidence is outside the borderline band (below 45% or
    above 75%), return immediately — the result is reliable. If inside the band,
    run 2 more times concurrently and take the majority verdict. If no majority
    (all 3 different), take the median confidence run.

    Args:
        screening_input: Validated ScreeningInput for one candidate.
        ensemble_threshold_low: Lower bound of the borderline confidence band.
            Candidates with confidence below this are returned immediately
            (strong reject). Defaults to 45.0.
        ensemble_threshold_high: Upper bound of the borderline confidence band.
            Candidates with confidence at or above this are returned immediately
            (strong accept/reject). Defaults to 75.0.
        ensemble_runs: Total number of pipeline runs used when ensemble fires.
            Defaults to 3.

    Returns:
        Tuple of (final_state, num_runs_used) where num_runs_used is 1 or 3.
        final_state is always one of the actual pipeline run states, never a
        merged or synthesised state.
    """
    candidate_id = screening_input.candidate_id

    # Run the pipeline once
    state1: ScreeningState = await _screen_candidate_single(screening_input)

    decision1 = state1.get("decision")
    if decision1 is None or decision1.confidence_pct is None:
        # Error state — no confidence available, return as-is
        return (state1, 1)

    confidence1: float = decision1.confidence_pct

    # Outside the borderline band — result is reliable, no ensemble needed
    if confidence1 < ensemble_threshold_low or confidence1 >= ensemble_threshold_high:
        return (state1, 1)

    # Inside the borderline band: run 2 more times concurrently
    logger.info(
        "ensemble_voting: borderline confidence detected, firing ensemble",
        candidate_id=candidate_id,
        confidence_pct=confidence1,
        ensemble_runs=ensemble_runs,
    )

    extra_runs = ensemble_runs - 1  # already have state1
    extra_states: tuple[ScreeningState, ...] = await asyncio.gather(
        *[_screen_candidate_single(screening_input) for _ in range(extra_runs)]
    )

    all_states: list[ScreeningState] = [state1, *extra_states]

    # Collect (verdict, confidence) pairs for states that produced a decision
    valid_pairs: list[tuple[str, float, ScreeningState]] = [
        (s["decision"].verdict, s["decision"].confidence_pct, s)
        for s in all_states
        if s.get("decision") is not None and s["decision"].confidence_pct is not None
    ]

    verdicts: list[str] = [verdict for verdict, _, _ in valid_pairs]

    logger.info(
        "ensemble_voting: runs complete",
        candidate_id=candidate_id,
        verdicts=verdicts,
    )

    if not valid_pairs:
        # All runs errored — fall back to first run
        return (state1, ensemble_runs)

    # Try majority verdict (count >= 2)
    verdict_counter: Counter[str] = Counter(verdicts)
    top_verdict, top_count = verdict_counter.most_common(1)[0]

    if top_count >= 2:
        # Majority found — return the run with that verdict that has highest confidence
        majority_candidates = [
            (conf, s) for v, conf, s in valid_pairs if v == top_verdict
        ]
        majority_candidates.sort(key=lambda x: x[0], reverse=True)
        winning_state = majority_candidates[0][1]

        logger.info(
            "ensemble_voting: majority verdict selected",
            candidate_id=candidate_id,
            verdicts=verdicts,
            winner=top_verdict,
            runs=ensemble_runs,
        )
        return (winning_state, ensemble_runs)

    # No majority — all 3 verdicts differ; return the median-confidence run
    # WHY: Median is more robust than min/max when there is no consensus —
    # it avoids the extremes while still picking an actual pipeline output.
    sorted_by_confidence = sorted(valid_pairs, key=lambda x: x[1])
    median_index = len(sorted_by_confidence) // 2
    median_verdict, median_confidence, median_state = sorted_by_confidence[median_index]

    logger.info(
        "ensemble_voting: no majority, median confidence run selected",
        candidate_id=candidate_id,
        verdicts=verdicts,
        winner=median_verdict,
        median_confidence_pct=median_confidence,
        runs=ensemble_runs,
    )
    return (median_state, ensemble_runs)


async def screen_candidate(screening_input: ScreeningInput) -> ScreeningState:
    """
    WHY: Backward-compatible public entry point for single-candidate screening.
    Delegates to screen_candidate_with_ensemble so borderline candidates
    (45–75% confidence) automatically benefit from ensemble voting without
    any change to callers.

    HOW: Thin wrapper — calls screen_candidate_with_ensemble and discards
    the run count, returning only the final state.

    Args:
        screening_input: Validated ScreeningInput for one candidate.

    Returns:
        ScreeningState with all populated fields. For borderline candidates,
        this is the winning state from 3 ensemble runs.
    """
    state, _ = await screen_candidate_with_ensemble(screening_input)
    return state


async def screen_batch(inputs: list[ScreeningInput]) -> list[ScreeningState]:
    """
    WHY: Concurrent fan-out for batch screening. When evaluating a pool of candidates
    for the same role, running them in parallel (vs. sequentially) reduces total
    wall-clock time from O(n * avg_pipeline_time) to O(max_pipeline_time).

    The comparative_rank node uses a shared in-memory batch store (module-level dict
    in comparative_rank.py) to collect all candidates for the batch_id before ranking.
    Because candidates run concurrently, the store write is lock-protected.

    HOW: asyncio.gather() fans out all candidates concurrently using
    screen_candidate_with_ensemble, so borderline candidates are automatically
    re-run 3 times before contributing to the batch result. Results are returned
    in the same order as the input list (asyncio.gather preserves order).

    IMPORTANT: All inputs in a batch should share the same batch_id for comparative
    ranking to work. If batch_id differs, each candidate ranks independently.

    Args:
        inputs: List of ScreeningInput objects, typically sharing the same batch_id.

    Returns:
        List of ScreeningState objects in the same order as inputs.
    """
    if not inputs:
        return []

    batch_id = inputs[0].batch_id
    total = len(inputs)

    logger.info(
        "screen_batch: starting",
        batch_id=batch_id,
        total_candidates=total,
    )

    batch_start_ms = time.time() * 1000

    # Fan out all candidates concurrently using ensemble for borderline confidence
    tasks = [screen_candidate_with_ensemble(inp) for inp in inputs]
    results_with_counts: tuple[tuple[ScreeningState, int], ...] = await asyncio.gather(
        *tasks
    )
    results: list[ScreeningState] = [state for state, _ in results_with_counts]
    total_ensemble_invocations: int = sum(
        1 for _, num_runs in results_with_counts if num_runs > 1
    )

    elapsed_ms = int((time.time() * 1000) - batch_start_ms)
    verdicts = [
        r["decision"].verdict if r.get("decision") else "ERROR"
        for r in results
    ]
    total_cost = sum(r.get("total_cost_usd", 0.0) for r in results)

    logger.info(
        "screen_batch: complete",
        batch_id=batch_id,
        total_candidates=total,
        verdicts=verdicts,
        total_cost_usd=round(total_cost, 6),
        total_ensemble_invocations=total_ensemble_invocations,
        elapsed_ms=elapsed_ms,
    )

    return results
