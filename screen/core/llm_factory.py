"""
WHY: Single source of truth for LLM client construction. Every node that needs
an LLM calls build_llm(tier) — they never import a specific provider directly.

This gives us three things:
  1. Provider chain without vendor lock-in — OpenRouter → OpenAI → Gemini,
     selected by which API key is configured. Swap providers by setting one env var.
  2. Model-per-task selection — Tier 1 (extraction/generation) uses cheap flash
     models; Tier 2/3 (reasoning/synthesis) uses capable mid-tier models. The
     right model for the right cognitive task, not one model for everything.
  3. Glass-box traceability — get_active_model(tier) returns "provider:model" so
     every trajectory entry records exactly which provider and model ran.

HOW: build_llm() detects the active provider from available API keys (in priority
order), constructs the appropriate LangChain model client, and caches it. The
cache means each tier instantiates once per process — not once per LLM call.

PROVIDER SELECTION:
  OpenRouter — primary. Routes to any model on any provider. Gives cost arbitrage,
    model fallback if a specific model goes down, and a single billing surface.
    Uses ChatOpenAI with a custom base_url (OpenRouter is OpenAI API-compatible).
  OpenAI — secondary. Direct API, same format as OpenRouter. Zero code changes
    when falling back. Widely available — judges and developers likely have a key.
  Gemini — tertiary. Backward-compatible fallback for local dev environments
    where only a Gemini key is set (matches original SCREEN setup).

WHY @lru_cache: LLM clients are stateless connection pools. Building one per
call wastes time and connection overhead. The cache key is the tier string — we
build at most 3 clients (one per tier) per process lifetime.
"""

from functools import lru_cache
from typing import Literal

from langchain_core.language_models import BaseChatModel

from screen.core.config import settings
from screen.core.logging_config import get_logger

logger = get_logger(__name__)

Tier = Literal["tier1", "tier2", "tier3"]

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# WHY: OpenRouter requires these headers to track usage and attribute requests.
# The X-Title header appears in the OpenRouter dashboard — useful for cost tracking.
_OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/Kamara-AI/micro1-screen",
    "X-Title": "SCREEN - micro1 Hackathon 2026",  # ASCII only — HTTP headers cannot contain em dashes
}


def _detect_provider() -> str:
    """
    WHY: Provider is determined by which API key is set — no extra config needed.
    Priority: OpenRouter > OpenAI > Gemini. First key found wins.

    Returns:
        Provider string: "openrouter", "openai", or "gemini".

    Raises:
        RuntimeError: If no API key is configured for any provider.
    """
    if settings.openrouter_api_key:
        return "openrouter"
    if settings.openai_api_key:
        return "openai"
    if settings.gemini_api_key:
        return "gemini"
    raise RuntimeError(
        "No LLM API key configured. Set one of: "
        "OPENROUTER_API_KEY (recommended), OPENAI_API_KEY, or GEMINI_API_KEY."
    )


def _model_for_tier(provider: str, tier: Tier) -> str:
    """
    WHY: Model selection is a function of both provider and tier. Each provider
    has its own model naming convention — OpenRouter uses slugs, OpenAI uses
    model names, Gemini uses model IDs.

    Args:
        provider: Active provider string.
        tier: Cognitive task tier.

    Returns:
        Model identifier string for the given provider and tier.
    """
    tier_map: dict[str, dict[Tier, str]] = {
        "openrouter": {
            "tier1": settings.openrouter_model_tier1,
            "tier2": settings.openrouter_model_tier2,
            "tier3": settings.openrouter_model_tier3,
        },
        "openai": {
            "tier1": settings.openai_model_tier1,
            "tier2": settings.openai_model_tier2,
            "tier3": settings.openai_model_tier3,
        },
        "gemini": {
            "tier1": settings.gemini_model_tier1,
            "tier2": settings.gemini_model_tier2,
            "tier3": settings.gemini_model_tier3,
        },
    }
    return tier_map[provider][tier]


def get_active_model(tier: Tier) -> str:
    """
    WHY: Nodes log model_used in their trajectory entry. This must reflect
    the actual provider and model that ran — not a hardcoded string. Returns
    "provider:model" so the audit trail shows both dimensions.

    Example returns:
      "openrouter:anthropic/claude-3.5-haiku"
      "openai:gpt-4o-mini"
      "gemini:gemini-1.5-pro"

    Args:
        tier: Cognitive task tier.

    Returns:
        "provider:model" string for trajectory logging.
    """
    provider = _detect_provider()
    model = _model_for_tier(provider, tier)
    return f"{provider}:{model}"


@lru_cache(maxsize=3)  # one entry per tier — tier1, tier2, tier3
def build_llm(tier: Tier) -> BaseChatModel:
    """
    WHY: Central factory — all LLM-using nodes call this instead of importing
    a provider-specific client. Provider detection and model selection happen
    here once; the result is cached for the process lifetime.

    HOW:
      - OpenRouter and OpenAI both use ChatOpenAI (same API format).
        OpenRouter uses a custom base_url and authentication headers.
      - Gemini uses ChatGoogleGenerativeAI (different client library).

    Args:
        tier: Cognitive task tier — determines which model is selected.

    Returns:
        Cached LangChain BaseChatModel instance for the active provider and tier.
    """
    provider = _detect_provider()
    model = _model_for_tier(provider, tier)

    logger.info(
        "llm_factory: building client",
        provider=provider,
        tier=tier,
        model=model,
    )

    if provider in ("openrouter", "openai"):
        from langchain_openai import ChatOpenAI

        kwargs: dict = {
            "model": model,
            "temperature": settings.llm_temperature,
            "max_retries": settings.llm_max_retries,
            "timeout": settings.llm_timeout_seconds,
        }

        if provider == "openrouter":
            kwargs["openai_api_key"] = settings.openrouter_api_key
            kwargs["openai_api_base"] = _OPENROUTER_BASE_URL
            kwargs["default_headers"] = _OPENROUTER_HEADERS
        else:
            kwargs["openai_api_key"] = settings.openai_api_key

        return ChatOpenAI(**kwargs)

    else:  # gemini — tertiary fallback
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.llm_temperature,
            max_retries=settings.llm_max_retries,
        )
