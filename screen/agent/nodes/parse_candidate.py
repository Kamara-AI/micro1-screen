"""
WHY: Node 1 — the data boundary. Raw CV text enters here and never leaves
as raw text again. Every downstream node receives a structured, anonymised
CandidateProfile instead of an unstructured string.

Anonymisation is not cosmetic — it is a bias-control mechanism. By replacing
the candidate's name with "CANDIDATE" and stripping photo/age proxies before
the LLM produces any assessment, we prevent name-origin bias and age discrimination
from contaminating the analysis tier.

HOW: The node sends cv_text to Gemini Flash (fast, cheap — this is pure extraction,
not reasoning) with a structured output prompt bound to CandidateProfile.
On validation failure or LLM error, the node raises and the pipeline surfaces the error.
"""

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from screen.core.config import settings
from screen.core.exceptions import LLMCallError, StateTransitionError
from screen.core.llm_factory import build_llm, get_active_model
from screen.core.logging_config import get_logger
from screen.core.trajectory import estimate_token_cost, make_trajectory_entry
from screen.schemas.candidate import CandidateProfile
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── System prompt ──────────────────────────────────────────────────────────────
# WHY: The system prompt is a module-level constant so it can be reviewed,
# tested, and adjusted without touching the node logic.
PARSE_SYSTEM_PROMPT = """You are an expert CV parser with strict anonymisation responsibilities.

Your job is to extract structured information from a raw CV/resume and return it
as a structured CandidateProfile. You must follow these rules exactly:

ANONYMISATION (mandatory):
- Replace the candidate's real name everywhere with "CANDIDATE"
- Remove all photo references, headshot URLs, and profile image mentions
- Strip graduation years that would reveal the candidate's age
- Remove any pronouns or demographic markers that could bias analysis

PARSING RULES:
- Extract roles in REVERSE chronological order (most recent first)
- For each role, flag is_quantified=True only if at least one achievement contains
  a specific number (e.g., "increased revenue by 40%", "managed team of 12")
- Record team_size_mentioned only if explicitly stated with a number
- For employment gaps: a gap >3 months between roles should be recorded
- has_non_linear_path=True if the candidate has worked in 2+ clearly different industries
  (e.g., finance → engineering → healthcare is non-linear; backend → full-stack is not)
- highest_education_level: phd > masters > bachelors > bootcamp > self_taught
- total_years_experience: calculate from earliest start date to most recent end date (or present)
- career_start_year: year of the FIRST professional role (not education)
- is_traditional=False for bootcamps, MOOCs, online certifications, self-taught paths

DO NOT:
- Hallucinate skills not present in the CV
- Add graduation years not explicitly stated
- Assume gender from name or pronoun
- Penalise non-linear paths — they are positive signals
- Include any raw CV text verbatim in the structured output

Output ONLY the structured CandidateProfile. Do not add commentary."""

# ── LLM Setup ──────────────────────────────────────────────────────────────────
# WHY tier1: parse_candidate is structured extraction, not reasoning. Flash-class
# models handle JSON extraction reliably at a fraction of Pro cost.
_llm = build_llm("tier1")
_structured_llm = _llm.with_structured_output(CandidateProfile)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_parse_llm(candidate_id: str, cv_text: str) -> CandidateProfile:
    """
    WHY: Isolated LLM call function so the retry decorator applies only
    to the network call, not to the surrounding node logic.

    HOW: Sends the CV text with explicit instructions to produce an anonymised
    CandidateProfile. The candidate_id is injected into the prompt so the
    LLM populates the model's candidate_id field correctly.
    """
    messages = [
        SystemMessage(content=PARSE_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Parse the following CV. Set candidate_id to: {candidate_id}\n\n"
                f"--- CV TEXT START ---\n{cv_text}\n--- CV TEXT END ---"
            )
        ),
    ]
    result: CandidateProfile = _structured_llm.invoke(messages)
    return result


def parse_candidate_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Entry node for the pipeline. Converts raw CV text into a structured,
    anonymised CandidateProfile. Sets current_tier to 2 because the candidate
    has passed the initial intake step and is entering the main analysis tier.

    HOW:
    1. Validate state has required input
    2. Call Gemini Flash with structured output bound to CandidateProfile
    3. Validate the returned profile (Pydantic does this automatically via with_structured_output)
    4. Build trajectory entry and return partial state update

    Returns only the fields this node populates — LangGraph merges partial updates.
    """
    node_name = "parse_candidate"
    start_ms = time.time() * 1000

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id
    cv_text = screening_input.cv_text

    logger.info(
        "parse_candidate started",
        node=node_name,
        candidate_id=candidate_id,
    )

    try:
        candidate_profile = _call_parse_llm(
            candidate_id=candidate_id,
            cv_text=cv_text,
        )
    except Exception as exc:
        raise LLMCallError(node_name, str(exc)) from exc

    # Estimate cost: cv_text length as proxy for token count (1 token ≈ 4 chars)
    prompt_token_estimate = len(cv_text) // 4
    completion_token_estimate = 500  # Structured profile output is roughly constant
    cost_usd = estimate_token_cost(
        prompt_tokens=prompt_token_estimate,
        completion_tokens=completion_token_estimate,
        model_tier=1,
    )

    num_roles = len(candidate_profile.roles)
    num_skills = len(candidate_profile.skills_stated)
    num_gaps = len(candidate_profile.employment_gaps)

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Parsed CV into structured profile. "
            f"Found {num_roles} roles, {num_skills} stated skills, "
            f"{num_gaps} employment gaps. "
            f"Non-linear path: {candidate_profile.has_non_linear_path}. "
            f"Candidate anonymised — name replaced with placeholder."
        ),
        output_summary=(
            f"{num_roles} roles extracted, {num_skills} skills, "
            f"education level: {candidate_profile.highest_education_level}"
        ),
        evidence_keys=[f"role:{r.company}" for r in candidate_profile.roles],
        model_used=get_active_model("tier1"),
        cost_usd=cost_usd,
    )

    logger.info(
        "parse_candidate complete",
        node=node_name,
        candidate_id=candidate_id,
        num_roles=num_roles,
        duration_ms=trajectory_entry.duration_ms,
        cost_usd=cost_usd,
    )

    return {
        "candidate_profile": candidate_profile,
        "current_tier": 2,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
