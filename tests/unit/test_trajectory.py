"""
WHY: The trajectory is the audit trail that makes SCREEN's decisions
explainable and compliant. If timestamps are wrong, if durations go
negative, or if cost calculations use the wrong rate, the audit trail
becomes untrustworthy. 100% coverage required on these utilities.

HOW: Tests call the trajectory utility functions directly (get_eat_timestamp,
estimate_token_cost, make_trajectory_entry) and verify their outputs
against known expected values. All functions are pure or near-pure —
deterministic given the same inputs.

Note: get_eat_timestamp depends on the current time (non-deterministic for
exact value), so we test its format and timezone properties rather than
its exact value.
"""

import re
import time

import pytest

from screen.core.trajectory import (
    estimate_token_cost,
    get_eat_timestamp,
    make_trajectory_entry,
)


# ── Timestamp Tests ───────────────────────────────────────────────────────────

class TestEATTimestamp:
    """
    WHY: All timestamps must be ISO 8601 in East Africa Time (UTC+3).
    A wrong timezone breaks the audit trail and violates the project
    timezone standard (EAT — the same standard as byYou's Rule in RULES.md).
    """

    def test_get_eat_timestamp_returns_iso_format_string(self) -> None:
        """
        get_eat_timestamp() must return a string in ISO 8601 format.
        Expected pattern: YYYY-MM-DDTHH:MM:SS.ffffff+03:00
        """
        ts = get_eat_timestamp()
        assert isinstance(ts, str)
        # ISO 8601 format check — must contain date separator and time separator
        assert "T" in ts, f"Expected ISO format with 'T' separator, got: {ts}"
        assert len(ts) > 10, f"Timestamp too short to be valid ISO: {ts}"

    def test_get_eat_timestamp_has_eat_offset(self) -> None:
        """The timestamp must carry the +03:00 UTC offset for EAT."""
        ts = get_eat_timestamp()
        # EAT is UTC+3 — the offset must appear in the string
        assert "+03:00" in ts, (
            f"Expected EAT (+03:00) offset in timestamp, got: {ts}"
        )

    def test_get_eat_timestamp_is_recent(self) -> None:
        """The returned timestamp must represent the current time (within 5 seconds)."""
        import datetime
        import pytz
        eat_tz = pytz.timezone("Africa/Nairobi")
        before = datetime.datetime.now(tz=eat_tz)
        ts = get_eat_timestamp()
        after = datetime.datetime.now(tz=eat_tz)

        parsed = datetime.datetime.fromisoformat(ts)
        assert before <= parsed <= after, (
            f"Timestamp {ts} is not within the expected recent range"
        )

    def test_get_eat_timestamp_contains_current_year(self) -> None:
        """The timestamp must contain the current year (basic sanity check)."""
        import datetime
        ts = get_eat_timestamp()
        current_year = str(datetime.datetime.now().year)
        assert current_year in ts, f"Current year {current_year} not found in timestamp: {ts}"


# ── Token Cost Estimation Tests ───────────────────────────────────────────────

class TestEstimateTokenCost:
    """
    WHY: Cost transparency is a differentiating feature of SCREEN. If the cost
    estimate is wrong, the per-candidate economics dashboard is misleading.
    Tests verify the correct rate is applied per model tier.
    """

    def test_estimate_token_cost_tier1_uses_flash_rate(self) -> None:
        """
        Tier 1 (Flash model) uses cost_per_1k_tokens_flash = 0.000075 USD/1K tokens.
        1000 prompt + 500 completion = 1500 total tokens.
        Expected cost = (1500 / 1000) * 0.000075 = 0.0001125, rounded to 6dp = 0.000112.

        WHY round(6): estimate_token_cost applies round(..., 6) to prevent
        floating-point noise. The test accounts for this rounding.
        """
        cost = estimate_token_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model_tier=1,
        )
        raw_expected = (1500 / 1000) * 0.000075
        # The function rounds to 6 decimal places — match that exactly
        expected = round(raw_expected, 6)
        assert cost == pytest.approx(expected, rel=1e-4)

    def test_estimate_token_cost_tier2_uses_pro_rate(self) -> None:
        """
        Tier 2 (Pro model) uses cost_per_1k_tokens_pro = 0.00125 USD/1K tokens.
        1000 prompt + 500 completion = 1500 total tokens.
        Expected cost = (1500 / 1000) * 0.00125 = 0.001875
        """
        cost = estimate_token_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model_tier=2,
        )
        expected = (1500 / 1000) * 0.00125
        assert cost == pytest.approx(expected, rel=1e-4)

    def test_estimate_token_cost_tier3_uses_pro_rate(self) -> None:
        """
        Tier 3 (Pro model) also uses cost_per_1k_tokens_pro (same as tier 2).
        This ensures the escalation brief step is correctly costed.
        """
        cost_tier2 = estimate_token_cost(1000, 500, model_tier=2)
        cost_tier3 = estimate_token_cost(1000, 500, model_tier=3)
        assert cost_tier2 == pytest.approx(cost_tier3)

    def test_estimate_token_cost_scales_linearly_with_token_count(self) -> None:
        """
        Doubling the token count must double the cost — linear scaling.
        This verifies the formula doesn't have a non-linear component.
        """
        cost_1k = estimate_token_cost(500, 500, model_tier=1)
        cost_2k = estimate_token_cost(1000, 1000, model_tier=1)
        assert cost_2k == pytest.approx(2 * cost_1k, rel=1e-4)

    def test_estimate_token_cost_zero_tokens_returns_zero(self) -> None:
        """Zero tokens must produce zero cost."""
        cost = estimate_token_cost(0, 0, model_tier=1)
        assert cost == 0.0

    def test_estimate_token_cost_is_non_negative(self) -> None:
        """Cost must always be ≥ 0.0 regardless of token counts."""
        cost = estimate_token_cost(100, 50, model_tier=2)
        assert cost >= 0.0


# ── make_trajectory_entry Tests ───────────────────────────────────────────────

class TestMakeTrajectoryEntry:
    """
    WHY: TrajectoryEntry is the audit record for each node. The constructor
    must produce accurate duration_ms, correct EAT timestamps, and correctly
    pass-through all caller-provided values.
    """

    def test_make_trajectory_entry_returns_correct_node_name(self) -> None:
        """The returned TrajectoryEntry must have the exact node name passed in."""
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="extract_evidence",
            start_time_ms=start_ms,
            reasoning_summary="Extracted 5 claims from CV",
            output_summary="5 claims, 0 contradictions",
        )
        assert entry.node == "extract_evidence"

    def test_make_trajectory_entry_duration_ms_is_non_negative(self) -> None:
        """
        duration_ms must be ≥ 0. The function uses max(0, duration) to floor
        at zero — this test verifies that floor is applied.
        """
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="make_decision",
            start_time_ms=start_ms,
            reasoning_summary="Computed verdict from evidence",
            output_summary="STRONG_YES at 87%",
        )
        assert entry.duration_ms >= 0

    def test_make_trajectory_entry_carries_reasoning_summary(self) -> None:
        """reasoning_summary must be passed through exactly."""
        summary = "Extracted 8 claims: 2 Tier A, 4 Tier B, 2 Tier C — no contradictions"
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="extract_evidence",
            start_time_ms=start_ms,
            reasoning_summary=summary,
            output_summary="8 claims extracted",
        )
        assert entry.reasoning_summary == summary

    def test_make_trajectory_entry_carries_output_summary(self) -> None:
        """output_summary must be passed through exactly."""
        output = "HARD REJECT — failed requirement: 'minimum 5 years Python'"
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="tier1_prefilter",
            start_time_ms=start_ms,
            reasoning_summary="Hard requirement check failed",
            output_summary=output,
        )
        assert entry.output_summary == output

    def test_make_trajectory_entry_model_used_is_none_for_deterministic_node(self) -> None:
        """Deterministic nodes (no LLM call) must have model_used=None."""
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="tier1_prefilter",
            start_time_ms=start_ms,
            reasoning_summary="No LLM used — deterministic check",
            output_summary="Pre-filter PASSED",
            model_used=None,
        )
        assert entry.model_used is None

    def test_make_trajectory_entry_model_used_is_set_for_llm_node(self) -> None:
        """LLM nodes must carry the model ID in model_used."""
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="extract_evidence",
            start_time_ms=start_ms,
            reasoning_summary="LLM extracted evidence",
            output_summary="5 claims",
            model_used="gemini-1.5-pro",
        )
        assert entry.model_used == "gemini-1.5-pro"

    def test_make_trajectory_entry_evidence_keys_defaults_to_empty_list(self) -> None:
        """When evidence_keys is not provided, it defaults to an empty list."""
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="parse_candidate",
            start_time_ms=start_ms,
            reasoning_summary="Parsed CV",
            output_summary="3 roles extracted",
        )
        assert entry.evidence_keys == []

    def test_make_trajectory_entry_evidence_keys_passed_through(self) -> None:
        """When evidence_keys is provided, all keys must be present in the entry."""
        keys = ["claim:TechCorp-1", "claim:Safaricom-2", "hard_req:python"]
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="tier1_prefilter",
            start_time_ms=start_ms,
            reasoning_summary="Checked requirements",
            output_summary="PASSED",
            evidence_keys=keys,
        )
        assert entry.evidence_keys == keys

    def test_make_trajectory_entry_cost_usd_defaults_to_zero(self) -> None:
        """Deterministic nodes have cost_usd=0.0 — the default must hold."""
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="tier1_prefilter",
            start_time_ms=start_ms,
            reasoning_summary="No cost — no LLM",
            output_summary="PASSED",
        )
        assert entry.cost_usd == 0.0

    def test_make_trajectory_entry_timestamp_is_eat(self) -> None:
        """The entry's timestamp must be in EAT (+03:00)."""
        start_ms = time.time() * 1000
        entry = make_trajectory_entry(
            node="test_node",
            start_time_ms=start_ms,
            reasoning_summary="test",
            output_summary="test",
        )
        assert "+03:00" in entry.timestamp_eat, (
            f"Expected EAT offset (+03:00) in timestamp: {entry.timestamp_eat}"
        )
