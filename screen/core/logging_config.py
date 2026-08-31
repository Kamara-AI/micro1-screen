"""
WHY: Structured logging gives us machine-readable logs that can be queried,
filtered, and shipped to observability tools without string parsing.
structlog is used over Python's stdlib logging because it makes adding
structured context (node name, candidate_id, duration_ms) natural.

CRITICAL PRIVACY RULE: CV text, candidate names, and any personally identifiable
information must NEVER appear in logs. Only IDs, node names, verdict codes,
duration, and cost are logged. This mirrors byYou's Rule 09 (no financial
data in logs) adapted for candidate privacy.

HOW: Call setup_logging() once at application startup. Then use get_logger()
in each module to get a pre-configured logger with the module name bound.
"""

import logging
import sys
from typing import Any

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    WHY: Configures structlog with ConsoleRenderer for dev and JSON for prod.
    The current implementation uses PrintLoggerFactory which outputs directly
    without needing stdlib formatter wiring.
    """
    log_level_int = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stdout, level=log_level_int)

    # WHY: add_logger_name requires a stdlib Logger with a .name attribute.
    # PrintLoggerFactory produces a PrintLogger which has no .name — that
    # processor is removed. The module name is bound at get_logger(name) call
    # time via structlog's context system instead.
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    WHY: Returns a logger pre-bound with the module name. Use this in every
    node file so all log lines are traceable to their source without adding
    the name manually to every log call.

    HOW: structlog.get_logger() is lazy — the name is bound at call time,
    not at import time. This is safe to call at module level.
    """
    return structlog.get_logger(name)


# ── Logging contract: what IS and IS NOT allowed in log fields ─────────────────
#
# ALLOWED:
#   candidate_id (opaque identifier only)
#   batch_id
#   node (pipeline stage name)
#   verdict (STRONG_YES / YES / AMBIGUOUS / NO / STRONG_NO / ESCALATE)
#   confidence_pct (float)
#   duration_ms (int)
#   cost_usd (float)
#   error_code (from ScreenException)
#   tier (1, 2, or 3)
#
# NEVER LOG:
#   cv_text (raw CV content — PII)
#   candidate name
#   email address
#   company names from the CV
#   job descriptions with identifying details
#   raw LLM output strings
#   any field from CandidateProfile, EvidenceBundle, or FitAnalysis
#
# Rationale: SCREEN is designed for the EU AI Act (high-risk employment AI)
# and NYC Local Law 144 audit trail requirements. Keeping candidate data out
# of logs is not just privacy hygiene — it's a compliance requirement.
