"""
WHY: CandidateProfile is the structured representation of raw CV text after
the parse_candidate node runs. Every subsequent node reads from this schema,
not from the raw CV string — this enforces a clean data layer boundary.

HOW: The parse node uses an LLM to extract structured data, then validates
it against these models. Fields are Optional where the information may
legitimately be absent (e.g. graduation_year for experienced professionals).
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleEntry(BaseModel):
    """
    WHY: One job in the candidate's history. Immutable once parsed — if the
    LLM extracted it wrong, that becomes an EvidenceBundle contradiction, not
    a mutation of this record.

    is_quantified signals whether the candidate described outcomes with
    numbers. Absence of quantification is a meaningful signal (silence flag)
    for senior roles.
    """

    model_config = ConfigDict(frozen=True)

    title: str = Field(..., description="Job title as stated on CV")
    company: str = Field(..., description="Company name as stated on CV")
    start_date: Optional[str] = Field(
        default=None, description="Start date — 'YYYY-MM' or 'YYYY' or free text"
    )
    end_date: Optional[str] = Field(
        default=None, description="End date — 'YYYY-MM' or 'YYYY' or 'Present'"
    )
    duration_months: Optional[int] = Field(
        default=None, description="Calculated tenure in months — None if dates missing"
    )
    achievements: list[str] = Field(
        default_factory=list,
        description="Bullet-point achievements as extracted from CV",
    )
    is_quantified: bool = Field(
        default=False,
        description=(
            "True if at least one achievement contains a numeric outcome. "
            "Absence of quantification is a silence flag for senior roles."
        ),
    )
    team_size_mentioned: Optional[int] = Field(
        default=None,
        description="Team size if explicitly stated. None = not mentioned (silence flag for leadership roles).",
    )


class EducationEntry(BaseModel):
    """
    WHY: Education is parsed but intentionally downweighted in our scoring.
    We record it to detect prestige-bias in our own reasoning, not to use
    it as a primary signal.
    """

    model_config = ConfigDict(frozen=True)

    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    is_traditional: bool = Field(
        default=True,
        description="False for bootcamps, MOOCs, self-taught paths — these are positive non-linear signals.",
    )


class EmploymentGap(BaseModel):
    """
    WHY: Gaps are data points, not automatic red flags. We record start/end
    so the analyze_fit node can reason about them in context — was this a
    gap at age 23 (common) or a gap after 15 years (needs explanation)?
    """

    model_config = ConfigDict(frozen=True)

    gap_start: str = Field(..., description="ISO-format date or year")
    gap_end: str = Field(..., description="ISO-format date or year")
    duration_months: Optional[int] = None
    explanation_provided: bool = Field(
        default=False,
        description="True if candidate offered any explanation on CV. No explanation = silence flag.",
    )


class CandidateProfile(BaseModel):
    """
    WHY: The structured, anonymised representation of the candidate. The
    anonymisation step (stripping name, photo references, demographic proxies)
    runs INSIDE the parse_candidate node before this model is populated.

    The anonymised_name field is replaced with a placeholder — the actual
    name is held only in the raw input and never flows deeper into the pipeline.

    HOW: Every downstream node receives this model, not the raw CV text.
    This enforces the data layer boundary analogous to byYou's two-plane split.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    anonymised_name: str = Field(
        default="CANDIDATE",
        description="Name is replaced with a placeholder — prevents name-based bias in analysis.",
    )
    roles: list[RoleEntry] = Field(
        default_factory=list,
        description="Work history in reverse chronological order",
    )
    education: list[EducationEntry] = Field(default_factory=list)
    skills_stated: list[str] = Field(
        default_factory=list,
        description="Skills explicitly listed — NOT the same as skills demonstrated in roles",
    )
    employment_gaps: list[EmploymentGap] = Field(default_factory=list)
    total_years_experience: Optional[float] = Field(
        default=None,
        description="Calculated from role dates. None if insufficient date data.",
    )
    career_start_year: Optional[int] = Field(
        default=None,
        description="Year of first professional role — used for trajectory analysis.",
    )
    has_non_linear_path: bool = Field(
        default=False,
        description=(
            "True if career spans multiple unrelated domains. "
            "Non-linear paths are a positive signal — ATS kills them, we seek them."
        ),
    )
    highest_education_level: Literal["phd", "masters", "bachelors", "bootcamp", "self_taught", "other", "unknown"] = Field(
        default="unknown"
    )
