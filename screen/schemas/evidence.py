"""
WHY: The evidence layer is the core of what makes SCREEN different from every
existing tool. Rather than producing a score, we extract structured evidence
from the CV and make that evidence the basis of every downstream decision.

This mirrors the elite recruiter's "verification instinct" — every claim is
tagged with its signal tier (A/B/C/D) so confidence calculations are grounded
in evidence quality, not evidence quantity.

HOW: The extract_evidence node populates an EvidenceBundle by asking the LLM
to find specific artefact types. Every claim carries a weight. The weight
system is the formula that makes our confidence % defensible.
"""

from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SignalTier(StrEnum):
    """
    WHY: Signal tiers encode evidence quality as an enum so they can be used
    as both type annotations and runtime values without confusion.
    """
    VERIFIED = "A"
    STATED = "B"
    VAGUE = "C"
    CONTRADICTED = "D"


# Weight map — deterministic, not LLM-determined
#
# WHY Tier C = 0.1 (not 0.3):
# Tier C claims are "vague and unverifiable" — they carry minimal confirmatory signal.
# The normalization formula (per_claim + 1.5) / 2.5 anchors at D=0 and A=1. With
# C=0.3, pure Tier C evidence normalises to 0.72 → blends into borderline YES territory.
# With C=0.1, pure Tier C evidence normalises to 0.64 — below the YES threshold (0.65)
# with neutral fit, preventing vague-claim inflation. The non-zero floor (vs 0.0) avoids
# catastrophically deflating strong candidates whose minor achievements get reclassified
# from B to C by the 2-element minimum rule for Tier B.
SIGNAL_WEIGHTS: dict[str, float] = {
    "A": 1.0,
    "B": 0.7,
    "C": 0.1,   # Vague claims contribute minimal positive signal (floor effect only)
    "D": -1.5,
}


class VerificationSource(StrEnum):
    """WHY: Tracks which tool produced the verification result for audit trail."""

    GITHUB_API = "github_api"
    WEB_SEARCH = "web_search"
    PORTFOLIO_FETCH = "portfolio_fetch"
    NOT_ATTEMPTED = "not_attempted"


class VerificationResult(BaseModel):
    """
    WHY: Records the outcome of an external verification attempt for a claim.
    Stored on the Claim so the audit trail includes both what was claimed
    and what external evidence found (or didn't find).
    """

    model_config = ConfigDict(frozen=True)

    source: VerificationSource
    query_used: str = Field(..., description="The exact query/URL used for verification")
    found: bool = Field(..., description="True if relevant external evidence was found")
    summary: str = Field(
        ...,
        description="What was found or why it wasn't found. 1-2 sentences.",
    )
    url: Optional[str] = Field(default=None, description="Source URL if applicable")
    tier_change: Optional[str] = Field(
        default=None,
        description="e.g. 'B->A' if claim was upgraded, 'B->D' if contradicted, None if unchanged",
    )


class Claim(BaseModel):
    """
    WHY: Every piece of evidence in the CV is modelled as a Claim with a tier
    and weight. This lets the decision node aggregate evidence mathematically
    rather than relying on LLM judgment for the final verdict.

    source_location gives the human reviewer a pointer to the exact CV section
    without reproducing the full CV text in the evidence bundle.
    """

    model_config = ConfigDict(frozen=True)

    text: str = Field(..., description="The claim as extracted — paraphrased, not verbatim")
    tier: Literal["A", "B", "C", "D"] = Field(..., description="Signal quality tier")
    confidence_weight: float = Field(
        ...,
        description="Numeric weight derived from tier. Set by extract_evidence node.",
        ge=-1.5,
        le=1.0,
    )
    source_location: str = Field(
        ...,
        description=(
            "Human-readable pointer to where this claim appears. "
            "E.g. 'Role at Safaricom 2019–2022, bullet 3'. Never contains raw CV text."
        ),
    )
    is_verifiable_externally: bool = Field(
        default=False,
        description="True if this claim could be checked against public data (LinkedIn, Companies House, etc.)",
    )
    verification: Optional[VerificationResult] = Field(
        default=None,
        description="External verification result. None if not attempted or not applicable.",
    )


class Contradiction(BaseModel):
    """
    WHY: Contradictions are a first-class evidence type — they are not just
    'low confidence signals'. A single critical contradiction (impossible dates,
    scope inflation) triggers an ESCALATE verdict regardless of other signals.

    severity determines both the confidence penalty and the routing:
      critical  → mandatory ESCALATE
      moderate  → lowers confidence, adds to human brief
      minor     → noted, doesn't change routing
    """

    model_config = ConfigDict(frozen=True)

    claim_a: str = Field(..., description="First conflicting claim (paraphrased)")
    claim_b: str = Field(..., description="Second conflicting claim (paraphrased)")
    contradiction_type: Literal[
        "temporal",          # Impossible date ranges (company not yet founded, etc.)
        "scope_inflation",   # Role scope claimed exceeds what company size allows
        "skill_level",       # Expert claim vs. no evidence of application
        "title_inflation",   # Senior title with junior responsibilities described
        "employment_gap",    # Unexplained gap between two stated dates
    ]
    severity: Literal["critical", "moderate", "minor"]
    explanation: str = Field(
        ...,
        description="Why this is a contradiction — the specific logical conflict",
    )


class SilenceFlag(BaseModel):
    """
    WHY: Elite recruiters read ABSENCE of information as a signal, not as
    neutral. A senior engineer with no architectural decisions mentioned is
    suspicious. A people manager with no team size ever stated is suspicious.

    Silence flags implement the "silence reader" mental model. They penalise
    confidence only for role-level-appropriate absences.

    severity encodes how damning the absence is for this specific role+seniority:
      high   → this should definitely be present for this role
      medium → would expect it but it's not impossible to omit
      low    → minor curiosity, doesn't affect verdict
    """

    model_config = ConfigDict(frozen=True)

    expected_signal: str = Field(
        ...,
        description="What we expected to see and didn't. E.g. 'quantified outcomes for senior role'",
    )
    absence_interpretation: str = Field(
        ...,
        description="Why this absence is significant in this context",
    )
    severity: Literal["high", "medium", "low"]


class EvidenceBundle(BaseModel):
    """
    WHY: The complete evidence picture for one candidate. This is what the
    decision node operates on — not the raw CV, not a summary, but structured
    evidence with quality weights attached.

    builder_signals and maintainer_signals implement the builder/maintainer
    classifier — a first-class output that no existing ATS produces.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    claims: list[Claim] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    silence_flags: list[SilenceFlag] = Field(default_factory=list)
    builder_signals: list[str] = Field(
        default_factory=list,
        description=(
            "Specific vocabulary/evidence of building: 'built from scratch', 'launched', "
            "'zero to one', 'architected', quantified growth outcomes"
        ),
    )
    maintainer_signals: list[str] = Field(
        default_factory=list,
        description=(
            "Specific vocabulary/evidence of maintaining: 'managed', 'maintained', "
            "'supported', 'ensured', 'oversaw', no ownership language"
        ),
    )
    builder_maintainer_verdict: Literal["builder", "maintainer", "hybrid", "insufficient_data"] = Field(
        default="insufficient_data",
        description="Synthesised verdict from signal analysis",
    )
    has_critical_contradiction: bool = Field(
        default=False,
        description="True if any contradiction has severity='critical'. Triggers ESCALATE regardless of confidence.",
    )
    has_unverifiable_high_stakes_claim: bool = Field(
        default=False,
        description=(
            "True if a Tier B/C claim is both high-impact for the verdict AND cannot be externally verified. "
            "Triggers ESCALATE when combined with high confidence."
        ),
    )

    @property
    def total_weighted_score(self) -> float:
        """
        WHY: The total weighted score across all claims is the raw input to the
        confidence calculation. It is a property, not a stored field, because
        it must be computed fresh from the claims list — not stored and stale.

        HOW: Sum all claim weights. Contradictions are already encoded as Tier D
        claims (weight -1.5) by the extract_evidence node, so they factor in here.
        """
        return sum(claim.confidence_weight for claim in self.claims)

    @property
    def silence_penalty(self) -> float:
        """
        WHY: Silence is penalised separately from claim quality so the two
        signals don't collapse into a single opaque number.

        HOW: High severity absence = -0.3, medium = -0.15, low = 0 (noted but not penalised).
        """
        penalty = 0.0
        for flag in self.silence_flags:
            if flag.severity == "high":
                penalty += 0.3
            elif flag.severity == "medium":
                penalty += 0.15
        return penalty
