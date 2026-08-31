"""
WHY: Schema-first (Rule 01 equivalent). All input to the pipeline is validated
against this schema before any node runs. Invalid input is rejected at the
boundary — never silently passed through.

HOW: ScreeningInput is the only accepted entry point. The graph entry node
validates against this model. job_description is kept separate from cv_text
so nodes can reason about role requirements independently of candidate claims.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScreeningInput(BaseModel):
    """
    WHY: The contract for what enters the pipeline. Every field has a clear purpose.
    Optional fields have sensible defaults so callers don't need to over-specify.

    batch_id groups candidates being evaluated for the same role — this enables
    comparative ranking in Node 9.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str = Field(
        ...,
        description="Opaque identifier — never contains PII. Used in logs and trajectory.",
        min_length=1,
        max_length=64,
    )
    cv_text: str = Field(
        ...,
        description="Raw CV/resume text. Plain text preferred; HTML/markdown accepted.",
        min_length=50,
    )
    job_description: str = Field(
        ...,
        description="Full job description including requirements, responsibilities, and context.",
        min_length=50,
    )
    role_seniority: Literal["junior", "mid", "senior", "staff", "executive"] = Field(
        ...,
        description="Target seniority level — used for role-specific red flag detection.",
    )
    role_type: Literal["engineering", "product", "data", "design", "operations", "other"] = Field(
        ...,
        description="Broad role category — used for role-specific silence flag detection.",
    )
    batch_id: Optional[str] = Field(
        default=None,
        description="Groups candidates for the same role. Set to enable comparative ranking.",
        max_length=64,
    )
    hard_requirements: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit knockout criteria (e.g. ['must have right to work in UK', "
            "'minimum 5 years Python']). Tier 1 pre-filter checks these first."
        ),
    )

    @field_validator("candidate_id")
    @classmethod
    def candidate_id_no_spaces(cls, v: str) -> str:
        """WHY: Spaces in IDs cause downstream parsing issues in logs and filenames."""
        if " " in v:
            raise ValueError("candidate_id must not contain spaces")
        return v
