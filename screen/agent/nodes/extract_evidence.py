"""
WHY: Node 3 — the intelligence core. This is what makes SCREEN different from
every ATS and keyword-matcher. Rather than scoring a CV against a job description,
we extract structured evidence with quality tiers attached to each claim.

The distinction:
  - ATS: "Python mentioned 5 times → +5 points"
  - SCREEN: "Led Python backend serving 1M+ requests/day (Tier A, weight 1.0);
             'Proficient in Python' on skills list with no demonstrated projects (Tier C, weight 0.3)"

The evidence quality tier (A/B/C/D) is what makes the downstream confidence
calculation defensible. A candidate with 3 Tier A claims outscores one with
20 Tier C claims — as it should be.

HOW: Gemini Pro is used here (not Flash) because this requires nuanced reasoning
about claim credibility, contradiction detection, and silence pattern recognition.
The LLM output is validated against EvidenceBundle schema automatically.
"""

import re
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
from screen.schemas.evidence import SIGNAL_WEIGHTS, EvidenceBundle
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── System prompt ──────────────────────────────────────────────────────────────
EXTRACT_EVIDENCE_SYSTEM_PROMPT = """You are an expert technical recruiter with elite evidence extraction skills.

Your task is to analyse a candidate's structured profile against a job description
and extract an EvidenceBundle — structured evidence with quality tiers.

SIGNAL TIER DEFINITIONS (assign these to every Claim):
  A (weight: 1.0)  — VERIFIED: Publicly cross-referenceable (GitHub repo URL, company still operating,
                     award with public record, named product). The claim CAN be checked independently.
  B (weight: 0.7)  — STATED: Specific, plausible, internally consistent, no contradictions.
                     Not externally verifiable but well-evidenced (named project with team + outcome).
  C (weight: 0.3)  — VAGUE: Generic language. "Worked on projects", "collaborated with teams",
                     "responsible for", "helped with" — no specifics, no numbers, no outcomes.
  D (weight: -1.5) — CONTRADICTED: This claim conflicts with another claim in the CV
                     (impossible dates, scope that exceeds company size, expert claim with no application).

SIGNAL_WEIGHTS map (you MUST assign confidence_weight from this map based on tier):
  "A" -> 1.0
  "B" -> 0.7
  "C" -> 0.3
  "D" -> -1.5

WHAT TO EXTRACT:

CLAIMS: Every material claim about skills, experience, or achievements.
  - source_location: "Role at [Company], [dates], bullet N" — never verbatim CV text
  - is_verifiable_externally: True only if claim could be checked against public data

CONTRADICTIONS: Look for:
  - temporal: working at a company before it was founded.
    MANDATORY CHECK: If and ONLY IF the provided CV text itself explicitly states a
    founding year for a company (e.g. "founded in 2019", "established 2020",
    "DataSync was founded in 2021"), compare that year against the role start date.
    A role start date BEFORE the explicitly-stated founding year is a CRITICAL
    contradiction — set severity="critical" and has_critical_contradiction=True.
    CRITICAL RULE: DO NOT use your own training knowledge of when real companies were
    founded. If the CV does not explicitly state a founding year for a company, do NOT
    create a temporal contradiction for that company — you have no verified data.
    DO NOT flag as contradictions:
    * Cases where the role start date is AFTER the founding year (this is consistent).
    * Career transitions where consecutive roles overlap by ≤3 months.
    * Career pivots or non-linear paths (e.g. teacher → software engineer).
    * Gaps between roles — these are absence of data, not contradictions.

  - skill_level: If a claimed Expert/Proficient skill is absent from every role's work
    bullets, that is a skill_level contradiction. severity="critical", has_critical_contradiction=True.
    Also set has_unverifiable_high_stakes_claim=True if that skill is required by the JD.
    Apply this check to ALL claimed expertise including non-technical systems (ERP, CRM, WMS).
    NOTE: The pre-computed facts block will list any detected skill-level conflicts — treat
    those as confirmed contradictions and generate the appropriate EvidenceBundle entries.

  - scope_inflation: VP/Director title at 5-person startup managing stated 0 people
  - title_inflation: Senior title with only junior task descriptions
  - employment_gap: Unexplained gap between two stated dates

SILENCE FLAGS: What's ABSENT that SHOULD be present given role type and seniority?

  IMPORTANT: Deterministic pre-computed facts will appear in the input under
  "DETERMINISTIC PRE-COMPUTED FACTS". Treat these as absolute ground truth.
  Generate the appropriate silence flags or contradictions based on these facts:
  - Supervision >70% → generate a "high" severity supervision dominance silence flag
  - Production deployment NOT DETECTED → generate a "high" severity production silence flag
  - Skill-level conflicts listed → generate a "critical" contradiction for each one,
    set has_critical_contradiction=True
  - Domain keywords = 0 → generate a "high" severity domain mismatch silence flag

  - Senior engineers: no architectural decisions mentioned? Flag it.
  - People managers: no team size ever stated? Flag it.
  - Product roles: no product launches, no metrics? Flag it.
  - Quantified outcomes: for senior+ roles, absence of numbers IS a signal.

  OPERATIONS DOMAIN MISMATCH (operations/supply chain roles): The word "operations" covers
  fundamentally different domains. Read the job description to identify the SPECIFIC
  operations domain required (e.g. FMCG supply chain, warehousing, distribution, logistics,
  3PL, fill rate, on-time delivery). Then read the candidate's ENTIRE work history.
  If the candidate's experience is ENTIRELY in a DIFFERENT operations domain — for example:
    - Events/hospitality operations (F&B, conferences, venue setup) vs supply chain
    - Contact centre operations (SLA, AHT, agent management, IVR) vs supply chain
    - Financial/payment operations (settlement, reconciliation, treasury) vs supply chain
    - NGO/programme operations (M&E, donor reporting, beneficiary management) vs supply chain
  ...and they have NO evidence of supply chain, warehousing, distribution, 3PL, logistics,
  fill rate, inventory, or FMCG-specific skills anywhere — flag severity="high":
  "Expected: [domain-specific skills]. Candidate's entire history is in [actual domain].
   No supply chain or FMCG operations evidence found."
  This is a critical signal — generic "operations management" experience in an unrelated
  domain does not transfer to FMCG supply chain or distribution management.

BUILDER vs MAINTAINER:
  Builder signals: "built from scratch", "launched", "zero to one", "architected X",
                   "founded", quantified growth they drove, shipped products
  Maintainer signals: "managed", "maintained", "oversaw", "ensured", "supported",
                      "responsible for ongoing", no ownership language, no creation verbs

BOOLEAN FLAGS:
  has_critical_contradiction: True if ANY contradiction has severity="critical"
  has_unverifiable_high_stakes_claim: True if a B/C tier claim is both:
    (a) high-impact for this specific role verdict AND
    (b) cannot be checked against public data

DO NOT:
  - Penalise non-linear career paths
  - Flag employment gaps as negative without context
  - Use prestige heuristics (Tier A universities, brand-name employers)
  - Generate claims not in the profile
  - Include raw CV text in source_location (paraphrase only)

The job description context is used to determine what silences are meaningful
and what claims are high-stakes. Tailor your analysis to the specific role.

Output the complete EvidenceBundle. Be thorough — a thin evidence bundle is
less defensible than a complete one with many C-tier claims accurately classified."""

# ── LLM Setup ──────────────────────────────────────────────────────────────────
# WHY tier2: evidence extraction requires multi-hop reasoning about claim credibility,
# contradiction detection, and silence pattern recognition. Flash models miss
# subtle contradictions — this is where SCREEN differentiates from ATS.
_llm = build_llm("tier2")
_structured_llm = _llm.with_structured_output(EvidenceBundle)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_extract_evidence_llm(
    candidate_id: str,
    profile_summary: str,
    job_description: str,
    role_seniority: str,
    role_type: str,
    cv_text_raw: str = "",
    deterministic_facts: str = "",
) -> EvidenceBundle:
    """
    WHY: Isolated LLM call with retry. The profile_summary is a structured
    text rendering of CandidateProfile — the primary input for evidence extraction.
    cv_text_raw is passed as supplementary context ONLY for temporal contradiction
    detection (e.g., detecting that a candidate claims employment before a company
    was founded). The structured profile is the canonical source; raw text provides
    context that structured extraction may have missed in the summary/cover sections.

    HOW: We pass both the structured profile and the job description so the
    LLM can reason about role-appropriate silences and high-stakes claims.
    """
    raw_cv_section = (
        f"\n--- ORIGINAL CV TEXT (use for contradiction cross-referencing: "
        f"founding dates vs employment dates, skill proficiency levels claimed vs "
        f"actual work evidence in role descriptions) ---\n"
        f"{cv_text_raw}\n"
    ) if cv_text_raw else ""

    messages = [
        SystemMessage(content=EXTRACT_EVIDENCE_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"CANDIDATE ID: {candidate_id}\n"
                f"ROLE SENIORITY: {role_seniority}\n"
                f"ROLE TYPE: {role_type}\n\n"
                f"--- CANDIDATE PROFILE (structured, anonymised) ---\n"
                f"{profile_summary}\n\n"
                f"--- JOB DESCRIPTION ---\n"
                f"{job_description}\n"
                f"{raw_cv_section}\n"
                f"{deterministic_facts}\n"
                f"Extract the complete EvidenceBundle for this candidate."
            )
        ),
    ]
    result: EvidenceBundle = _structured_llm.invoke(messages)
    return result


def _render_profile_for_llm(candidate_profile: CandidateProfile) -> str:
    """
    WHY: We pass a structured text rendering of CandidateProfile to the LLM
    rather than raw JSON. This is more readable for the model and ensures we
    never accidentally include raw CV text (which was already stripped in Node 1).

    HOW: Produces a structured plain-text summary. Company names remain because
    they are needed for contradiction detection (company founding dates, size).
    No candidate name appears — only "CANDIDATE".
    """
    lines = [
        f"CANDIDATE (anonymised) — {candidate_profile.total_years_experience or 'unknown'} years experience",
        f"Career start: {candidate_profile.career_start_year or 'unknown'}",
        f"Non-linear path: {candidate_profile.has_non_linear_path}",
        f"Highest education: {candidate_profile.highest_education_level}",
        "",
        "WORK HISTORY (reverse chronological):",
    ]

    for role in candidate_profile.roles:
        lines.append(
            f"  • {role.title} at {role.company} "
            f"({role.start_date or '?'} — {role.end_date or 'Present'}, "
            f"{role.duration_months or '?'} months)"
        )
        lines.append(f"    Quantified outcomes: {role.is_quantified}")
        if role.team_size_mentioned is not None:
            lines.append(f"    Team size mentioned: {role.team_size_mentioned}")
        for achievement in role.achievements:
            lines.append(f"    - {achievement}")

    if candidate_profile.education:
        lines.append("")
        lines.append("EDUCATION:")
        for edu in candidate_profile.education:
            lines.append(
                f"  • {edu.degree or 'Degree not stated'} in {edu.field_of_study or '?'} "
                f"at {edu.institution} "
                f"({'traditional' if edu.is_traditional else 'non-traditional'})"
            )

    if candidate_profile.skills_stated:
        lines.append("")
        lines.append(f"STATED SKILLS: {', '.join(candidate_profile.skills_stated)}")

    if candidate_profile.employment_gaps:
        lines.append("")
        lines.append("EMPLOYMENT GAPS:")
        for gap in candidate_profile.employment_gaps:
            explanation = "explained" if gap.explanation_provided else "NO EXPLANATION PROVIDED"
            lines.append(
                f"  • {gap.gap_start} to {gap.gap_end} "
                f"({gap.duration_months or '?'} months) — {explanation}"
            )

    return "\n".join(lines)


def _compute_deterministic_signals(
    candidate_profile: CandidateProfile,
    screening_input,
) -> dict:
    """
    WHY: Signals that LLMs compute inconsistently (30% miss rate) are computed
    deterministically in Python here. The results are injected as hard facts into
    the LLM prompt so the model only reasons about them, never detects them.

    Computes:
    - supervision_pct: fraction of role bullets using subordinate language
    - has_production_deployment: bool | None (None if not ML/DS role)
    - skill_conflicts: list of Expert/Proficient skills absent from ALL role bullets
    - domain_keyword_count: # of supply-chain keywords in cv_text (operations roles only)
    """
    # ── Supervision language ──────────────────────────────────────────────────
    SUPERVISION_PATTERNS = [
        "assisted", "under supervision", "as directed", "participated in",
        "supported the", "contributed to", "helped with", "shadowed",
        "worked under", "reported to", "as instructed",
    ]
    all_bullets = [
        ach.lower()
        for role in candidate_profile.roles
        for ach in role.achievements
    ]
    if all_bullets:
        subordinate_count = sum(
            1 for b in all_bullets
            if any(p in b for p in SUPERVISION_PATTERNS)
        )
        supervision_pct = subordinate_count / len(all_bullets)
    else:
        supervision_pct = 0.0

    # ── Production deployment (ML/DS roles only) ──────────────────────────────
    role_type_lower = screening_input.role_type.lower()
    is_ml_role = any(
        kw in role_type_lower
        for kw in ["data", "ml", "machine learning", "data science", "analytics", "ai"]
    )
    if is_ml_role:
        PRODUCTION_KEYWORDS = [
            "deployed", "in production", "model serving", "api endpoint",
            "real-time inference", "batch prediction", "model monitoring",
            "live system", "production system", "serving pipeline",
        ]
        all_role_text = " ".join(
            ach.lower()
            for role in candidate_profile.roles
            for ach in role.achievements
        )
        has_production_deployment = any(kw in all_role_text for kw in PRODUCTION_KEYWORDS)
    else:
        has_production_deployment = None  # Not applicable

    # ── Role type flags ──────────────────────────────────────────────────────
    # WHY: Computed early so both skill-conflict and domain-keyword blocks can use it.
    is_ops_role = "operations" in role_type_lower or "supply" in role_type_lower

    # ── Skill-level conflicts ────────────────────────────────────────────────
    # WHY: Skill conflict detection is SKIPPED for operations/supply-chain roles.
    # Operations candidates write achievement bullets in outcome language:
    #   "Reduced shrinkage by 23%", "Improved fill rate to 98%"
    # They do NOT repeat tool names in every bullet even when genuinely using them.
    # Checking "Expert: SAP, WMS, Odoo" against outcome bullets ALWAYS produces
    # false conflicts — causing legitimate YES/STRONG_YES ops candidates to ESCALATE.
    # Skill-level conflict detection is meaningful for tech roles (SWE, DS/ML) where
    # engineers name the tools they use in every implementation bullet.
    all_achievements_text = " ".join(
        ach.lower()
        for role in candidate_profile.roles
        for ach in role.achievements
    )
    skill_conflicts: list[str] = []
    if not is_ops_role:
        PROFICIENCY_MARKERS = ["expert", "proficient", "advanced", "expert:", "proficient:"]
        for skill in candidate_profile.skills_stated:
            skill_lower = skill.lower()
            is_high_proficiency = any(m in skill_lower for m in PROFICIENCY_MARKERS)
            if is_high_proficiency:
                # Extract the skill name (strip proficiency label and parentheses)
                skill_name = re.sub(
                    r"\b(expert|proficient|advanced|intermediate|beginner)\b[:\s]*",
                    "",
                    skill_lower,
                    flags=re.IGNORECASE,
                ).strip(" :()")
                # WHY: Use regex word extraction, not .split() — split() leaves commas
                # attached to tokens ("kubernetes," != "kubernetes"), causing false negatives
                # when skills_stated contains comma-separated lists like
                # "Expert: Kubernetes, Terraform, ML pipelines"
                skill_tokens = re.findall(r'\b[a-z][a-z0-9\-\.]{2,}\b', skill_name)
                # Filter generic English words that aren't skill names
                _GENERIC_TOKENS = {"and", "the", "for", "with", "use", "all", "not", "any",
                                   "python", "java", "sql"}  # common languages often implied
                skill_tokens = [t for t in skill_tokens if t not in _GENERIC_TOKENS]
                # WHY: Use missing-count not any/all — a grouped skill like
                # "Expert: Python, Kubernetes, Terraform" should still be flagged
                # if 2+ specific tools are absent, even if "python" is found.
                missing_tokens = [t for t in skill_tokens if t not in all_achievements_text]
                # WHY: Use a missing ratio (not absolute count) — a Proficient group
                # where 50% of tools aren't mentioned is fine; one where 80%+ of Expert
                # tools are absent is a real conflict. Threshold: ≥70% missing = conflict.
                missing_ratio = len(missing_tokens) / len(skill_tokens) if skill_tokens else 0.0
                found_in_work = missing_ratio < 0.70
                if not found_in_work:
                    skill_conflicts.append(skill)

    # ── Operations domain keywords ───────────────────────────────────────────
    if is_ops_role:
        SUPPLY_CHAIN_KEYWORDS = [
            "warehouse", "distribution", "logistics", "3pl", "supply chain",
            "inventory", "fill rate", "on-time delivery", "fmcg", "distributor",
            "dispatch", "freight", "last mile", "route planning", "shrinkage",
            "stock", "inbound", "outbound", "fulfilment", "procurement",
        ]
        cv_lower = screening_input.cv_text.lower()
        domain_keyword_count = sum(1 for kw in SUPPLY_CHAIN_KEYWORDS if kw in cv_lower)
    else:
        domain_keyword_count = None

    return {
        "supervision_pct": supervision_pct,
        "supervision_bullet_count": len(all_bullets),
        "has_production_deployment": has_production_deployment,
        "skill_conflicts": skill_conflicts,
        "domain_keyword_count": domain_keyword_count,
        "is_ml_role": is_ml_role,
        "is_ops_role": is_ops_role,
    }


def _render_deterministic_facts(signals: dict) -> str:
    """
    WHY: Formats pre-computed signals as a structured FACTS block for the LLM.
    The LLM must treat these as ground truth — never re-derive them.
    This eliminates the 30% miss rate from LLM-based detection.
    """
    lines = [
        "--- DETERMINISTIC PRE-COMPUTED FACTS (ground truth — do NOT re-derive) ---"
    ]

    # Supervision language
    pct = signals["supervision_pct"]
    n = signals["supervision_bullet_count"]
    pct_str = f"{pct:.0%}"
    flag = " ← FLAG: >70% threshold exceeded" if pct > 0.70 else ""
    lines.append(f"Supervision language: {pct_str} of {n} role bullets use subordinate language{flag}")

    # Production deployment
    if signals["has_production_deployment"] is not None:
        if signals["has_production_deployment"]:
            lines.append("Production deployment: DETECTED in role work bullets")
        else:
            lines.append(
                "Production deployment: NOT DETECTED in any role work bullet "
                "← FLAG: candidate has never deployed to production (critical for senior ML/DS role)"
            )

    # Skill conflicts
    conflicts = signals["skill_conflicts"]
    if conflicts:
        lines.append(
            f"Skill-level conflicts: {len(conflicts)} Expert/Proficient skill(s) appear in "
            f"skills section but are ABSENT from ALL role work bullets:"
        )
        for s in conflicts:
            lines.append(f"  • {s}")
        lines.append(
            "  → Each of these MUST be flagged as a skill_level contradiction "
            "(severity=critical, has_critical_contradiction=True)"
        )
    else:
        lines.append("Skill-level conflicts: None detected")

    # Domain keywords (operations roles)
    if signals["domain_keyword_count"] is not None:
        n_kw = signals["domain_keyword_count"]
        if n_kw == 0:
            lines.append(
                "Supply-chain/FMCG domain keywords: 0 found in entire CV "
                "← FLAG: candidate has NO supply-chain vocabulary anywhere in their history"
            )
        else:
            lines.append(f"Supply-chain/FMCG domain keywords: {n_kw} found in CV")

    lines.append("--- END PRE-COMPUTED FACTS ---")
    return "\n".join(lines)


def extract_evidence_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: This node produces the EvidenceBundle that drives all downstream scoring.
    The quality of this extraction directly determines the quality of the final verdict.

    HOW:
    1. Validate state has candidate_profile and screening_input
    2. Render profile to structured text (maintains data boundary — no raw CV)
    3. Call Gemini Pro with structured output bound to EvidenceBundle
    4. Log counts and key signals, build trajectory entry
    """
    node_name = "extract_evidence"
    start_ms = time.time() * 1000

    candidate_profile = state.get("candidate_profile")
    if candidate_profile is None:
        raise StateTransitionError(node_name, "candidate_profile")

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id

    logger.info(
        "extract_evidence started",
        node=node_name,
        candidate_id=candidate_id,
    )

    profile_text = _render_profile_for_llm(candidate_profile)

    # Compute deterministic signals before LLM call
    det_signals = _compute_deterministic_signals(candidate_profile, screening_input)
    det_facts_text = _render_deterministic_facts(det_signals)

    try:
        evidence_bundle = _call_extract_evidence_llm(
            candidate_id=candidate_id,
            profile_summary=profile_text,
            job_description=screening_input.job_description,
            role_seniority=screening_input.role_seniority,
            role_type=screening_input.role_type,
            cv_text_raw=screening_input.cv_text,
            deterministic_facts=det_facts_text,
        )
    except Exception as exc:
        raise LLMCallError(node_name, str(exc)) from exc

    # Estimate cost: profile text + job description as proxy
    prompt_token_estimate = (len(profile_text) + len(screening_input.job_description)) // 4
    completion_token_estimate = len(evidence_bundle.claims) * 80 + 200
    cost_usd = estimate_token_cost(
        prompt_tokens=prompt_token_estimate,
        completion_tokens=completion_token_estimate,
        model_tier=2,
    )

    num_claims = len(evidence_bundle.claims)
    num_contradictions = len(evidence_bundle.contradictions)
    num_silence_flags = len(evidence_bundle.silence_flags)
    has_critical = evidence_bundle.has_critical_contradiction

    # Collect evidence keys for trajectory
    evidence_keys = (
        [f"claim:{i}" for i in range(num_claims)]
        + [f"contradiction:{i}" for i in range(num_contradictions)]
        + [f"silence:{i}" for i in range(num_silence_flags)]
    )

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Extracted {num_claims} evidence claims "
            f"({sum(1 for c in evidence_bundle.claims if c.tier == 'A')} Tier A, "
            f"{sum(1 for c in evidence_bundle.claims if c.tier == 'B')} Tier B, "
            f"{sum(1 for c in evidence_bundle.claims if c.tier == 'C')} Tier C, "
            f"{sum(1 for c in evidence_bundle.claims if c.tier == 'D')} Tier D). "
            f"Found {num_contradictions} contradiction(s) "
            f"(critical: {has_critical}). "
            f"{num_silence_flags} silence flag(s) detected. "
            f"Builder/maintainer verdict: {evidence_bundle.builder_maintainer_verdict}."
        ),
        output_summary=(
            f"{num_claims} claims | {num_contradictions} contradictions "
            f"(critical: {has_critical}) | {num_silence_flags} silence flags | "
            f"verdict: {evidence_bundle.builder_maintainer_verdict}"
        ),
        evidence_keys=evidence_keys[:20],  # Cap at 20 keys for log readability
        model_used=get_active_model("tier2"),
        cost_usd=cost_usd,
    )

    logger.info(
        "extract_evidence complete",
        node=node_name,
        candidate_id=candidate_id,
        num_claims=num_claims,
        num_contradictions=num_contradictions,
        has_critical_contradiction=has_critical,
        builder_maintainer=evidence_bundle.builder_maintainer_verdict,
        duration_ms=trajectory_entry.duration_ms,
        cost_usd=cost_usd,
    )

    return {
        "evidence_bundle": evidence_bundle,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
