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

    # ── LLM APIs ──────────────────────────────────────────────────────────────
    gemini_api_key: str = Field(..., description="Gemini API key — required")
    openai_api_key: str = Field(default="", description="OpenAI key — fallback only")

    # ── Model Selection ───────────────────────────────────────────────────────
    gemini_model_tier1: str = Field(
        default="gemini-1.5-flash",
        description="Fast pre-filter model — cheap, instant hard-requirement checks",
    )
    gemini_model_tier2: str = Field(
        default="gemini-1.5-pro",
        description="Deep analysis model — evidence extraction, fit analysis, bias check",
    )
    gemini_model_tier3: str = Field(
        default="gemini-1.5-pro",
        description="Human brief model — structured escalation brief generation",
    )
    llm_temperature: float = Field(
        default=0.1,
        description="Low temperature for analytical consistency across runs",
    )
    llm_max_retries: int = Field(
        default=3,
        description="Maximum LLM call retries before raising (mirrors Rule 07 iteration cap)",
    )
    llm_timeout_seconds: int = Field(default=30, description="Per-call timeout in seconds")

    # ── Confidence Thresholds ─────────────────────────────────────────────────
    # WHY: All thresholds live here so they can be adjusted without touching
    # node logic. The decision node reads from settings, not from literals.
    strong_yes_threshold: float = Field(default=80.0, description="% — STRONG_YES floor")
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
