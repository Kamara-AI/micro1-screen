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

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SignalTier(str):
    """
    WHY: Signal tiers encode evidence quality. A verified claim (Tier A) is
    worth 3x a vague claim (Tier C). A contradiction (Tier D) penalises
    confidence by more than a positive claim can offset.

    This prevents a resume full of vague claims from scoring as high as
    a resume with a few specific, internally consistent achievements.
    """

    VERIFIED = "A"      # Public, cross-referenceable — weight: +1.0
    STATED = "B"        # Specific, plausible, uncontradicted — weight: +0.7
    VAGUE = "C"         # Generic, unspecific ("worked on projects") — weight: +0.3
    CONTRADICTED = "D"  # Conflicts with another claim — weight: -1.5


# Weight map — deterministic, not LLM-determined
SIGNAL_WEIGHTS: dict[str, float] = {
    "A": 1.0,
    "B": 0.7,
    "C": 0.3,
    "D": -1.5,
}


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
