"""
WHY: The ChatGPT baseline is what we compare against. It's a single prompt
with no tools, no structured output, no uncertainty, no verification.
This is the "current state of the art" for a quick AI screening implementation.

We run the same 10 candidates through both SCREEN and the baseline and compare:
- Verdict accuracy (agreement with ground truth)
- Calibration (does SCREEN's confidence % correlate with actual correctness?)
- Evidence quality (does SCREEN cite evidence the baseline misses?)
- Human escalation (does SCREEN correctly identify candidates needing human review?)

HOW: A single call via OpenRouter with a structured prompt but NO structured output
format — the LLM returns free text. We parse the verdict out of the text with a
simple keyword scan, simulating the "copy-paste prompt into ChatGPT" approach that
most hiring managers actually use.

WHY OpenRouter for the baseline: Same provider as SCREEN so the comparison is fair —
any accuracy delta comes from the architecture (evidence extraction, contradiction
detection, calibrated confidence), not from using a different API.

WHY the same tier1 model: The baseline deliberately uses the cheapest capable model
(same as SCREEN's tier1) to represent the naive single-prompt approach at comparable
cost. The point is not to make the baseline look bad by giving it a weak model —
it's to show that a sophisticated pipeline outperforms a single prompt even when
both use the same model tier.

This is deliberately naive — the point is to show what you get without SCREEN's
evidence layer, contradiction detection, and calibrated confidence.
"""

import re
import time
from typing import Optional

from langchain_openai import ChatOpenAI

from screen.core.config import settings


_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/Kamara-AI/micro1-screen",
    "X-Title": "SCREEN - micro1 Hackathon 2026",
}

# WHY: Same tier1 model as SCREEN (google/gemini-2.5-flash-lite) so the comparison
# is fair — any accuracy delta is architecture, not model. If the operator overrides
# OPENROUTER_MODEL_TIER1 in their .env, the baseline uses the same override.
_BASELINE_MODEL = settings.openrouter_model_tier1

_SYSTEM_PROMPT = """You are an AI assistant helping a recruiter pre-screen job candidates.
You will be given a CV (resume) and a job description.
Your task is to assess whether the candidate is a good fit for the role.

Respond with:
1. A verdict: STRONG_YES, YES, AMBIGUOUS, NO, or STRONG_NO
2. A brief reasoning (3-5 sentences)

Be direct and decisive."""

_USER_TEMPLATE = """JOB DESCRIPTION:
{job_description}

CANDIDATE CV:
{cv_text}

Please provide your screening verdict and reasoning."""

# WHY: These patterns are intentionally simple — we want the baseline parser
# to mirror what a human would do when reading a free-text LLM response.
# Using regex rather than another LLM call keeps the baseline truly "naive".
_VERDICT_PATTERNS: dict[str, str] = {
    "STRONG_YES": r"STRONG[_\s]YES",
    "STRONG_NO": r"STRONG[_\s]NO",
    "YES": r"\bYES\b",
    "NO": r"\bNO\b",
    "AMBIGUOUS": r"\bAMBIGUOUS\b",
    "ESCALATE": r"\bESCALATE\b",
}


def _parse_verdict_from_text(text: str) -> str:
    """
    WHY: The baseline LLM returns free text, not structured JSON. We need to
    extract a verdict from natural language. This function does a greedy keyword
    scan — the order matters because 'STRONG_YES' must be checked before 'YES'
    to prevent false 'YES' matches inside 'STRONG_YES'.

    HOW: Iterates through patterns in priority order. Falls back to 'AMBIGUOUS'
    if no pattern matches — representing the failure mode where the LLM refuses
    to commit to a verdict (which happens more often than one might expect).

    Args:
        text: The raw LLM response string.

    Returns:
        One of the six verdict strings. Never raises.
    """
    for verdict in ["STRONG_YES", "STRONG_NO", "YES", "NO", "AMBIGUOUS", "ESCALATE"]:
        pattern = _VERDICT_PATTERNS[verdict]
        if re.search(pattern, text, re.IGNORECASE):
            return verdict
    # WHY: When the LLM doesn't commit, AMBIGUOUS is the honest fallback —
    # it reflects genuine uncertainty rather than asserting a wrong verdict.
    return "AMBIGUOUS"


def run_baseline(cv_text: str, job_description: str) -> dict:
    """
    WHY: The single-prompt, no-tools, no-structure baseline. This is the "quick AI"
    approach — equivalent to pasting the CV into ChatGPT and asking for a verdict.
    It represents the quality floor that SCREEN needs to beat.

    Deliberately NOT async — the baseline is sequential to reflect how it would
    actually be used (one candidate at a time, manually). The runner handles
    parallelism at a higher level.

    HOW: Builds a single user message, sends it to Gemini Flash, parses the
    verdict from the text response. No retry logic, no structured output validation,
    no evidence extraction. This is the naive path.

    Args:
        cv_text: Raw CV text for the candidate.
        job_description: Full job description text.

    Returns:
        Dict with keys:
            - verdict (str): One of the six verdict strings, parsed from text.
            - reasoning (str): The raw LLM response (unstructured).
            - raw_response (str): Full response text for audit.
            - latency_ms (int): Time taken for the LLM call in milliseconds.
            - model (str): Model identifier used.
            - error (Optional[str]): Error message if the call failed.
    """
    llm = ChatOpenAI(
        model=_BASELINE_MODEL,
        temperature=0.1,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=_OPENROUTER_BASE_URL,
        default_headers=_OPENROUTER_HEADERS,
        # WHY: No structured output — the whole point is to compare against
        # unstructured text generation, which is the naive baseline.
    )

    user_message = _USER_TEMPLATE.format(
        cv_text=cv_text.strip(),
        job_description=job_description.strip(),
    )

    start_ms = time.monotonic()
    error: Optional[str] = None
    raw_text = ""

    try:
        response = llm.invoke(
            [
                ("system", _SYSTEM_PROMPT),
                ("human", user_message),
            ]
        )
        raw_text = str(response.content)
    except Exception as exc:
        error = str(exc)
        raw_text = ""

    latency_ms = int((time.monotonic() - start_ms) * 1000)
    verdict = _parse_verdict_from_text(raw_text) if raw_text else "AMBIGUOUS"

    return {
        "verdict": verdict,
        "reasoning": raw_text,
        "raw_response": raw_text,
        "latency_ms": latency_ms,
        "model": _BASELINE_MODEL,
        "error": error,
        # WHY: Estimate cost from token count approximation.
        # google/gemini-2.5-flash-lite is $0.10/1M input + $0.40/1M output tokens.
        # Rough estimate: prompt ~600 tokens, response ~200 tokens.
        "cost_usd": (600 * 0.10 + 200 * 0.40) / 1_000_000,
    }


async def run_baseline_async(cv_text: str, job_description: str) -> dict:
    """
    WHY: The runner uses asyncio.gather() for parallel execution. The baseline
    LLM call is synchronous (langchain invoke), but we wrap it in an async function
    so the runner can gather all 10 in parallel using asyncio.to_thread.

    HOW: Delegates to run_baseline() in a thread executor via asyncio.to_thread,
    keeping the synchronous implementation as the canonical version.

    Args:
        cv_text: Raw CV text for the candidate.
        job_description: Full job description text.

    Returns:
        Same dict as run_baseline(). See run_baseline() for field documentation.
    """
    import asyncio

    return await asyncio.to_thread(run_baseline, cv_text, job_description)


__all__ = ["run_baseline", "run_baseline_async"]
