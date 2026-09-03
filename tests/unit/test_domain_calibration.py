"""
Tests for the domain calibration registry.

WHY: Domain calibration is the core fix for the Batch 4 Marketing failure.
These tests enforce registry completeness and correct alias matching —
if a domain is misconfigured, it will produce wrong silence flags and
incorrect P0 hard cap decisions at eval time.
"""

import pytest

from screen.core.domain_calibration import (
    DOMAIN_REGISTRY,
    GENERIC_CALIBRATION,
    DomainCalibration,
    detect_domain,
    get_calibration,
)


# ── Domain detection ───────────────────────────────────────────────────────────

class TestDetectDomain:
    def test_software_engineer(self):
        result = detect_domain("Senior Software Engineer")
        assert result is not None
        assert "engineering" in result.name.lower() or "software" in result.name.lower()

    def test_data_scientist(self):
        result = detect_domain("Senior Data Scientist")
        assert result is not None
        assert "data science" in result.name.lower() or "ml" in result.name.lower()

    def test_ml_engineer(self):
        result = detect_domain("ML Engineer")
        assert result is not None
        # Should match Data Science / ML domain, not generic Software Engineering
        assert "data science" in result.name.lower() or "ml" in result.name.lower()

    def test_digital_marketing(self):
        result = detect_domain("Senior Digital Marketing Manager")
        assert result is not None
        assert "marketing" in result.name.lower()

    def test_marketing_director(self):
        result = detect_domain("Marketing Director EMEA")
        assert result is not None
        assert "marketing" in result.name.lower()

    def test_finance(self):
        result = detect_domain("Chief Financial Officer")
        assert result is not None
        assert "finance" in result.name.lower()

    def test_fp_and_a(self):
        result = detect_domain("FP&A Manager")
        assert result is not None
        assert "finance" in result.name.lower()

    def test_supply_chain(self):
        result = detect_domain("Supply Chain Manager")
        assert result is not None
        assert "operations" in result.name.lower() or "supply chain" in result.name.lower()

    def test_operations_manager(self):
        result = detect_domain("Senior Operations Manager")
        assert result is not None
        assert "operations" in result.name.lower()

    def test_devops(self):
        result = detect_domain("DevOps Engineer")
        assert result is not None
        assert "devops" in result.name.lower() or "platform" in result.name.lower()

    def test_sre(self):
        result = detect_domain("Site Reliability Engineer")
        assert result is not None
        assert "devops" in result.name.lower() or "sre" in result.name.lower() or "platform" in result.name.lower()

    def test_cybersecurity(self):
        result = detect_domain("Cybersecurity Analyst")
        assert result is not None
        assert "security" in result.name.lower() or "cyber" in result.name.lower()

    def test_product_manager(self):
        result = detect_domain("Product Manager")
        assert result is not None
        assert "product" in result.name.lower()

    def test_customer_success(self):
        result = detect_domain("Customer Success Manager")
        assert result is not None
        assert "customer" in result.name.lower()

    def test_hr_manager(self):
        result = detect_domain("HR Manager")
        assert result is not None
        assert "hr" in result.name.lower() or "people" in result.name.lower()

    def test_legal(self):
        result = detect_domain("Legal Counsel")
        assert result is not None
        assert "legal" in result.name.lower()

    def test_ux_designer(self):
        result = detect_domain("Senior UX Designer")
        assert result is not None
        assert "design" in result.name.lower()

    def test_project_manager(self):
        result = detect_domain("Project Manager")
        assert result is not None
        assert "project" in result.name.lower() or "programme" in result.name.lower()

    def test_sales(self):
        result = detect_domain("Account Executive")
        assert result is not None
        assert "sales" in result.name.lower()

    def test_ceo(self):
        result = detect_domain("Chief Executive Officer")
        assert result is not None
        assert "executive" in result.name.lower() or "management" in result.name.lower()

    def test_unknown_returns_none(self):
        result = detect_domain("Intergalactic Procurement Wizard")
        assert result is None

    def test_empty_string_returns_none(self):
        result = detect_domain("")
        assert result is None

    def test_whitespace_returns_none(self):
        result = detect_domain("   ")
        assert result is None

    def test_case_insensitive(self):
        lower = detect_domain("senior software engineer")
        upper = detect_domain("SENIOR SOFTWARE ENGINEER")
        mixed = detect_domain("Senior Software Engineer")
        # All should match the same domain
        assert lower is not None
        assert upper is not None
        assert mixed is not None
        assert lower.name == upper.name == mixed.name


# ── get_calibration never throws ───────────────────────────────────────────────

class TestGetCalibration:
    @pytest.mark.parametrize("role_type", [
        "Senior Software Engineer",
        "Marketing Manager",
        "CFO",
        "Supply Chain Director",
        "Random Unknown Role XYZ",
        "",
        "   ",
        "123",
        "a" * 500,  # Extremely long string
    ])
    def test_never_throws(self, role_type: str):
        cal = get_calibration(role_type)
        assert isinstance(cal, DomainCalibration)

    def test_unknown_returns_generic(self):
        cal = get_calibration("Intergalactic Procurement Wizard XYZ")
        assert cal is GENERIC_CALIBRATION

    def test_known_role_does_not_return_generic(self):
        cal = get_calibration("Senior Software Engineer")
        assert cal is not GENERIC_CALIBRATION
        assert cal.name != GENERIC_CALIBRATION.name


# ── Registry completeness ──────────────────────────────────────────────────────

class TestRegistryCompleteness:
    def test_minimum_domain_count(self):
        assert len(DOMAIN_REGISTRY) >= 16, (
            f"Expected at least 16 domains, got {len(DOMAIN_REGISTRY)}"
        )

    def test_all_domains_have_name(self):
        for domain in DOMAIN_REGISTRY:
            assert domain.name, f"Domain has empty name"
            assert len(domain.name) > 3

    def test_all_domains_have_aliases(self):
        for domain in DOMAIN_REGISTRY:
            assert len(domain.aliases) >= 2, (
                f"{domain.name} has only {len(domain.aliases)} aliases"
            )

    def test_all_domains_have_minimum_keywords(self):
        for domain in DOMAIN_REGISTRY:
            assert len(domain.domain_keywords) >= 10, (
                f"{domain.name} has only {len(domain.domain_keywords)} domain_keywords"
            )

    def test_all_domains_have_hard_anchors(self):
        for domain in DOMAIN_REGISTRY:
            assert len(domain.hard_anchor_patterns) >= 4, (
                f"{domain.name} has only {len(domain.hard_anchor_patterns)} hard_anchor_patterns"
            )

    def test_all_domains_have_tier_c_traps(self):
        for domain in DOMAIN_REGISTRY:
            assert len(domain.tier_c_traps) >= 4, (
                f"{domain.name} has only {len(domain.tier_c_traps)} tier_c_traps"
            )

    def test_minimum_domain_keyword_count_is_positive(self):
        for domain in DOMAIN_REGISTRY:
            assert domain.minimum_domain_keyword_count >= 1, (
                f"{domain.name} has minimum_domain_keyword_count < 1"
            )

    def test_production_check_enabled_domains_have_keywords(self):
        for domain in DOMAIN_REGISTRY:
            if domain.production_check_enabled:
                assert len(domain.production_check_keywords) >= 5, (
                    f"{domain.name} has production_check_enabled=True "
                    f"but only {len(domain.production_check_keywords)} production_check_keywords"
                )

    def test_no_duplicate_names(self):
        names = [d.name for d in DOMAIN_REGISTRY]
        assert len(names) == len(set(names)), "Duplicate domain names found"

    def test_generic_calibration_exists(self):
        assert GENERIC_CALIBRATION is not None
        assert isinstance(GENERIC_CALIBRATION, DomainCalibration)
        assert GENERIC_CALIBRATION.name == "General / Unknown"

    def test_all_aliases_are_lowercase(self):
        for domain in DOMAIN_REGISTRY:
            for alias in domain.aliases:
                assert alias == alias.lower(), (
                    f"{domain.name} alias '{alias}' is not lowercase — "
                    f"detect_domain() lowercases role_type but alias must also be lowercase"
                )


# ── Production check and skill conflict logic ──────────────────────────────────

class TestCalibrationFlags:
    def test_software_engineering_production_check_enabled(self):
        cal = get_calibration("Senior Software Engineer")
        assert cal.production_check_enabled is True

    def test_data_science_production_check_enabled(self):
        cal = get_calibration("Senior Data Scientist")
        assert cal.production_check_enabled is True

    def test_devops_production_check_enabled(self):
        cal = get_calibration("DevOps Engineer")
        assert cal.production_check_enabled is True

    def test_marketing_production_check_disabled(self):
        cal = get_calibration("Marketing Manager")
        assert cal.production_check_enabled is False

    def test_sales_production_check_disabled(self):
        cal = get_calibration("Account Executive")
        assert cal.production_check_enabled is False

    def test_hr_production_check_disabled(self):
        cal = get_calibration("HR Manager")
        assert cal.production_check_enabled is False

    def test_software_engineering_skill_conflict_enabled(self):
        cal = get_calibration("Senior Software Engineer")
        assert cal.skill_conflict_check_enabled is True

    def test_data_science_skill_conflict_enabled(self):
        cal = get_calibration("Senior Data Scientist")
        assert cal.skill_conflict_check_enabled is True

    def test_marketing_skill_conflict_disabled(self):
        # WHY: Disabled. Senior marketers write outcome-language bullets ("grew traffic
        # 45%") without naming every tool in every line. The conflict check produces
        # systematic false positives: "Expert: GA4" + outcome bullets → wrongly ESCALATED.
        # Domain calibration catches weak candidates via 0 hard anchors + high Tier-C
        # trap count in the deterministic facts block instead.
        cal = get_calibration("Marketing Manager")
        assert cal.skill_conflict_check_enabled is False

    def test_operations_skill_conflict_disabled(self):
        cal = get_calibration("Supply Chain Manager")
        assert cal.skill_conflict_check_enabled is False

    def test_sales_skill_conflict_disabled(self):
        cal = get_calibration("Account Executive")
        assert cal.skill_conflict_check_enabled is False

    def test_hr_skill_conflict_disabled(self):
        cal = get_calibration("HR Manager")
        assert cal.skill_conflict_check_enabled is False


# ── Specific domain content validation ────────────────────────────────────────

class TestDomainContent:
    def test_marketing_has_roas_in_keywords(self):
        cal = get_calibration("Marketing Manager")
        assert "roas" in cal.domain_keywords

    def test_sales_has_quota_in_keywords(self):
        cal = get_calibration("Account Executive")
        assert "quota" in cal.domain_keywords

    def test_supply_chain_has_alien_domains(self):
        cal = get_calibration("Supply Chain Manager")
        assert len(cal.hard_cap_alien_domains) >= 3

    def test_finance_has_pl_in_keywords(self):
        cal = get_calibration("CFO")
        assert "p&l" in cal.domain_keywords

    def test_ds_ml_has_production_keywords(self):
        cal = get_calibration("Senior Data Scientist")
        assert "deployed" in cal.production_check_keywords or "in production" in cal.production_check_keywords

    def test_cybersecurity_has_frameworks_in_keywords(self):
        cal = get_calibration("Cybersecurity Analyst")
        keywords_combined = " ".join(cal.domain_keywords)
        assert any(fw in keywords_combined for fw in ["iso 27001", "soc 2", "nist"])
