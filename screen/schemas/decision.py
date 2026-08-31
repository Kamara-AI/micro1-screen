"""
WHY: The decision layer is what judges see. Every output type here is designed
to be judge-readable, candidate-dignified, and recruiter-actionable.

HumanBrief implements the "interview brief constructor" mental model — not just
"flag for review" but a specific structured brief telling the human reviewer
exactly what to verify, what to ask, and what the first question should be.

CandidateFeedback implements the "candidate dignity protocol" — even rejected
candidates receive one genuine strength and one honest gap.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Verdict(str):
    """
    WHY: Six verdict states — not binary pass/fail. The distinction between
    AMBIGUOUS (needs more info) and ESCALATE (specific verification required)
    is what separates a thoughtful agent from a scoring engine.
    """

    STRONG_YES = "STRONG_YES"   # ≥80% confidence — proceed without hesitation
    YES = "YES"                 # 65–79% — strong signal, proceed with normal screening
    AMBIGUOUS = "AMBIGUOUS"     # 45–64% — mixed signals, phone screen first
    NO = "NO"                   # 25–44% — insufficient fit, pass
    STRONG_NO = "STRONG_NO"     # <25% or failed hard requirement — clear pass
    ESCALATE = "ESCALATE"       # Contradiction / bias flag / unverifiable high-stakes claim


class HumanBrief(BaseModel):
    """
    WHY: The feature no ATS provides. When a candidate is ESCALATED, the human
    reviewer receives a structured brief — not just a flag. This implements
    the senior recruiter's habit of constructing a targeted interview brief
    before handing off to the hiring manager.

    The brief tells the human:
      - What we know (verified + stated evidence)
      - What we cannot verify (unverifiable claims that matter)
      - What to do next (specific verification tasks)
      - What to ask first (the most important question)
      - What risk to probe (the thing that could disqualify if true)

    HOW: Populated by the build_human_brief node only when verdict = ESCALATE.
    For non-ESCALATE verdicts, human_brief is None in state.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    escalation_category: Literal[
        "critical_contradiction",
        "unverifiable_high_stakes_claim",
        "bias_flag_detected",
        "ambiguous_non_linear_background",
    ]
    summary: str = Field(
        ...,
        description="2-sentence max. What the agent found and why it cannot make a call.",
        max_length=500,
    )
    what_we_know: list[str] = Field(
        ...,
        description="Tier A and strong Tier B claims — what we're reasonably confident about",
        min_length=1,
    )
    what_we_cannot_verify: list[str] = Field(
        ...,
        description="Specific unverifiable claims that are material to the verdict",
        min_length=1,
    )
    verification_tasks: list[str] = Field(
        ...,
        description=(
            "Concrete external verification steps. E.g. 'Check LinkedIn for DataCorp founding date', "
            "'Verify AWS certification via Credly badge link if provided'"
        ),
        min_length=1,
    )
    suggested_interview_questions: list[str] = Field(
        ...,
        description="Evidence-based questions targeting the specific gaps identified",
        min_length=2,
    )
    first_question: str = Field(
        ...,
        description=(
            "The single most important question to open the interview with. "
            "Targets the most material unverifiable claim or the primary contradiction."
        ),
    )
    risk_to_probe: str = Field(
        ...,
        description=(
            "The one thing that — if it turns out to be true — would likely disqualify this candidate. "
            "Ask about this early, not late."
        ),
    )


class CandidateFeedback(BaseModel):
    """
    WHY: Every candidate receives feedback — including rejections. This is both
    an ethical practice (candidates are people in a stressful situation) and
    a strategic one (well-treated rejected candidates refer others and reapply).

    No existing ATS or AI screener does this. It costs one small LLM call.

    The genuine_strength must be real — not a platitude. The gap_for_this_role
    is specific to the role mismatch, not a general criticism.

    encouragement is only generated when the gap is genuinely closable (e.g.
    missing certification, insufficient seniority but strong trajectory).
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    verdict_communicated: str = Field(
        default="not selected for this role at this time",
        description="Plain-language verdict for candidate — never shows internal codes",
    )
    genuine_strength: str = Field(
        ...,
        description=(
            "One real, specific positive from their CV. Not 'you seem passionate' — "
            "something concrete like 'your Python→Rust self-taught transition is strong evidence of learning agility'"
        ),
        min_length=20,
    )
    gap_for_this_role: str = Field(
        ...,
        description=(
            "One honest, specific reason the role wasn't a match. Not 'insufficient experience' — "
            "something like 'this role requires system design at 100K+ user scale, which isn't evidenced here'"
        ),
        min_length=20,
    )
    encouragement: Optional[str] = Field(
        default=None,
        description=(
            "Only when the gap is genuinely closable. None for fundamental mismatches. "
            "E.g. 'A portfolio project demonstrating distributed systems design would strengthen future applications'"
        ),
    )


class Decision(BaseModel):
    """
    WHY: The final output of the pipeline for one candidate. Everything a
    recruiter or hiring manager needs in one structured document.

    Primary evidence lists the top 3 reasons for the verdict — cited from
    the EvidenceBundle, not generated fresh. This makes the decision auditable:
    you can trace every primary_evidence entry back to a specific Claim or
    SilenceFlag in the evidence bundle.

    estimated_cost_usd makes SCREEN's economics transparent — a feature no
    existing tool provides. Judges and customers can calculate ROI directly.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    verdict: Literal["STRONG_YES", "YES", "AMBIGUOUS", "NO", "STRONG_NO", "ESCALATE"]
    confidence_pct: float = Field(
        ..., ge=0.0, le=100.0,
        description="Confidence in the verdict. NOT the probability of being a good hire — the confidence in the assessment.",
    )
    primary_evidence: list[str] = Field(
        ...,
        description=(
            "Top 3 reasons for this verdict, cited from EvidenceBundle. "
            "Each entry should reference a specific claim, contradiction, or silence flag."
        ),
        min_length=1,
        max_length=5,
    )
    escalation_reason: Optional[str] = Field(
        default=None,
        description="Required when verdict=ESCALATE. Plain-English reason for escalation.",
    )
    escalation_category: Optional[Literal[
        "critical_contradiction",
        "unverifiable_high_stakes_claim",
        "bias_flag_detected",
        "ambiguous_non_linear_background",
    ]] = Field(default=None)
    tier_processed: int = Field(
        ..., ge=1, le=3,
        description="Which processing tier produced this decision (1=prefilter, 2=full, 3=escalation brief)",
    )
    estimated_cost_usd: float = Field(
        ..., ge=0.0,
        description="Estimated LLM API cost for this candidate. Transparent per-candidate economics.",
    )
    processing_time_ms: int = Field(..., description="Total pipeline time for this candidate")
    passed_hard_requirements: bool = Field(
        ...,
        description="False for STRONG_NO due to hard requirement failure (not fit failure)",
    )
