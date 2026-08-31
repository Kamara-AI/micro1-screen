"""
WHY: Shared fixtures prevent duplication across test files. A canonical
CandidateProfile, EvidenceBundle, and FitAnalysis fixture means tests
focus on what they're testing, not on setup.

HOW: All fixtures use pytest's function scope by default so each test gets
a fresh object. Models are frozen (immutable) so there is no risk of
cross-test contamination from shared mutable state.

IMPORTANT: screen.core.config.Settings() runs at *module import time* and
requires GEMINI_API_KEY as a mandatory env var. We must set it in os.environ
HERE, at conftest.py module level, BEFORE any `screen.*` import happens.
The monkeypatch autouse fixture keeps it set for each test function as well.
"""

import os

# ── Must be set BEFORE any `screen.*` import — Settings() is a module-level singleton ──
# WHY: pydantic-settings reads os.environ at class instantiation time.
# If this key is absent when `screen.core.config` is first imported (during
# pytest collection), every test file that imports a screen module will fail.
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-real")
os.environ.setdefault("ENV", "test")

import pytest

from screen.schemas.analysis import FitAnalysis, LearningVelocityEvidence
from screen.schemas.candidate import CandidateProfile, EducationEntry, RoleEntry
from screen.schemas.evidence import Claim, Contradiction, EvidenceBundle, SilenceFlag
from screen.schemas.input import ScreeningInput


# ── Environment bootstrap ─────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    WHY: Ensures GEMINI_API_KEY remains set for every test function's lifetime.
    The module-level os.environ.setdefault() above handles the import-time case;
    this fixture ensures no test can accidentally remove the key mid-session.

    HOW: monkeypatch.setenv re-sets the value and automatically cleans up
    after each test. Belt-and-suspenders: both module-level and fixture level.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ENV", "test")


# ── CandidateProfile fixtures ─────────────────────────────────────────────────

@pytest.fixture()
def sample_candidate_profile() -> CandidateProfile:
    """
    WHY: A fully-populated CandidateProfile with 3 roles covers the common
    case for integration and unit tests that need a realistic candidate structure.

    HOW: Built from concrete, plausible data so silence-flag tests have
    something real to work against (quantified outcomes, team sizes present).
    """
    return CandidateProfile(
        candidate_id="cand-001",
        anonymised_name="CANDIDATE",
        roles=[
            RoleEntry(
                title="Senior Software Engineer",
                company="TechCorp Kenya",
                start_date="2021-03",
                end_date="Present",
                duration_months=30,
                achievements=[
                    "Led migration of monolith to microservices, reducing deployment time by 60%",
                    "Mentored a team of 8 engineers across 3 squads",
                    "Architected the real-time payments API processing 50K transactions/day",
                ],
                is_quantified=True,
                team_size_mentioned=8,
            ),
            RoleEntry(
                title="Software Engineer",
                company="Safaricom PLC",
                start_date="2018-06",
                end_date="2021-02",
                duration_months=32,
                achievements=[
                    "Built USSD gateway integration for M-Pesa API",
                    "Reduced API error rate from 4.2% to 0.3% via circuit-breaker implementation",
                ],
                is_quantified=True,
                team_size_mentioned=5,
            ),
            RoleEntry(
                title="Junior Developer",
                company="Nairobi Startup Hub",
                start_date="2016-09",
                end_date="2018-05",
                duration_months=20,
                achievements=[
                    "Developed internal CRM tool using Django and PostgreSQL",
                    "Deployed 3 client-facing web applications",
                ],
                is_quantified=True,
                team_size_mentioned=None,
            ),
        ],
        education=[
            EducationEntry(
                institution="University of Nairobi",
                degree="BSc Computer Science",
                field_of_study="Computer Science",
                graduation_year=2016,
                is_traditional=True,
            )
        ],
        skills_stated=["Python", "Go", "PostgreSQL", "Kubernetes", "AWS", "Redis"],
        employment_gaps=[],
        total_years_experience=8.0,
        career_start_year=2016,
        has_non_linear_path=False,
        highest_education_level="bachelors",
    )


# ── EvidenceBundle fixtures ───────────────────────────────────────────────────

@pytest.fixture()
def sample_evidence_bundle_strong() -> EvidenceBundle:
    """
    WHY: High-quality evidence — mix of Tier A and B claims with no contradictions.
    Used when testing paths that should produce STRONG_YES or YES verdicts.

    HOW: Two Tier A (verified) and two Tier B (stated) claims, no silence flags.
    total_weighted_score = 1.0 + 1.0 + 0.7 + 0.7 = 3.4
    """
    return EvidenceBundle(
        candidate_id="cand-001",
        claims=[
            Claim(
                text="Led migration of monolith to microservices at TechCorp — 60% deployment time reduction",
                tier="A",
                confidence_weight=1.0,
                source_location="Role at TechCorp Kenya 2021–Present, bullet 1",
                is_verifiable_externally=True,
            ),
            Claim(
                text="Architected real-time payments API processing 50K transactions/day",
                tier="A",
                confidence_weight=1.0,
                source_location="Role at TechCorp Kenya 2021–Present, bullet 3",
                is_verifiable_externally=True,
            ),
            Claim(
                text="Reduced API error rate from 4.2% to 0.3% at Safaricom",
                tier="B",
                confidence_weight=0.7,
                source_location="Role at Safaricom PLC 2018–2021, bullet 2",
                is_verifiable_externally=False,
            ),
            Claim(
                text="Mentored team of 8 engineers across 3 squads",
                tier="B",
                confidence_weight=0.7,
                source_location="Role at TechCorp Kenya 2021–Present, bullet 2",
                is_verifiable_externally=False,
            ),
        ],
        contradictions=[],
        silence_flags=[],
        builder_signals=["architected", "built from scratch", "zero to one migration", "launched payments API"],
        maintainer_signals=[],
        builder_maintainer_verdict="builder",
        has_critical_contradiction=False,
        has_unverifiable_high_stakes_claim=False,
    )


@pytest.fixture()
def sample_evidence_bundle_weak() -> EvidenceBundle:
    """
    WHY: Poor-quality evidence — all Tier C claims with one moderate contradiction.
    Used when testing paths that should produce NO or AMBIGUOUS verdicts.

    HOW: Three Tier C claims (0.3 each) and one moderate contradiction.
    total_weighted_score = 0.3 + 0.3 + 0.3 = 0.9
    silence_penalty = 0.15 (one medium-severity silence flag)
    """
    return EvidenceBundle(
        candidate_id="cand-002",
        claims=[
            Claim(
                text="Worked on backend projects",
                tier="C",
                confidence_weight=0.3,
                source_location="Role at Unknown Co, bullet 1",
                is_verifiable_externally=False,
            ),
            Claim(
                text="Managed various engineering tasks",
                tier="C",
                confidence_weight=0.3,
                source_location="Role at Unknown Co, bullet 2",
                is_verifiable_externally=False,
            ),
            Claim(
                text="Led team on unspecified initiatives",
                tier="C",
                confidence_weight=0.3,
                source_location="Role at Unknown Co, bullet 3",
                is_verifiable_externally=False,
            ),
        ],
        contradictions=[
            Contradiction(
                claim_a="Claims to have led a team of 50 engineers",
                claim_b="Company had 12 total employees at the time",
                contradiction_type="scope_inflation",
                severity="moderate",
                explanation="A team of 50 engineers cannot exist inside a 12-person company",
            )
        ],
        silence_flags=[
            SilenceFlag(
                expected_signal="quantified outcomes for senior role",
                absence_interpretation="Senior engineers are expected to state measurable impact",
                severity="medium",
            )
        ],
        builder_signals=[],
        maintainer_signals=["managed", "oversaw", "maintained"],
        builder_maintainer_verdict="maintainer",
        has_critical_contradiction=False,
        has_unverifiable_high_stakes_claim=False,
    )


@pytest.fixture()
def sample_evidence_bundle_escalate() -> EvidenceBundle:
    """
    WHY: Evidence bundle that should trigger ESCALATE routing — has a critical
    contradiction AND an unverifiable high-stakes claim.

    Used when testing the ESCALATE verdict path and build_human_brief routing.
    """
    return EvidenceBundle(
        candidate_id="cand-003",
        claims=[
            Claim(
                text="CTO of DataCorp from 2018–2020",
                tier="B",
                confidence_weight=0.7,
                source_location="Role at DataCorp, title field",
                is_verifiable_externally=False,
            ),
            Claim(
                text="Built ML platform serving 10M users",
                tier="B",
                confidence_weight=0.7,
                source_location="Role at DataCorp, bullet 1",
                is_verifiable_externally=False,
            ),
        ],
        contradictions=[
            Contradiction(
                claim_a="Claims employment at DataCorp from 2018",
                claim_b="DataCorp was founded in 2020 according to Companies House",
                contradiction_type="temporal",
                severity="critical",
                explanation="It is impossible to work at a company before it was incorporated",
            )
        ],
        silence_flags=[
            SilenceFlag(
                expected_signal="quantified outcomes for CTO-level role",
                absence_interpretation="C-suite roles require evidenced organisational impact",
                severity="high",
            )
        ],
        builder_signals=["built ML platform"],
        maintainer_signals=[],
        builder_maintainer_verdict="insufficient_data",
        has_critical_contradiction=True,
        has_unverifiable_high_stakes_claim=True,
    )


# ── FitAnalysis fixtures ──────────────────────────────────────────────────────

@pytest.fixture()
def sample_fit_analysis_high() -> FitAnalysis:
    """
    WHY: All dimension scores ≥ 0.8 — represents a strong fit candidate.
    Used for testing the high-confidence verdict path.

    HOW: composite_fit_score = 0.9*0.35 + 0.85*0.25 + 0.85*0.25 + 0.8*0.15
       = 0.315 + 0.2125 + 0.2125 + 0.12 = 0.86
    """
    return FitAnalysis(
        candidate_id="cand-001",
        technical_fit=0.9,
        technical_fit_rationale="Strong Python and distributed systems background matches role requirements",
        experience_level_fit=0.85,
        experience_level_rationale="8 years experience appropriate for senior engineering role",
        learning_velocity_score=0.85,
        learning_velocity_rationale="Demonstrated skill growth from Django to microservices to Kubernetes",
        learning_velocity_evidence=LearningVelocityEvidence(
            new_skills_across_roles=["Go", "Kubernetes", "gRPC"],
            self_directed_signals=["AWS certification", "open source contributions"],
            promoted_into_unfamiliar=False,
            stagnation_flags=[],
        ),
        builder_maintainer_score=0.8,
        career_shape="ascending",
        career_velocity="Promoted approximately every 2.5 years with increasing scope",
        company_contexts=[],
        non_obvious_fit_signals=["M-Pesa API experience directly relevant to fintech role"],
        role_specific_red_flags=[],
        role_specific_green_flags=["Quantified outcomes in every role", "Team leadership evidenced"],
        bias_flags=[],
        has_bias_flag=False,
        probe_points=[],
        confirm_strengths=["Payments API architecture at scale"],
    )


@pytest.fixture()
def sample_fit_analysis_low() -> FitAnalysis:
    """
    WHY: All dimension scores ≈ 0.3 — represents a poor-fit candidate.
    Used for testing the low-confidence / NO verdict path.

    HOW: composite_fit_score = 0.3*0.35 + 0.3*0.25 + 0.3*0.25 + 0.3*0.15
       = 0.105 + 0.075 + 0.075 + 0.045 = 0.30
    """
    return FitAnalysis(
        candidate_id="cand-002",
        technical_fit=0.3,
        technical_fit_rationale="Skills stated are mismatched with role requirements",
        experience_level_fit=0.3,
        experience_level_rationale="3 years experience insufficient for senior-level scope",
        learning_velocity_score=0.3,
        learning_velocity_rationale="No evidence of skill acquisition across roles",
        learning_velocity_evidence=LearningVelocityEvidence(
            new_skills_across_roles=[],
            self_directed_signals=[],
            promoted_into_unfamiliar=False,
            stagnation_flags=["Same technology stack across all 3 roles for 5 years"],
        ),
        builder_maintainer_score=0.3,
        career_shape="plateau",
        career_velocity="No progression observed over 5-year tenure",
        company_contexts=[],
        non_obvious_fit_signals=[],
        role_specific_red_flags=["No architectural decisions mentioned", "No ownership language"],
        role_specific_green_flags=[],
        bias_flags=[],
        has_bias_flag=False,
        probe_points=["What specific systems did you design end-to-end?"],
        confirm_strengths=[],
    )


# ── ScreeningInput fixture ────────────────────────────────────────────────────

@pytest.fixture()
def sample_screening_input() -> ScreeningInput:
    """
    WHY: A valid ScreeningInput for a senior SWE role. Reused across tests
    that need to construct ScreeningState or test the prefilter node.

    HOW: Includes realistic hard requirements so prefilter tests have
    something concrete to check against.
    """
    return ScreeningInput(
        candidate_id="cand-001",
        cv_text=(
            "Senior Software Engineer with 8 years of experience. "
            "Specialised in Python, Go, and distributed systems. "
            "Led teams at Safaricom and TechCorp Kenya. "
            "Built real-time payments infrastructure at scale. "
            "AWS certified. Open source contributor."
        ),
        job_description=(
            "We are looking for a Senior Software Engineer to join our fintech team. "
            "You will design and build high-throughput payment systems. "
            "Requirements: 5+ years backend engineering, Python proficiency, "
            "experience with distributed systems, AWS knowledge. "
            "Nice to have: Go, Kubernetes, prior fintech experience."
        ),
        role_seniority="senior",
        role_type="engineering",
        batch_id="batch-2026-08",
        hard_requirements=["python", "5 years"],
    )
