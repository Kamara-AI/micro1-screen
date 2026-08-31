"""
WHY: FitAnalysis is the multi-dimensional assessment of how well a candidate
matches the role — going far beyond keyword overlap. Each dimension maps to
a specific senior recruiter mental model from our research.

HOW: The analyze_fit node populates this schema. Scores are 0.0–1.0 per
dimension. The decision node blends them with evidence quality to produce
the final confidence %.
"""

from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class CareerShape(StrEnum):
    """
    WHY: Career shape is more predictive than any single role title.
    Using StrEnum allows use as both type annotation and runtime value.
    """
    ASCENDING = "ascending"
    ACCELERATING = "accelerating"
    PLATEAU = "plateau"
    LATERAL = "lateral"
    DESCENDING = "descending"
    NON_LINEAR = "non_linear"


class LearningVelocityEvidence(BaseModel):
    """
    WHY: Learning velocity (from Bock's Google research) is the single highest
    predictor of long-term performance. We make it explicit rather than folding
    it into a generic 'culture fit' score.
    """

    model_config = ConfigDict(frozen=True)

    new_skills_across_roles: list[str] = Field(
        default_factory=list,
        description="Skills that appeared in a later role that weren't in the earlier one",
    )
    self_directed_signals: list[str] = Field(
        default_factory=list,
        description="Blog posts, talks, open source, certifications applied in real work",
    )
    promoted_into_unfamiliar: bool = Field(
        default=False,
        description="True if candidate was promoted into a role domain they hadn't worked in before",
    )
    stagnation_flags: list[str] = Field(
        default_factory=list,
        description="Evidence of no skill evolution in the last N years",
    )


class CompanyContext(BaseModel):
    """
    WHY: 'Director at XYZ Corp' means completely different things depending on
    whether XYZ Corp had 8 employees or 8,000. Junior recruiters miss this.
    We make it explicit.
    """

    model_config = ConfigDict(frozen=True)

    company_name: str
    estimated_size: Literal["micro", "small", "medium", "large", "enterprise", "unknown"] = Field(
        default="unknown",
        description="micro <10, small 10–50, medium 50–500, large 500–5K, enterprise 5K+",
    )
    stage_at_join: Literal["pre_seed", "seed", "series_a", "series_b", "growth", "public", "enterprise", "unknown"] = Field(
        default="unknown"
    )
    outcome: Literal["still_operating", "acquired", "ipo", "closed", "unknown"] = Field(
        default="unknown"
    )
    role_scope_appropriate: bool = Field(
        default=True,
        description=(
            "False when stated title scope exceeds what the company size plausibly supports. "
            "E.g. 'VP Engineering' at a 5-person startup managing 0 engineers."
        ),
    )


class FitAnalysis(BaseModel):
    """
    WHY: Multi-dimensional fit analysis implements the senior recruiter's
    "achievement pattern reader", "career trajectory analyst", and "builder
    vs. maintainer classifier" mental models — all in one structured output.

    Scores are 0.0–1.0 per dimension. The decision node uses a weighted blend
    (configurable in Settings) to produce a composite fit score.

    HOW: The analyze_fit LLM call is prompted to evaluate each dimension
    independently and produce a score with a brief rationale. This forces
    dimension-by-dimension reasoning rather than holistic impression.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str

    # ── Dimension Scores (0.0–1.0) ────────────────────────────────────────────
    technical_fit: float = Field(
        ..., ge=0.0, le=1.0,
        description="How well stated + demonstrated skills match role technical requirements",
    )
    technical_fit_rationale: str = Field(..., description="Brief evidence-linked explanation")

    experience_level_fit: float = Field(
        ..., ge=0.0, le=1.0,
        description="Does career stage, scope, and seniority match the role level?",
    )
    experience_level_rationale: str = Field(...)

    learning_velocity_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Bock's learning agility metric — predicts long-term performance",
    )
    learning_velocity_rationale: str = Field(...)
    learning_velocity_evidence: LearningVelocityEvidence = Field(
        default_factory=LearningVelocityEvidence
    )

    builder_maintainer_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "1.0 = pure builder, 0.0 = pure maintainer. Interpreted against role need: "
            "early startup needs 1.0, enterprise ops needs 0.0–0.3."
        ),
    )

    # ── Career Trajectory ─────────────────────────────────────────────────────
    career_shape: Literal[
        "ascending", "accelerating", "plateau", "lateral", "descending", "non_linear"
    ]
    career_velocity: str = Field(
        ...,
        description="Plain-English summary of promotion cadence. E.g. 'promoted ~every 18 months'",
    )
    company_contexts: list[CompanyContext] = Field(default_factory=list)

    # ── Non-obvious Fit ───────────────────────────────────────────────────────
    non_obvious_fit_signals: list[str] = Field(
        default_factory=list,
        description=(
            "Signals that an ATS would miss: non-linear path with coherent narrative, "
            "cross-domain skills that apply to this role, building track record without "
            "matching job title"
        ),
    )

    # ── Red and Green Flags ───────────────────────────────────────────────────
    role_specific_red_flags: list[str] = Field(
        default_factory=list,
        description="Role-type-aware red flags. E.g. 'Senior PM with no product launches mentioned'",
    )
    role_specific_green_flags: list[str] = Field(
        default_factory=list,
        description="Role-type-aware positive signals beyond the obvious",
    )

    # ── Bias Check Output ─────────────────────────────────────────────────────
    bias_flags: list[str] = Field(
        default_factory=list,
        description=(
            "Populated by the detect_bias node — NOT by analyze_fit. "
            "Listed here so they travel with the analysis in state."
        ),
    )
    has_bias_flag: bool = Field(default=False)

    # ── Interview Brief Inputs ────────────────────────────────────────────────
    probe_points: list[str] = Field(
        default_factory=list,
        description=(
            "Specific gaps or inconsistencies the interviewer should probe. "
            "Used by build_human_brief node to generate targeted questions."
        ),
    )
    confirm_strengths: list[str] = Field(
        default_factory=list,
        description="Genuine positives worth validating in the interview",
    )

    @property
    def composite_fit_score(self) -> float:
        """
        WHY: A weighted blend of all dimension scores gives a single fit number
        that the decision node blends 40% with the 60% evidence quality score.

        HOW: Weights reflect hiring research — technical fit and learning velocity
        are the strongest predictors of role performance (Schmidt & Hunter meta-analysis).
        Builder/maintainer fit is weighted by how explicitly the role requires one or the other.
        """
        return (
            self.technical_fit * 0.35
            + self.experience_level_fit * 0.25
            + self.learning_velocity_score * 0.25
            + self.builder_maintainer_score * 0.15
        )
