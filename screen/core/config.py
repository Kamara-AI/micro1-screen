"""
WHY: All configuration is loaded from environment variables via pydantic-settings.
No values are hardcoded — this mirrors byYou's Rule 05 (Zero Hardcoded Values)
adapted for agent configuration. This single Settings class is the only source
of truth for thresholds, model names, and API keys.

HOW: pydantic-settings reads from .env on startup. All fields are typed and
validated. The singleton `settings` is imported wherever config is needed.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    WHY: Single-class config follows the same principle as byYou's AppConfig —
    one place to read, one place to change. Adding a new threshold never
    requires hunting through node files.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── LLM APIs — provider chain: OpenRouter → OpenAI → Gemini ─────────────
    # WHY: Provider chain gives us fallback without vendor lock-in. OpenRouter
    # is primary because it offers model routing, fallback, and cost arbitrage
    # across 100+ models with a single API key. OpenAI is the direct fallback
    # (same API format as OpenRouter — zero code change). Gemini is tertiary for
    # backward compatibility with local dev environments.
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key — primary provider (routes to any model)",
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key — secondary provider (direct, same format as OpenRouter)",
    )
    gemini_api_key: str = Field(
        default="",
        description="Gemini API key — tertiary fallback for local dev",
    )

    # ── External verification tool keys (optional) ────────────────────────────
    # WHY: Both default to empty string so the pipeline degrades gracefully
    # when they are not set — verify_claims skips the relevant tool rather than crashing.
    tavily_api_key: str = Field(
        default="",
        description="Tavily API key — enables web search claim verification",
    )
    github_token: str = Field(
        default="",
        description="GitHub PAT — increases rate limit from 60 to 5,000 req/hr for GitHub API",
    )
    max_new_claims_from_github: int = Field(
        default=3,
        description="Cap on auto-discovered GitHub repo claims added per candidate (avoids noise)",
    )

    # ── Model Selection ───────────────────────────────────────────────────────
    # WHY: Three tiers map to three cognitive task classes:
    #   Tier 1 (Flash) — Structured extraction and controlled generation.
    #     parse_candidate: CV → CandidateProfile (parsing, not reasoning)
    #     candidate_feedback: template + personalisation (structure is defined)
    #     Flash/mini models are more than capable for both. Pro is overkill.
    #   Tier 2 (Mid) — Multi-hop reasoning and subtle analysis.
    #     extract_evidence: claim credibility + contradiction detection (nuanced)
    #     analyze_fit: comparative scoring across claims (comparative reasoning)
    #     detect_bias: linguistic proxy pattern recognition (subtle, high-stakes)
    #     These tasks require a model that genuinely reasons, not just pattern-matches.
    #   Tier 3 (Mid) — Synthesis and narrative writing.
    #     build_human_brief: structured narrative for a human reviewer (coherence + tone)
    #     Same tier as tier 2 because quality of reasoning still matters here.
    #
    # WHY these specific defaults:
    #   OpenRouter tier1: google/gemini-2.5-flash-lite — $0.10/M tokens, cheapest
    #     capable flash model on OpenRouter as of 2026-08. Structured extraction
    #     (parse_candidate) and template generation (candidate_feedback) do not
    #     need deep reasoning — a fast flash model is the right tool.
    #   OpenRouter tier2/3: openai/gpt-4o-mini — $0.15/M tokens. Strong structured
    #     output compliance, reliable multi-hop reasoning, and cheaper than any
    #     Anthropic Haiku variant on OpenRouter. Used for extract_evidence,
    #     analyze_fit, detect_bias, make_decision, build_human_brief.
    #   OpenAI tier1/2/3: gpt-4o-mini — capable across all tasks, widely available,
    #     no model-switching complexity when OpenAI is the fallback provider.
    #   Gemini tier1/2/3: flash/pro split — matches original design intent.
    #
    # All are config-settable — operators can tune cost vs quality per tier.
    # Use exact openrouter.ai/models slug format (NOT Anthropic date-suffix format).

    # OpenRouter model slugs (use exact openrouter.ai/models slug format)
    openrouter_model_tier1: str = Field(
        default="google/gemini-2.5-flash-lite",
        description="OpenRouter tier 1 — fast extraction and generation ($0.10/M tokens)",
    )
    openrouter_model_tier2: str = Field(
        default="openai/gpt-4o-mini",
        description="OpenRouter tier 2 — reasoning, analysis, contradiction detection ($0.15/M tokens)",
    )
    openrouter_model_tier3: str = Field(
        default="openai/gpt-4o-mini",
        description="OpenRouter tier 3 — synthesis and narrative brief writing ($0.15/M tokens)",
    )

    # OpenAI model names (direct API)
    openai_model_tier1: str = Field(
        default="gpt-4o-mini",
        description="OpenAI tier 1 — fast extraction and generation",
    )
    openai_model_tier2: str = Field(
        default="gpt-4o-mini",
        description="OpenAI tier 2 — reasoning (gpt-4o-mini is capable at this tier)",
    )
    openai_model_tier3: str = Field(
        default="gpt-4o-mini",
        description="OpenAI tier 3 — synthesis writing",
    )

    # Gemini model names (tertiary fallback)
    gemini_model_tier1: str = Field(
        default="gemini-1.5-flash",
        description="Gemini tier 1 — fast extraction (tertiary fallback)",
    )
    gemini_model_tier2: str = Field(
        default="gemini-1.5-pro",
        description="Gemini tier 2 — analysis (tertiary fallback)",
    )
    gemini_model_tier3: str = Field(
        default="gemini-1.5-pro",
        description="Gemini tier 3 — brief writing (tertiary fallback)",
    )

    llm_temperature: float = Field(
        default=0.1,
        description="Low temperature for analytical consistency across runs",
    )
    llm_max_retries: int = Field(
        default=3,
        description="Maximum LLM call retries before raising",
    )
    llm_timeout_seconds: int = Field(default=30, description="Per-call timeout in seconds")

    # ── Confidence Thresholds ─────────────────────────────────────────────────
    # WHY: All thresholds live here so they can be adjusted without touching
    # node logic. The decision node reads from settings, not from literals.
    strong_yes_threshold: float = Field(default=86.0, description="% — STRONG_YES floor")
    yes_threshold: float = Field(default=65.0, description="% — YES floor")
    ambiguous_threshold: float = Field(default=45.0, description="% — AMBIGUOUS floor")
    no_threshold: float = Field(default=25.0, description="% — NO floor; below = STRONG_NO")

    # ── Escalation Triggers ───────────────────────────────────────────────────
    escalate_on_critical_contradiction: bool = Field(default=True)
    escalate_on_bias_flag: bool = Field(default=True)
    escalate_on_unverifiable_high_confidence: bool = Field(default=True)

    # ── Cost Estimates (USD per 1K tokens, approximate) ───────────────────────
    cost_per_1k_tokens_flash: float = Field(default=0.000075)
    cost_per_1k_tokens_pro: float = Field(default=0.00125)

    # ── Environment ───────────────────────────────────────────────────────────
    env: str = Field(default="dev", description="dev | staging | prod")
    log_level: str = Field(default="INFO")
    timezone: str = Field(default="Africa/Nairobi", description="EAT — UTC+3")


# WHY: Module-level singleton — imported once, shared everywhere.
# Avoids re-reading .env on every function call.
settings = Settings()
