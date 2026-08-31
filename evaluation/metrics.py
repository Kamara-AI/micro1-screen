"""
WHY: Hackathon judges need to see quantifiable improvement over baseline.
These metrics make the case that SCREEN is better — not just "more complex".
Each metric targets a different failure mode of naive AI screening:

- verdict_accuracy: does the system get the answer right?
- escalation_precision/recall: does it correctly flag edge cases that need humans?
- calibration_score: is its confidence % meaningful, or just noise?
- avg_cost_per_candidate: is the additional quality worth the cost?

HOW: All functions are pure (no LLM calls, no I/O). They accept lists and return
scalars or strings. This makes them trivially testable and composable.
"""

import math
from typing import Optional


def verdict_accuracy(verdicts: list[str], ground_truths: list[str]) -> float:
    """
    WHY: The primary accuracy metric — percentage of verdicts that match the
    ground truth. Simple but essential. If SCREEN's accuracy isn't measurably
    higher than baseline, we have a calibration problem, not a complexity advantage.

    HOW: Exact string match. Both inputs must be from the set:
    {STRONG_YES, YES, AMBIGUOUS, NO, STRONG_NO, ESCALATE}.

    Args:
        verdicts: List of verdict strings produced by the system under evaluation.
        ground_truths: List of ground truth verdict strings, same length and order.

    Returns:
        Float in [0.0, 1.0] — proportion of correct verdicts. Returns 0.0 for
        empty lists to avoid ZeroDivisionError.
    """
    if not verdicts or not ground_truths:
        return 0.0
    if len(verdicts) != len(ground_truths):
        raise ValueError(
            f"verdicts ({len(verdicts)}) and ground_truths ({len(ground_truths)}) "
            "must have the same length"
        )
    correct = sum(v == gt for v, gt in zip(verdicts, ground_truths))
    return correct / len(ground_truths)


def escalation_precision(escalated: list[str], should_escalate: list[str]) -> float:
    """
    WHY: Accuracy alone doesn't capture escalation quality. A system that never
    escalates gets 0% precision but doesn't penalise other metrics. We want to
    know: when SCREEN says ESCALATE, is it right?

    Precision = true_positives / (true_positives + false_positives)
    i.e. "of the things we escalated, what fraction actually needed escalation?"

    High precision means human review time is well-spent. Low precision means
    we are flooding recruiters with unnecessary escalations.

    HOW: A candidate_id is in escalated if the system returned ESCALATE for them.
    It is in should_escalate if the ground truth is ESCALATE. Precision is computed
    over these two sets.

    Args:
        escalated: List of candidate_ids the system chose to escalate.
        should_escalate: List of candidate_ids that ground truth says should escalate.

    Returns:
        Float in [0.0, 1.0]. Returns 1.0 if nothing was escalated (vacuously true —
        no false positives). Returns 0.0 if everything escalated was wrong.
    """
    if not escalated:
        # No escalations — vacuously precise (no false positives)
        return 1.0
    should_set = set(should_escalate)
    true_positives = sum(c in should_set for c in escalated)
    return true_positives / len(escalated)


def escalation_recall(escalated: list[str], should_escalate: list[str]) -> float:
    """
    WHY: The complement of precision. Recall = true_positives / all_that_should_escalate.
    A system with high precision but low recall escalates correctly when it does escalate,
    but misses many genuine escalation cases — routing them to a wrong pass/fail verdict.

    Missing an escalation case (e.g. date contradiction) is a meaningful failure mode —
    it means an inconsistency reaches the hiring manager unexamined.

    Args:
        escalated: List of candidate_ids the system chose to escalate.
        should_escalate: List of candidate_ids that ground truth says should escalate.

    Returns:
        Float in [0.0, 1.0]. Returns 1.0 if should_escalate is empty (vacuously true).
    """
    if not should_escalate:
        return 1.0
    escalated_set = set(escalated)
    true_positives = sum(c in escalated_set for c in should_escalate)
    return true_positives / len(should_escalate)


def calibration_score(confidence_pcts: list[float], correct: list[bool]) -> float:
    """
    WHY: A system that says 95% confidence on every verdict is useless — the confidence
    carries no information. Calibration measures whether high confidence actually
    correlates with correctness.

    We use a simplified Brier-score-style calibration: the mean squared error between
    the stated confidence (as a probability) and the binary correctness outcome.
    Lower is better. We invert and normalise to [0.0, 1.0] where 1.0 is perfect calibration.

    Brier score = mean((p_i - o_i)^2) where p_i is confidence/100 and o_i is 1 if correct.
    Perfect calibration = Brier score of 0.0. Random = 0.25. We return (1 - brier_score).

    WHY Brier score: It is a proper scoring rule — it penalises both overconfidence and
    underconfidence. A system that always says 50% gets a Brier score of 0.25. A system
    that says 90% and is always right gets ~0.01.

    Args:
        confidence_pcts: List of confidence percentages (0.0–100.0) from the system.
        correct: List of booleans — True if the verdict matched ground truth.

    Returns:
        Float in [0.0, 1.0]. 1.0 = perfect calibration, 0.75 = random baseline.
    """
    if not confidence_pcts or not correct:
        return 0.0
    if len(confidence_pcts) != len(correct):
        raise ValueError("confidence_pcts and correct must have the same length")

    brier_score = sum(
        (pct / 100.0 - (1.0 if c else 0.0)) ** 2
        for pct, c in zip(confidence_pcts, correct)
    ) / len(confidence_pcts)

    # Invert: 1.0 = perfect, 0.75 = random
    return max(0.0, 1.0 - brier_score)


def avg_cost_per_candidate(costs: list[float]) -> float:
    """
    WHY: Makes SCREEN's economics transparent. The judge question is: "is the quality
    improvement worth the extra cost vs. a single prompt?" If SCREEN costs $0.04 per
    candidate and the baseline costs $0.003, the question is: is the accuracy delta
    worth the 13x cost? This function provides the denominator of that calculation.

    HOW: Simple arithmetic mean. Cost is in USD, taken from Decision.estimated_cost_usd.

    Args:
        costs: List of per-candidate cost estimates in USD.

    Returns:
        Mean cost in USD. Returns 0.0 for empty list.
    """
    if not costs:
        return 0.0
    return sum(costs) / len(costs)


def _direction_correct(verdict: str, ground_truth: str) -> bool:
    """
    WHY: For partial credit in the comparison report, it's useful to know if the
    system got the directional sentiment right (positive/negative/uncertain) even
    when the exact tier differs. E.g. YES when STRONG_YES is correct = directionally
    right. STRONG_NO when NO is correct = directionally right.

    HOW: Maps verdicts to sentiment buckets. Used only in the report, not in the
    primary metrics.

    Args:
        verdict: The system's verdict string.
        ground_truth: The ground truth verdict string.

    Returns:
        True if both verdicts are in the same sentiment bucket.
    """
    positive = {"STRONG_YES", "YES"}
    negative = {"STRONG_NO", "NO"}
    uncertain = {"AMBIGUOUS", "ESCALATE"}

    def bucket(v: str) -> Optional[str]:
        if v in positive:
            return "positive"
        if v in negative:
            return "negative"
        if v in uncertain:
            return "uncertain"
        return None

    return bucket(verdict) == bucket(ground_truth)


def generate_comparison_report(
    screen_results: list[dict],
    baseline_results: list[dict],
    ground_truths: list[str],
) -> str:
    """
    WHY: The narrative report is what judges read. It contextualises the metrics —
    not just "SCREEN got 80%" but "SCREEN caught both contradictions the baseline
    missed, correctly identified the gap-explained candidate as YES, and had lower
    overconfidence on edge cases."

    HOW: Iterates over results to compute per-candidate analysis, then aggregates
    into section-by-section narrative. Returns a formatted plain-text string that
    can be printed or written to a file.

    Args:
        screen_results: List of dicts, each with keys: candidate_id, verdict,
            confidence_pct, correct (bool), cost_usd, processing_time_ms.
            None entries indicate SCREEN did not run for that candidate.
        baseline_results: List of dicts, each with keys: candidate_id, verdict,
            correct (bool). Confidence and cost are not available for the baseline.
        ground_truths: List of ground truth verdict strings, same order as results.

    Returns:
        Formatted multi-section text report as a string.
    """
    n = len(ground_truths)

    # ── Accuracy ──────────────────────────────────────────────────────────────
    screen_verdicts = [
        r["verdict"] if r is not None else "UNKNOWN" for r in screen_results
    ]
    baseline_verdicts = [
        r["verdict"] if r is not None else "UNKNOWN" for r in baseline_results
    ]

    screen_accuracy = verdict_accuracy(screen_verdicts, ground_truths)
    baseline_accuracy = verdict_accuracy(baseline_verdicts, ground_truths)

    screen_correct_flags = [
        v == gt for v, gt in zip(screen_verdicts, ground_truths)
    ]
    baseline_correct_flags = [
        v == gt for v, gt in zip(baseline_verdicts, ground_truths)
    ]

    screen_directional = sum(
        _direction_correct(v, gt)
        for v, gt in zip(screen_verdicts, ground_truths)
    )
    baseline_directional = sum(
        _direction_correct(v, gt)
        for v, gt in zip(baseline_verdicts, ground_truths)
    )

    # ── Escalation ────────────────────────────────────────────────────────────
    gt_escalated = [
        ground_truths[i]
        for i in range(n)
        if ground_truths[i] == "ESCALATE"
    ]
    # Build candidate_id lists for escalation metrics
    # We use index as proxy for candidate_id since we don't have it here
    gt_escalate_ids = [str(i) for i in range(n) if ground_truths[i] == "ESCALATE"]
    screen_escalate_ids = [
        str(i) for i in range(n) if screen_verdicts[i] == "ESCALATE"
    ]
    baseline_escalate_ids = [
        str(i) for i in range(n) if baseline_verdicts[i] == "ESCALATE"
    ]

    screen_esc_precision = escalation_precision(screen_escalate_ids, gt_escalate_ids)
    screen_esc_recall = escalation_recall(screen_escalate_ids, gt_escalate_ids)
    baseline_esc_precision = escalation_precision(baseline_escalate_ids, gt_escalate_ids)
    baseline_esc_recall = escalation_recall(baseline_escalate_ids, gt_escalate_ids)

    # ── Calibration ───────────────────────────────────────────────────────────
    screen_confidences = [
        r["confidence_pct"] if r is not None else 50.0 for r in screen_results
    ]
    screen_calibration = calibration_score(screen_confidences, screen_correct_flags)

    # ── Cost ──────────────────────────────────────────────────────────────────
    screen_costs = [
        r.get("cost_usd", 0.0) if r is not None else 0.0 for r in screen_results
    ]
    screen_avg_cost = avg_cost_per_candidate(screen_costs)
    baseline_avg_cost = avg_cost_per_candidate(
        [r.get("cost_usd", 0.003) if r is not None else 0.003 for r in baseline_results]
    )

    # ── Per-candidate table ───────────────────────────────────────────────────
    col_widths = [20, 12, 12, 12, 10, 10, 10]
    header = (
        f"{'Candidate ID':<20} {'Ground Truth':<12} {'SCREEN':<12} {'Baseline':<12} "
        f"{'SCR OK':<10} {'BAS OK':<10} {'SCR Conf':<10}"
    )
    separator = "-" * sum(col_widths) + "-" * (len(col_widths) - 1)

    rows: list[str] = []
    for i in range(n):
        sr = screen_results[i]
        br = baseline_results[i]
        sv = screen_verdicts[i]
        bv = baseline_verdicts[i]
        gt = ground_truths[i]
        sc_ok = "YES" if screen_correct_flags[i] else "NO"
        ba_ok = "YES" if baseline_correct_flags[i] else "NO"
        conf = f"{sr['confidence_pct']:.0f}%" if sr is not None else "N/A"

        candidate_id = sr["candidate_id"] if sr is not None else f"candidate_{i}"
        rows.append(
            f"{candidate_id:<20} {gt:<12} {sv:<12} {bv:<12} {sc_ok:<10} {ba_ok:<10} {conf:<10}"
        )

    per_candidate_table = "\n".join([header, separator] + rows)

    # ── Render report ─────────────────────────────────────────────────────────
    report_lines = [
        "=" * 80,
        "SCREEN vs BASELINE — EVALUATION REPORT",
        "=" * 80,
        "",
        "ACCURACY",
        f"  SCREEN exact match:      {screen_accuracy:.0%}  ({sum(screen_correct_flags)}/{n})",
        f"  Baseline exact match:    {baseline_accuracy:.0%}  ({sum(baseline_correct_flags)}/{n})",
        f"  SCREEN directional:      {screen_directional/n:.0%}  ({screen_directional}/{n})",
        f"  Baseline directional:    {baseline_directional/n:.0%}  ({baseline_directional}/{n})",
        f"  Delta (exact):           {(screen_accuracy - baseline_accuracy):+.0%}",
        "",
        "ESCALATION HANDLING",
        f"  Ground truth escalations: {len(gt_escalate_ids)}/{n}",
        f"  SCREEN escalations:       {len(screen_escalate_ids)} "
        f"(precision={screen_esc_precision:.0%}, recall={screen_esc_recall:.0%})",
        f"  Baseline escalations:     {len(baseline_escalate_ids)} "
        f"(precision={baseline_esc_precision:.0%}, recall={baseline_esc_recall:.0%})",
        "",
        "CALIBRATION (Brier-based, 1.0 = perfect, 0.75 = random)",
        f"  SCREEN calibration score: {screen_calibration:.3f}",
        f"  Baseline: N/A (no structured confidence output)",
        "",
        "ECONOMICS",
        f"  SCREEN avg cost/candidate: ${screen_avg_cost:.4f}",
        f"  Baseline avg cost/candidate: ${baseline_avg_cost:.4f}",
        f"  Cost multiplier: {(screen_avg_cost / baseline_avg_cost):.1f}x"
        if baseline_avg_cost > 0 else "  Cost multiplier: N/A",
        "",
        "PER-CANDIDATE RESULTS",
        per_candidate_table,
        "",
        "=" * 80,
    ]

    return "\n".join(report_lines)


__all__ = [
    "verdict_accuracy",
    "escalation_precision",
    "escalation_recall",
    "calibration_score",
    "avg_cost_per_candidate",
    "generate_comparison_report",
]
