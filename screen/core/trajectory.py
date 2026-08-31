"""
WHY: A shared utility for creating TrajectoryEntry records so every node
uses the same timestamp format, cost calculation, and field structure.
Centralising this prevents subtle inconsistencies across 10 nodes (Rule 21.4).

HOW: Each node calls make_trajectory_entry() at the end of its execution,
passing its own name, the timing, cost, and a human-readable summary.
The result is appended to state['trajectory'].
"""

import time
from datetime import datetime
from typing import Optional

import pytz

from screen.core.config import settings
from screen.schemas.trajectory import TrajectoryEntry


def get_eat_timestamp() -> str:
    """
    WHY: All timestamps in this project use East Africa Time (EAT, UTC+3).
    This is the project timezone standard (mirrors byYou's Rule in RULES.md).

    HOW: Convert UTC now() to EAT using pytz. Returns ISO 8601 string.
    """
    eat_tz = pytz.timezone(settings.timezone)
    now_eat = datetime.now(tz=eat_tz)
    return now_eat.isoformat()


def estimate_token_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model_tier: int,
) -> float:
    """
    WHY: Every node that calls an LLM reports its estimated cost.
    This makes SCREEN's economics transparent — a key differentiator
    from every other tool in the market.

    HOW: Token counts come from the LLM response metadata. We multiply by
    the per-token rate for the model tier used. Returns USD.

    Note: These are estimates — actual billing may differ slightly.
    """
    if model_tier == 1:
        cost_per_1k = settings.cost_per_1k_tokens_flash
    else:
        cost_per_1k = settings.cost_per_1k_tokens_pro

    total_tokens = prompt_tokens + completion_tokens
    return round((total_tokens / 1000) * cost_per_1k, 6)


def make_trajectory_entry(
    node: str,
    start_time_ms: float,
    reasoning_summary: str,
    output_summary: str,
    evidence_keys: Optional[list[str]] = None,
    model_used: Optional[str] = None,
    cost_usd: float = 0.0,
) -> TrajectoryEntry:
    """
    WHY: Standardised constructor for TrajectoryEntry. Every node calls this
    identically — no node constructs TrajectoryEntry directly. This ensures
    all trajectory entries have the same structure, the correct EAT timestamp,
    and accurate duration_ms.

    HOW: start_time_ms is captured at the beginning of the node execution
    using time.time() * 1000. This function calculates the elapsed time.

    PRIVACY: reasoning_summary and output_summary must never contain raw CV
    text, candidate names, or any PII. Callers are responsible for this —
    the function trusts callers but the contract is documented here.
    """
    duration_ms = int((time.time() * 1000) - start_time_ms)

    return TrajectoryEntry(
        node=node,
        timestamp_eat=get_eat_timestamp(),
        reasoning_summary=reasoning_summary,
        evidence_keys=evidence_keys or [],
        model_used=model_used,
        duration_ms=max(0, duration_ms),
        cost_usd=cost_usd,
        output_summary=output_summary,
    )
