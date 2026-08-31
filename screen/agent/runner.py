"""
WHY: The runner is the public interface to the SCREEN pipeline. All callers
(CLI, API, evaluation harness, tests) use runner functions — never the
LangGraph graph directly. This provides one place to add cross-cutting concerns:
  - Input validation
  - Structured logging at the run boundary
  - Error capture and state annotation
  - Batch parallelism

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


async def screen_candidate(screening_input: ScreeningInput) -> ScreeningState:
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

    return final_state


async def screen_batch(inputs: list[ScreeningInput]) -> list[ScreeningState]:
    """
    WHY: Concurrent fan-out for batch screening. When evaluating a pool of candidates
    for the same role, running them in parallel (vs. sequentially) reduces total
    wall-clock time from O(n * avg_pipeline_time) to O(max_pipeline_time).

    The comparative_rank node uses a shared in-memory batch store (module-level dict
    in comparative_rank.py) to collect all candidates for the batch_id before ranking.
    Because candidates run concurrently, the store write is lock-protected.

    HOW: asyncio.gather() fans out all candidates concurrently. Results are returned
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

    # Fan out all candidates concurrently
    tasks = [screen_candidate(inp) for inp in inputs]
    results: list[ScreeningState] = await asyncio.gather(*tasks)

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
        elapsed_ms=elapsed_ms,
    )

    return results
