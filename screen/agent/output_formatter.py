"""
WHY: Presentation layer for SCREEN pipeline output. Separates formatting
concerns from pipeline logic — the runner produces ScreeningState, this
module converts it into forms that different consumers can actually use.

Consumers:
  - Hiring managers and recruiters: format_markdown_report() → .md file
  - CLI demo / hackathon judges: format_console_report() → coloured terminal
  - Evaluation harness: format_evaluation_metrics() → flat dict for DataFrame
  - API callers: format_decision_summary() → minimal structured response

HOW: All functions are pure — they take a ScreeningState (or list of them)
and return a string or dict. No side effects, no file I/O here. The runner
handles file saving; this module handles formatting only.
"""

from typing import Any, Optional

from screen.schemas.cohort import CohortAnalysis
from screen.schemas.decision import CandidateFeedback, Decision, HumanBrief
from screen.schemas.evidence import EvidenceBundle
from screen.schemas.state import ScreeningState
from screen.schemas.trajectory import TrajectoryEntry

# ── Verdict display mappings ───────────────────────────────────────────────────
_VERDICT_DISPLAY: dict[str, str] = {
    "STRONG_YES": "STRONG YES",
    "YES": "YES",
    "AMBIGUOUS": "AMBIGUOUS",
    "NO": "NO",
    "STRONG_NO": "STRONG NO",
    "ESCALATE": "⚠ ESCALATE — HUMAN REVIEW REQUIRED",
}

_VERDICT_EMOJI: dict[str, str] = {
    "STRONG_YES": "✅",
    "YES": "✓",
    "AMBIGUOUS": "〰",
    "NO": "✗",
    "STRONG_NO": "✗✗",
    "ESCALATE": "⚠",
}

_TIER_EMOJI: dict[str, str] = {
    "A": "✅",
    "B": "✓",
    "C": "〰",
    "D": "✗",
}

_TIER_LABEL: dict[str, str] = {
    "A": "Tier A — verified",
    "B": "Tier B — stated",
    "C": "Tier C — vague",
    "D": "Tier D — contradicted",
}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _trunc(text: str, max_len: int = 80) -> str:
    """Truncate text to max_len characters with ellipsis.

    Args:
        text: String to truncate.
        max_len: Maximum character length.

    Returns:
        Truncated string with '...' appended if truncated.
    """
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def _confidence_bar(pct: float, width: int = 20) -> str:
    """Render a simple ASCII confidence bar.

    Args:
        pct: Confidence percentage (0–100).
        width: Total bar width in characters.

    Returns:
        String like '[████████░░░░░░░░░░░░] 43.2%'
    """
    filled = int((pct / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct:.1f}%"


def _bullet_list(items: list[str], indent: int = 0) -> str:
    """Format a list of strings as markdown bullet points.

    Args:
        items: List of strings to format.
        indent: Number of spaces to indent each bullet.

    Returns:
        Markdown bullet list string.
    """
    prefix = " " * indent
    return "\n".join(f"{prefix}- {item}" for item in items)


def _numbered_list(items: list[str], indent: int = 0) -> str:
    """Format a list of strings as a numbered markdown list.

    Args:
        items: List of strings to format.
        indent: Number of spaces to indent each item.

    Returns:
        Numbered markdown list string.
    """
    prefix = " " * indent
    return "\n".join(f"{prefix}{i + 1}. {item}" for i, item in enumerate(items))


# ── Public formatting functions ────────────────────────────────────────────────

def format_decision_summary(state: ScreeningState) -> dict[str, Any]:
    """Minimal structured dict for API callers and programmatic access.

    WHY: API consumers need a clean, flat dict without markdown formatting.
    This is the machine-readable equivalent of format_markdown_report.

    Args:
        state: Final ScreeningState from pipeline execution.

    Returns:
        Dict with verdict, confidence, evidence, feedback, cost, and escalation fields.
    """
    decision: Optional[Decision] = state.get("decision")
    feedback: Optional[CandidateFeedback] = state.get("candidate_feedback")

    if decision is None:
        return {
            "error": state.get("error_message", "Pipeline did not complete"),
            "error_node": state.get("error_node"),
        }

    result: dict[str, Any] = {
        "candidate_id": decision.candidate_id,
        "verdict": decision.verdict,
        "confidence_pct": round(decision.confidence_pct, 1),
        "primary_evidence": decision.primary_evidence,
        "tier_processed": decision.tier_processed,
        "passed_hard_requirements": decision.passed_hard_requirements,
        "estimated_cost_usd": round(decision.estimated_cost_usd, 5),
        "processing_time_ms": decision.processing_time_ms,
    }

    if decision.escalation_reason:
        result["escalation_reason"] = decision.escalation_reason
    if decision.escalation_category:
        result["escalation_category"] = decision.escalation_category

    if feedback:
        result["candidate_feedback"] = {
            "genuine_strength": feedback.genuine_strength,
            "gap_for_this_role": feedback.gap_for_this_role,
            "encouragement": feedback.encouragement,
        }

    return result


def format_markdown_report(state: ScreeningState) -> str:
    """Full human-readable markdown report for hiring managers and judges.

    WHY: The rubric's End-to-End Quality criterion (20 pts) requires output
    with 'the finish of something a person would sign their name to rather
    than an obvious AI generated draft.' A ScreeningState dict is not that.
    This converts the structured pipeline output into a document a recruiter
    can forward to a hiring manager without post-processing.

    HOW: Assembles sections conditionally — HumanBrief only appears for
    ESCALATE verdicts, CohortAnalysis only appears in batch mode. All fields
    that could be None are guarded.

    Args:
        state: Final ScreeningState from pipeline execution.

    Returns:
        Markdown-formatted screening report string.
    """
    decision: Optional[Decision] = state.get("decision")
    human_brief: Optional[HumanBrief] = state.get("human_brief")
    feedback: Optional[CandidateFeedback] = state.get("candidate_feedback")
    trajectory: list[TrajectoryEntry] = state.get("trajectory") or []
    cohort: Optional[CohortAnalysis] = state.get("cohort_analysis")
    total_cost: float = state.get("total_cost_usd") or 0.0
    screening_input = state.get("screening_input")

    # ── Error state ────────────────────────────────────────────────────────────
    if decision is None:
        error_msg = state.get("error_message", "Unknown pipeline error")
        error_node = state.get("error_node", "unknown")
        return (
            f"# SCREEN — Pipeline Error\n\n"
            f"**Failed at node:** `{error_node}`\n\n"
            f"**Error:** {error_msg}\n\n"
            f"*No verdict was produced. Review logs for details.*\n"
        )

    candidate_id = decision.candidate_id
    verdict = decision.verdict
    confidence = decision.confidence_pct
    role_seniority = screening_input.role_seniority if screening_input else "unknown"
    role_type = screening_input.role_type if screening_input else "unknown"

    # Last trajectory timestamp as screened-at
    screened_at = trajectory[-1].timestamp_eat if trajectory else "unknown"

    verdict_display = _VERDICT_DISPLAY.get(verdict, verdict)
    verdict_emoji = _VERDICT_EMOJI.get(verdict, "")

    lines: list[str] = []

    # ── Header ─────────────────────────────────────────────────────────────────
    lines += [
        "# SCREEN Screening Report",
        "",
        f"**Candidate ID:** `{candidate_id}`  ",
        f"**Role:** {role_seniority.title()} {role_type.title()}  ",
        f"**Screened:** {screened_at}  ",
        "**Pipeline:** SCREEN v0.1.0 — Structured Candidate Reasoning and Evaluation Engine",
        "",
        "---",
        "",
    ]

    # ── Verdict block ──────────────────────────────────────────────────────────
    lines += [
        f"## {verdict_emoji} Verdict: {verdict_display}",
        "",
        f"**Confidence:** {_confidence_bar(confidence)}",
        "",
    ]

    if verdict == "ESCALATE" and decision.escalation_reason:
        lines += [
            f"> **Why escalated:** {decision.escalation_reason}",
            "",
        ]

    # ── Primary evidence ───────────────────────────────────────────────────────
    lines += [
        "### Primary Evidence",
        "",
    ]
    for evidence_item in decision.primary_evidence:
        lines.append(f"- • {evidence_item}")
    lines.append("")

    # ── Claim verification detail ──────────────────────────────────────────────
    # WHY: The verify_claims node is the flagship feature of Iteration 10.
    # Without this section, a hiring manager reading the report cannot see
    # that GitHub confirmed a claim or that a temporal contradiction was
    # caught externally. The external evidence must be surfaced explicitly.
    evidence_bundle: Optional[EvidenceBundle] = state.get("evidence_bundle")
    if evidence_bundle:
        verified_claims = [c for c in evidence_bundle.claims if c.verification is not None]
        if verified_claims:
            lines += [
                "### External Claim Verification",
                "",
                "| Claim | Tier | Change | Verified By | Finding |",
                "|-------|------|--------|-------------|---------|",
            ]
            for claim in verified_claims:
                vr = claim.verification
                tier_display = claim.tier
                change_display = vr.tier_change if vr.tier_change else "—"
                source_display = vr.source.replace("_", " ").title()
                summary_trunc = _trunc(vr.summary, 70)
                url_part = f" ([source]({vr.url}))" if vr.url else ""
                lines.append(
                    f"| {_trunc(claim.text, 45)} "
                    f"| {tier_display} "
                    f"| {change_display} "
                    f"| {source_display} "
                    f"| {summary_trunc}{url_part} |"
                )
            lines.append("")

    # ── Hard requirement note ──────────────────────────────────────────────────
    if not decision.passed_hard_requirements:
        lines += [
            "> ⚠ **Hard requirement not met** — candidate did not pass the minimum",
            "> eligibility criteria for this role. No further analysis was performed.",
            "",
        ]

    lines.append("---")
    lines.append("")

    # ── Candidate feedback ─────────────────────────────────────────────────────
    if feedback:
        lines += [
            "## Candidate Strengths & Gaps",
            "",
            f"**Strength:** {feedback.genuine_strength}",
            "",
            f"**Gap for this role:** {feedback.gap_for_this_role}",
            "",
        ]
        if feedback.encouragement:
            lines += [
                f"**Next step:** {feedback.encouragement}",
                "",
            ]
        lines += ["---", ""]

    # ── Human brief (ESCALATE only) ────────────────────────────────────────────
    if human_brief:
        lines += [
            "## ⚠ Escalation Brief — Human Review Required",
            "",
            f"**Escalation category:** `{human_brief.escalation_category}`",
            "",
            f"> {human_brief.summary}",
            "",
            "### What We Know",
            "",
            _bullet_list(human_brief.what_we_know),
            "",
            "### What We Cannot Verify",
            "",
            _bullet_list(human_brief.what_we_cannot_verify),
            "",
            "### Verification Tasks",
            "",
            _numbered_list(human_brief.verification_tasks),
            "",
            "### Open the Interview With This Question",
            "",
            f"> {human_brief.first_question}",
            "",
            "### Primary Risk to Probe",
            "",
            f"> {human_brief.risk_to_probe}",
            "",
            "### Suggested Interview Questions",
            "",
            _numbered_list(human_brief.suggested_interview_questions),
            "",
            "---",
            "",
        ]

    # ── Pipeline audit trail ───────────────────────────────────────────────────
    lines += [
        "## Pipeline Audit Trail",
        "",
        "| Step | Summary | Duration | Model | Cost |",
        "|------|---------|----------|-------|------|",
    ]
    for entry in trajectory:
        model_label = entry.model_used or "deterministic"
        lines.append(
            f"| `{entry.node}` "
            f"| {_trunc(entry.reasoning_summary, 70)} "
            f"| {entry.duration_ms}ms "
            f"| {model_label} "
            f"| ${entry.cost_usd:.5f} |"
        )

    total_duration_ms = sum(e.duration_ms for e in trajectory)
    lines += [
        "",
        f"**Total pipeline cost:** ${total_cost:.4f}  ",
        f"**Total pipeline time:** {total_duration_ms}ms  ",
        f"**Nodes executed:** {len(trajectory)}",
        "",
        "---",
        "",
    ]

    # ── Cohort ranking (batch mode only) ──────────────────────────────────────
    if cohort:
        this_rank = next(
            (r for r in cohort.rankings if r.candidate_id == candidate_id), None
        )
        lines += [
            "## Cohort Ranking",
            "",
            f"**Batch:** `{cohort.batch_id}` — {cohort.total_candidates} candidates",
            "",
        ]
        if this_rank:
            lines += [
                f"| Dimension | Rank |",
                f"|-----------|------|",
                f"| Overall | #{this_rank.overall_rank} of {cohort.total_candidates} |",
                f"| Technical | #{this_rank.technical_rank} |",
                f"| Learning Velocity | #{this_rank.velocity_rank} |",
                f"| Career Trajectory | #{this_rank.trajectory_rank} |",
                f"| Builder Signal | #{this_rank.builder_rank} |",
                "",
                f"**Standout signal:** {this_rank.standout_signal}",
                "",
            ]
        if cohort.cohort_insight:
            lines += [
                f"**Cohort insight:** {cohort.cohort_insight}",
                "",
            ]
        if cohort.cohort_bias_flags:
            lines += [
                "**Batch bias flags:**",
                "",
                _bullet_list(cohort.cohort_bias_flags),
                "",
            ]
        lines += ["---", ""]

    # ── Footer ─────────────────────────────────────────────────────────────────
    lines += [
        "*Report generated by SCREEN — Structured Candidate Reasoning and Evaluation Engine*  ",
        "*micro1 Agentic Workflows Hackathon 2026*",
    ]

    return "\n".join(lines)


def format_console_report(state: ScreeningState) -> str:
    """Compact human-readable string for CLI demo and terminal output.

    WHY: The 5-minute demo video needs clean terminal output that reads well
    on screen. The full markdown report is too long for a demo walkthrough.
    This produces a condensed version that fits comfortably in a terminal window.

    Args:
        state: Final ScreeningState from pipeline execution.

    Returns:
        Compact console-friendly string (no markdown headers, uses box chars).
    """
    decision: Optional[Decision] = state.get("decision")
    feedback: Optional[CandidateFeedback] = state.get("candidate_feedback")
    trajectory: list[TrajectoryEntry] = state.get("trajectory") or []

    if decision is None:
        return f"[ERROR] Pipeline failed: {state.get('error_message', 'unknown error')}"

    verdict = decision.verdict
    confidence = decision.confidence_pct
    verdict_display = _VERDICT_DISPLAY.get(verdict, verdict)

    lines = [
        "━" * 60,
        f"  SCREEN — Candidate {decision.candidate_id}",
        "━" * 60,
        f"  Verdict:    {verdict_display}",
        f"  Confidence: {_confidence_bar(confidence, width=24)}",
        "",
        "  Evidence:",
    ]
    for item in decision.primary_evidence:
        lines.append(f"    • {_trunc(item, 55)}")

    if feedback:
        lines += [
            "",
            f"  Strength: {_trunc(feedback.genuine_strength, 55)}",
            f"  Gap:      {_trunc(feedback.gap_for_this_role, 55)}",
        ]

    total_ms = sum(e.duration_ms for e in trajectory)
    total_cost = state.get("total_cost_usd") or 0.0
    lines += [
        "",
        f"  Nodes: {len(trajectory)} | Time: {total_ms}ms | Cost: ${total_cost:.4f}",
        "━" * 60,
    ]
    return "\n".join(lines)


def format_evaluation_metrics(state: ScreeningState) -> dict[str, Any]:
    """Flat dict for evaluation harness DataFrame construction.

    WHY: The evaluation runner (evaluation/runner.py) needs to compare
    SCREEN verdicts against ground truth across all 10 test candidates.
    This produces a consistent flat dict for easy pandas DataFrame assembly.

    Args:
        state: Final ScreeningState from pipeline execution.

    Returns:
        Flat dict with all metrics needed for evaluation comparison.
    """
    decision: Optional[Decision] = state.get("decision")
    trajectory: list[TrajectoryEntry] = state.get("trajectory") or []

    if decision is None:
        return {
            "candidate_id": "unknown",
            "verdict": "ERROR",
            "confidence_pct": 0.0,
            "cost_usd": 0.0,
            "duration_ms": 0,
            "nodes_executed": 0,
            "error": state.get("error_message"),
        }

    return {
        "candidate_id": decision.candidate_id,
        "verdict": decision.verdict,
        "confidence_pct": round(decision.confidence_pct, 1),
        "cost_usd": round(decision.estimated_cost_usd, 5),
        "duration_ms": decision.processing_time_ms,
        "nodes_executed": len(trajectory),
        "tier_processed": decision.tier_processed,
        "passed_hard_requirements": decision.passed_hard_requirements,
        "escalated": decision.verdict == "ESCALATE",
        "escalation_category": decision.escalation_category,
        "error": None,
    }


def format_batch_summary(states: list[ScreeningState]) -> str:
    """Aggregated markdown summary across all candidates from screen_batch().

    WHY: After running the evaluation suite or a real batch, judges and hiring
    managers need a single document showing all results — not 10 separate files.

    Args:
        states: List of ScreeningState objects from screen_batch().

    Returns:
        Markdown summary table with per-candidate results and batch totals.
    """
    if not states:
        return "# SCREEN Batch Report\n\nNo candidates processed.\n"

    lines = [
        "# SCREEN Batch Screening Report",
        "",
        f"**Candidates screened:** {len(states)}",
        "",
        "| Candidate | Verdict | Confidence | Cost | Time |",
        "|-----------|---------|------------|------|------|",
    ]

    total_cost = 0.0
    total_ms = 0
    verdicts: dict[str, int] = {}

    for state in states:
        decision: Optional[Decision] = state.get("decision")
        trajectory: list[TrajectoryEntry] = state.get("trajectory") or []

        if decision is None:
            candidate_id = "unknown"
            row = f"| {candidate_id} | ERROR | — | — | — |"
        else:
            candidate_id = decision.candidate_id
            verdict = decision.verdict
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
            confidence_str = f"{decision.confidence_pct:.1f}%"
            cost_str = f"${decision.estimated_cost_usd:.4f}"
            duration_ms = sum(e.duration_ms for e in trajectory)
            total_cost += decision.estimated_cost_usd
            total_ms += duration_ms
            verdict_display = _VERDICT_DISPLAY.get(verdict, verdict)
            row = (
                f"| `{candidate_id}` "
                f"| {verdict_display} "
                f"| {confidence_str} "
                f"| {cost_str} "
                f"| {duration_ms}ms |"
            )
        lines.append(row)

    lines += [
        "",
        "### Summary",
        "",
    ]
    for verdict, count in sorted(verdicts.items()):
        lines.append(f"- **{verdict}:** {count}")

    lines += [
        "",
        f"**Total cost:** ${total_cost:.4f}",
        f"**Total time:** {total_ms}ms",
        f"**Avg cost/candidate:** ${(total_cost / len(states)):.4f}" if states else "",
        "",
        "---",
        "*Generated by SCREEN — micro1 Agentic Workflows Hackathon 2026*",
    ]

    return "\n".join(lines)


# ── Module-level convenience aliases ──────────────────────────────────────────

def format_screening_report(state: ScreeningState) -> str:
    """Convenience alias for format_markdown_report().

    Args:
        state: Final ScreeningState from pipeline execution.

    Returns:
        Markdown-formatted screening report string.
    """
    return format_markdown_report(state)
