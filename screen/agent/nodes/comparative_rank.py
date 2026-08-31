"""
WHY: Node 9 — the comparative intelligence layer. This is the feature that
answers the question every hiring manager actually asks: "Of all the candidates
we screened, who is the best fit, and in what dimension?"

No existing ATS or screener does this natively. They produce individual pass/fail
verdicts. SCREEN produces cohort rankings that give the hiring manager a strategic
view — not just "who passed" but "who is the best technical fit vs. the strongest
learner vs. the most career-appropriate."

The in-memory store approach is intentional for the hackathon:
  - Simple, no external dependencies (no Redis, no DB)
  - Thread-safe enough for single-process evaluation runs
  - Can be swapped for a persistent store (Redis, Postgres) in production

WHY batch_id check: Some screenings are one-off (no batch_id). In these cases,
comparative ranking makes no sense. The node returns immediately with a minimal
trajectory entry rather than producing empty analysis.

HOW: Module-level dict keyed by batch_id stores (candidate_id, Decision, FitAnalysis)
tuples. When a new candidate's result arrives:
  1. Store their result in the batch
  2. Check if we have ≥2 candidates
  3. If yes: compute rankings across all dimensions, produce CohortAnalysis
  4. If no: return empty (ranking not yet possible)

IMPORTANT: Because LangGraph may run nodes concurrently in some configurations,
we use a simple lock around the store write. For the hackathon sequential run
this is belt-and-suspenders safety, not a performance concern.
"""

import time
import threading
from typing import Any

from screen.core.config import settings
from screen.core.exceptions import StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import make_trajectory_entry
from screen.schemas.cohort import CandidateRank, CohortAnalysis
from screen.schemas.decision import Decision
from screen.schemas.analysis import FitAnalysis
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── In-memory batch store ──────────────────────────────────────────────────────
# WHY: Module-level dict is the simplest persistent-within-process store.
# Key: batch_id → list of (candidate_id, Decision, FitAnalysis)
# In production this would be replaced by a Redis or Postgres store.
_batch_store: dict[str, list[tuple[str, Decision, FitAnalysis]]] = {}
_batch_store_lock = threading.Lock()


def _career_shape_rank_score(career_shape: str) -> float:
    """
    WHY: Career shape needs a numeric proxy for ranking. We use a simple
    ordered scale where ascending/accelerating shapes score highest (most
    trajectory potential) and descending/plateau score lowest.

    This ranking is context-dependent — in some roles a plateau specialist
    is ideal. The score here is a general preference, not an absolute judgment.
    """
    shape_scores = {
        "accelerating": 1.0,
        "ascending": 0.9,
        "non_linear": 0.8,
        "lateral": 0.6,
        "plateau": 0.4,
        "descending": 0.3,
    }
    return shape_scores.get(career_shape, 0.5)


def _rank_list(values: list[float], ascending: bool = False) -> list[int]:
    """
    WHY: Converts a list of scores into 1-based ranks (1 = best).
    For all our dimensions, higher score = better fit (so ascending=False is the default).
    Ties are broken by list position (stable sort).

    HOW: argsort the values, then invert to get 1-based ranks.
    """
    indexed = list(enumerate(values))
    indexed.sort(key=lambda x: x[1], reverse=not ascending)
    ranks = [0] * len(values)
    for rank, (original_idx, _) in enumerate(indexed, start=1):
        ranks[original_idx] = rank
    return ranks


def _compute_standout_signal(
    candidate_id: str,
    decision: Decision,
    fit_analysis: FitAnalysis,
    all_decisions: list[Decision],
    all_fits: list[FitAnalysis],
) -> str:
    """
    WHY: The standout signal captures the one thing about this candidate that
    distinguishes them from the cohort — positive or negative. This is the
    insight that a hiring manager would write in their notes.

    HOW: We compare the candidate's dimension scores against cohort averages
    and surface the biggest deviation.
    """
    cohort_avg_technical = sum(f.technical_fit for f in all_fits) / len(all_fits)
    cohort_avg_velocity = sum(f.learning_velocity_score for f in all_fits) / len(all_fits)
    cohort_avg_confidence = sum(d.confidence_pct for d in all_decisions) / len(all_decisions)

    deviations = {
        "technical_fit": fit_analysis.technical_fit - cohort_avg_technical,
        "learning_velocity": fit_analysis.learning_velocity_score - cohort_avg_velocity,
        "confidence": (decision.confidence_pct - cohort_avg_confidence) / 100,
    }

    best_dimension = max(deviations, key=lambda k: abs(deviations[k]))
    deviation = deviations[best_dimension]

    if best_dimension == "technical_fit":
        if deviation > 0.15:
            return f"Strongest technical fit in cohort (+{deviation:.2f} above average)"
        elif deviation < -0.15:
            return f"Weakest technical fit in cohort ({deviation:.2f} below average)"
    elif best_dimension == "learning_velocity":
        if deviation > 0.15:
            return f"Highest learning velocity in cohort (+{deviation:.2f} above average)"
        elif deviation < -0.15:
            return f"Lowest learning velocity in cohort ({deviation:.2f} below average)"
    elif best_dimension == "confidence":
        if deviation > 0.15:
            return f"Highest overall confidence in cohort ({decision.confidence_pct}%)"
        elif deviation < -0.15:
            return f"Lowest overall confidence in cohort ({decision.confidence_pct}%)"

    # No strong deviation — note verdict or special property
    if decision.verdict in ("STRONG_YES", "YES"):
        return f"Solid across-the-board candidate — verdict: {decision.verdict}"
    elif decision.verdict == "ESCALATE":
        return f"Flagged for human review: {decision.escalation_category or 'see brief'}"
    else:
        return f"No strong standout dimension — composite confidence: {decision.confidence_pct}%"


def _check_cohort_bias_flags(
    results: list[tuple[str, Decision, FitAnalysis]],
) -> list[str]:
    """
    WHY: Cohort-level bias monitoring checks for patterns across the batch that
    indicate systematic bias — e.g., all rejections share a demographic proxy.

    HOW: Currently checks:
      - If all rejected candidates have non-linear paths flagged (path bias)
      - If all escalations share the same escalation_category (model systematically unsure about one type)
      - If confidence variance is extremely low (model may be rubber-stamping)

    This is intentionally lightweight for the hackathon — production would add
    more sophisticated bias pattern detection.
    """
    flags: list[str] = []
    total = len(results)

    rejected = [
        (cid, dec, fit)
        for cid, dec, fit in results
        if dec.verdict in ("NO", "STRONG_NO")
    ]

    escalated = [
        (cid, dec, fit)
        for cid, dec, fit in results
        if dec.verdict == "ESCALATE"
    ]

    # Check if all rejections share a non-linear path characteristic
    if len(rejected) >= 2:
        non_linear_rejected = sum(1 for _, _, fit in rejected if fit.career_shape == "non_linear")
        if non_linear_rejected == len(rejected) and len(rejected) >= 2:
            flags.append(
                f"All {len(rejected)} rejected candidates have non-linear career paths — "
                f"verify that non-linear paths are not being systematically penalised"
            )

    # Check if all escalations share same category (systematic model uncertainty)
    if len(escalated) >= 2:
        categories = [dec.escalation_category for _, dec, _ in escalated if dec.escalation_category]
        if len(set(categories)) == 1 and categories:
            flags.append(
                f"All {len(escalated)} escalated candidates share the same escalation category "
                f"('{categories[0]}') — check if this reflects genuine uncertainty or a systematic model pattern"
            )

    # Check confidence variance — extremely uniform scores may indicate rubber-stamping
    confidences = [dec.confidence_pct for _, dec, _ in results]
    if total >= 3:
        confidence_range = max(confidences) - min(confidences)
        if confidence_range < 10.0:
            flags.append(
                f"All {total} candidates scored within a {confidence_range:.1f}% confidence band "
                f"— very low variance may indicate the model is not differentiating effectively"
            )

    return flags


def _compute_cohort_insight(
    results: list[tuple[str, Decision, FitAnalysis]],
) -> str:
    """
    WHY: The cohort insight gives the hiring manager a one-paragraph strategic
    view of what the batch told us about the candidate pool for this role.
    This is a deterministic summary — no LLM, just pattern reading.
    """
    total = len(results)
    strong_yes = sum(1 for _, d, _ in results if d.verdict == "STRONG_YES")
    yes = sum(1 for _, d, _ in results if d.verdict == "YES")
    escalated = sum(1 for _, d, _ in results if d.verdict == "ESCALATE")
    rejected = sum(1 for _, d, _ in results if d.verdict in ("NO", "STRONG_NO"))

    avg_technical = sum(f.technical_fit for _, _, f in results) / total
    avg_velocity = sum(f.learning_velocity_score for _, _, f in results) / total
    avg_confidence = sum(d.confidence_pct for _, d, _ in results) / total

    technical_label = (
        "strong" if avg_technical >= 0.7
        else "moderate" if avg_technical >= 0.5
        else "weak"
    )
    velocity_label = (
        "high" if avg_velocity >= 0.7
        else "moderate" if avg_velocity >= 0.5
        else "low"
    )

    return (
        f"Cohort of {total} candidates: {strong_yes + yes} recommended for interview, "
        f"{escalated} escalated for review, {rejected} not recommended. "
        f"Cohort shows {technical_label} technical fit (avg: {avg_technical:.2f}) and "
        f"{velocity_label} learning velocity (avg: {avg_velocity:.2f}). "
        f"Average confidence: {avg_confidence:.1f}%. "
        f"{'Strong candidate pool for this role.' if (strong_yes + yes) / total >= 0.5 else 'Thin candidate pool — consider broadening the search criteria.'}"
    )


def comparative_rank_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Computes comparative rankings across all candidates in a batch.
    Produces a CohortAnalysis when ≥2 candidates have been processed.

    HOW:
    1. Check if batch_id is present — if not, return immediately
    2. Store this candidate's result in the module-level batch store
    3. If ≥2 candidates in store: compute rankings and CohortAnalysis
    4. Rankings are computed across: technical_fit, learning_velocity,
       career_shape (proxy score), builder_maintainer_score, overall confidence

    THREAD SAFETY: Uses a lock around the store write. For sequential hackathon
    runs this is not strictly necessary but follows production hygiene.
    """
    node_name = "comparative_rank"
    start_ms = time.time() * 1000

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    batch_id = screening_input.batch_id
    candidate_id = screening_input.candidate_id

    # ── Skip if not batch mode ──────────────────────────────────────────────────
    if batch_id is None:
        trajectory_entry = make_trajectory_entry(
            node=node_name,
            start_time_ms=start_ms,
            reasoning_summary=(
                "No batch_id present — single-candidate screening. "
                "Comparative ranking skipped."
            ),
            output_summary="Skipped — no batch_id",
            model_used=None,
            cost_usd=0.0,
        )
        logger.info(
            "comparative_rank skipped (no batch_id)",
            node=node_name,
            candidate_id=candidate_id,
        )
        return {
            "trajectory": [trajectory_entry],
            "total_cost_usd": 0.0,
        }

    decision = state.get("decision")
    if decision is None:
        raise StateTransitionError(node_name, "decision")

    fit_analysis = state.get("fit_analysis")

    # WHY: Hard-rejected candidates (structural_precheck or tier1_prefilter) never
    # run analyze_fit, so fit_analysis is always None for them. Ranking them against
    # qualified candidates is meaningless — their STRONG_NO is deterministic, not scored.
    # We skip ranking and return cleanly. The decision is still recorded in trajectory.
    if fit_analysis is None:
        trajectory_entry = make_trajectory_entry(
            node=node_name,
            start_time_ms=start_ms,
            reasoning_summary=(
                "Candidate was hard-rejected before fit analysis ran — "
                "no FitAnalysis available. Comparative ranking skipped for this candidate."
            ),
            output_summary="Skipped — hard-rejected candidate (no fit_analysis)",
            model_used=None,
            cost_usd=0.0,
        )
        logger.info(
            "comparative_rank skipped (hard-rejected candidate)",
            node=node_name,
            candidate_id=candidate_id,
            verdict=decision.verdict,
        )
        return {
            "trajectory": [trajectory_entry],
            "total_cost_usd": 0.0,
        }

    logger.info(
        "comparative_rank started",
        node=node_name,
        candidate_id=candidate_id,
        batch_id=batch_id,
    )

    # ── Store this candidate's result ───────────────────────────────────────────
    with _batch_store_lock:
        if batch_id not in _batch_store:
            _batch_store[batch_id] = []

        # Avoid duplicate entries if node is re-run
        existing_ids = {cid for cid, _, _ in _batch_store[batch_id]}
        if candidate_id not in existing_ids:
            _batch_store[batch_id].append((candidate_id, decision, fit_analysis))

        batch_results = list(_batch_store[batch_id])  # Copy under lock

    # ── Need ≥2 candidates to rank ──────────────────────────────────────────────
    if len(batch_results) < 2:
        trajectory_entry = make_trajectory_entry(
            node=node_name,
            start_time_ms=start_ms,
            reasoning_summary=(
                f"Only {len(batch_results)} candidate(s) in batch '{batch_id}'. "
                f"Need ≥2 for comparative ranking. Result stored; ranking deferred."
            ),
            output_summary=f"Stored ({len(batch_results)}/≥2 for ranking)",
            model_used=None,
            cost_usd=0.0,
        )
        return {
            "trajectory": [trajectory_entry],
            "total_cost_usd": 0.0,
        }

    # ── Compute rankings ────────────────────────────────────────────────────────
    all_ids = [cid for cid, _, _ in batch_results]
    all_decisions = [dec for _, dec, _ in batch_results]
    all_fits = [fit for _, _, fit in batch_results]

    technical_scores = [f.technical_fit for f in all_fits]
    velocity_scores = [f.learning_velocity_score for f in all_fits]
    trajectory_scores = [_career_shape_rank_score(f.career_shape) for f in all_fits]
    builder_scores = [f.builder_maintainer_score for f in all_fits]
    confidence_scores = [d.confidence_pct / 100 for d in all_decisions]

    technical_ranks = _rank_list(technical_scores)
    velocity_ranks = _rank_list(velocity_scores)
    trajectory_ranks = _rank_list(trajectory_scores)
    builder_ranks = _rank_list(builder_scores)

    # Overall rank = FitAnalysis.composite_fit_score (authoritative weighted blend)
    # blended with confidence (15%) which reflects evidence quality beyond fit alone.
    # WHY: Uses FitAnalysis.composite_fit_score (the authoritative weighted blend)
    # rather than redefining weights here. Confidence adds a small signal (15%)
    # since it reflects evidence quality beyond fit dimensions alone.
    composite_scores = [
        all_fits[i].composite_fit_score * 0.85 + confidence_scores[i] * 0.15
        for i in range(len(batch_results))
    ]
    overall_ranks = _rank_list(composite_scores)

    # Build CandidateRank list
    candidate_ranks: list[CandidateRank] = []
    for i, (cid, dec, fit) in enumerate(batch_results):
        standout = _compute_standout_signal(cid, dec, fit, all_decisions, all_fits)
        candidate_ranks.append(
            CandidateRank(
                candidate_id=cid,
                verdict=dec.verdict,
                confidence_pct=dec.confidence_pct,
                overall_rank=overall_ranks[i],
                technical_rank=technical_ranks[i],
                velocity_rank=velocity_ranks[i],
                trajectory_rank=trajectory_ranks[i],
                builder_rank=builder_ranks[i],
                standout_signal=standout,
            )
        )

    # Sort by overall rank
    candidate_ranks.sort(key=lambda r: r.overall_rank)

    # Best-in-dimension IDs
    best_overall_id = all_ids[composite_scores.index(max(composite_scores))]
    best_technical_id = all_ids[technical_scores.index(max(technical_scores))]
    best_velocity_id = all_ids[velocity_scores.index(max(velocity_scores))]
    best_trajectory_id = all_ids[trajectory_scores.index(max(trajectory_scores))]

    # Categorise candidates by verdict
    recommended = [
        r.candidate_id for r in candidate_ranks
        if r.verdict in ("STRONG_YES", "YES")
    ]
    escalated_list = [
        r.candidate_id for r in candidate_ranks
        if r.verdict == "ESCALATE"
    ]
    rejected_list = [
        r.candidate_id for r in candidate_ranks
        if r.verdict in ("NO", "STRONG_NO")
    ]

    # Cohort-level bias flags
    cohort_bias_flags = _check_cohort_bias_flags(batch_results)

    # Economics
    total_cost = sum(d.estimated_cost_usd for d in all_decisions)
    cost_per_candidate = total_cost / len(batch_results) if batch_results else 0.0
    total_time_ms = sum(d.processing_time_ms for d in all_decisions)

    # Cohort insight
    cohort_insight = _compute_cohort_insight(batch_results)

    cohort_analysis = CohortAnalysis(
        batch_id=batch_id,
        total_candidates=len(batch_results),
        rankings=candidate_ranks,
        best_overall_id=best_overall_id,
        best_technical_id=best_technical_id,
        best_velocity_id=best_velocity_id,
        best_trajectory_id=best_trajectory_id,
        recommended_for_interview=recommended,
        escalated_candidates=escalated_list,
        clear_rejections=rejected_list,
        cohort_bias_flags=cohort_bias_flags,
        total_cost_usd=round(total_cost, 6),
        cost_per_candidate_usd=round(cost_per_candidate, 6),
        total_processing_time_ms=total_time_ms,
        cohort_insight=cohort_insight,
    )

    # Clear batch after ranking is complete to prevent stale accumulation on re-runs
    with _batch_store_lock:
        _batch_store.pop(batch_id, None)

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Comparative ranking complete for batch '{batch_id}'. "
            f"{len(batch_results)} candidates ranked. "
            f"Best overall: {best_overall_id}. "
            f"Recommended: {len(recommended)}. "
            f"Escalated: {len(escalated_list)}. "
            f"Rejected: {len(rejected_list)}. "
            f"Cohort bias flags: {len(cohort_bias_flags)}."
        ),
        output_summary=(
            f"CohortAnalysis: {len(batch_results)} candidates | "
            f"best: {best_overall_id} | "
            f"recommended: {len(recommended)} | "
            f"bias flags: {len(cohort_bias_flags)}"
        ),
        evidence_keys=[f"rank:{r.candidate_id}:{r.overall_rank}" for r in candidate_ranks],
        model_used=None,  # Deterministic — no LLM call
        cost_usd=0.0,
    )

    logger.info(
        "comparative_rank complete",
        node=node_name,
        candidate_id=candidate_id,
        batch_id=batch_id,
        total_in_batch=len(batch_results),
        best_overall_id=best_overall_id,
        num_recommended=len(recommended),
        num_escalated=len(escalated_list),
        num_rejected=len(rejected_list),
        cohort_bias_flags=len(cohort_bias_flags),
        duration_ms=trajectory_entry.duration_ms,
    )

    return {
        "cohort_analysis": cohort_analysis,
        "trajectory": [trajectory_entry],
        "total_cost_usd": 0.0,
    }
