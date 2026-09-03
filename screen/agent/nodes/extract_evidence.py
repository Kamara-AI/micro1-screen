"""
WHY: Node 3 — the intelligence core. This is what makes SCREEN different from
every ATS and keyword-matcher. Rather than scoring a CV against a job description,
we extract structured evidence with quality tiers attached to each claim.

The distinction:
  - ATS: "Python mentioned 5 times → +5 points"
  - SCREEN: "Led Python backend serving 1M+ requests/day (Tier A, weight 1.0);
             'Proficient in Python' on skills list with no demonstrated projects (Tier C, weight 0.1)"

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
from screen.core.domain_calibration import get_calibration
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

  B (weight: 0.7)  — STATED: A specific claim that names AT LEAST TWO of the following:
                     (1) the employer / client / product where the work happened
                     (2) a specific tool, platform, or technology actually used to do the work
                     (3) a quantified outcome with a clear before→after or against a benchmark
                         ("from 8% to 23%", "against a 280% target", not just "by 45%")
                     (4) a named collaborator, team size, or reporting structure

                     TIER B EXAMPLES (2+ named elements):
                       "Managed KES 5M Google Ads budget at Safaricom, achieving 340% ROAS" ✓ (tool + metric)
                       "Led 8-person team to migrate 3 microservices from monolith to Kubernetes" ✓ (tool + team)
                       "Built HubSpot email sequences that moved MQL→SQL rate from 8% to 23%" ✓ (tool + baseline→result)

                     NOT TIER B — assign Tier C instead:
                       "Grew organic traffic by 45%" ✗ — one percentage, no named tool, no baseline, no client
                       "Increased revenue by 30%" ✗ — percentage only, no context
                       "Managed social media accounts" ✗ — no metrics, no named platform specifics
                       "Improved team efficiency" ✗ — no tool, no metric, no scope

  C (weight: 0.1)  — VAGUE: Generic or single-element claims. No named tools, no named employers in context,
                     no baselines for metrics. Includes: outcome-only language ("drove growth",
                     "improved performance", "increased by X%" with no named tool or client context),
                     responsibility descriptions without specifics ("managed campaigns", "oversaw strategy"),
                     generic collaboration ("worked with cross-functional teams").
                     A single number without context (who, what tool, what baseline) is STILL Tier C.

  D (weight: -1.5) — CONTRADICTED: This claim conflicts with another claim in the CV
                     (impossible dates, scope that exceeds company size, expert claim with no application).

SIGNAL_WEIGHTS map (you MUST assign confidence_weight from this map based on tier):
  "A" -> 1.0
  "B" -> 0.7
  "C" -> 0.1
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

DOMAIN CALIBRATION (read before extracting evidence):
  The DETERMINISTIC PRE-COMPUTED FACTS block includes domain-calibration signals:
    - Detected domain: the auto-classified hiring domain for this JD
    - Domain keywords found: count of domain-specific vocabulary in the entire CV
    - Hard anchor signals found: count of specific phrases proving real domain experience
    - Tier-C trap phrases found: count of unverifiable generic claims common in this domain

  Use these facts as follows:
    1. If hard_anchor_count = 0 AND domain_keyword_count < minimum threshold:
       generate a domain mismatch silence flag at severity="high":
       "Expected: [domain-specific vocabulary]. Found 0 hard anchors and fewer than
       [threshold] domain keywords. Candidate may not have genuine [domain] experience."
    2. If tier_c_trap_count > 3: add a yellow-flag silence flag at severity="low":
       "High proportion of generic/unverifiable claim language for [domain]. Recommend
       probing for specific metrics and outcomes in interview."
       Do NOT automatically penalise — let the tier assignments carry the weight.

  DOMAIN-SPECIFIC SILENCE PATTERNS (generate these when the detected domain matches):
    Software Engineering / DevOps / Cybersecurity:
      → No architecture decisions for a senior candidate? Flag it.
      → No production deployment evidence for a senior role? Flag it.
    Data Science / ML / AI:
      → No model deployed to production for a senior role? Flag it.
      → No business impact metric for any model or analysis? Flag it.
      → No experimental methodology (A/B test, holdout, validation)? Flag it.
    Digital Marketing:
      → No conversion rate, ROAS, CAC, or CPC metric anywhere? Flag it.
      → No specific channel ownership with budget control? Flag it.
    Sales / Business Development:
      → No quota attainment figure? Flag it.
      → No deal size, ARR closed, or pipeline value? Flag it.
    Finance / Accounting / FP&A:
      → No P&L ownership, budget size, or financial model? Flag it.
      → No specific regulation, filing, or instrument? Flag it.
    Product Management:
      → No product shipped with real user metrics? Flag it.
      → No roadmap ownership or launch described? Flag it.
    HR / People Operations:
      → No retention rate, time-to-hire, or headcount managed? Flag it.
    Customer Success:
      → No NPS, CSAT, churn rate, or ARR retained metric? Flag it.
    Legal / Compliance:
      → No specific regulation, jurisdiction, or transaction type? Flag it.
    Design (UX / UI / Brand):
      → No portfolio link or named shipped product for a senior role? Flag it.
    Project / Programme Management:
      → No budget managed or on-time delivery rate? Flag it.
    Cybersecurity:
      → No specific framework (SOC 2, ISO 27001, NIST) implemented? Flag it.

  DOMAIN MISMATCH (ALL DOMAINS): A candidate whose ENTIRE career is in a fundamentally
  different domain should receive a domain mismatch silence flag at severity="high".
  The hard_cap_alien_domains list (in the domain calibration block) specifies which
  backgrounds are non-transferable for the detected domain.
  Operations mismatch: Events/hospitality, contact centre, NGO programme ops,
  financial/payment ops, and banking branch ops are NOT transferable to FMCG supply
  chain management.

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

    Now domain-calibration-aware: all domain-specific checks (production deployment,
    skill conflict, domain keywords) are driven by the domain registry rather than
    hardcoded role-type strings. This is what enables accurate screening across
    20+ domains without per-domain code changes.

    Computes:
    - supervision_pct: fraction of role bullets using subordinate language
    - has_production_deployment: bool | None (None if domain has no production check)
    - skill_conflicts: list of Expert/Proficient skills absent from ALL role bullets
    - domain_keyword_count: # of calibrated domain keywords found in full CV text
    - hard_anchor_count: # of domain-specific hard anchor phrases found in role bullets
    - tier_c_trap_count: # of domain-specific Tier C trap phrases found in role bullets
    - detected_domain: canonical domain name from calibration registry

    WHY backwards-compat keys are preserved:
    - is_ml_role and is_ops_role are derived from the detected domain name so that
      any downstream code still referencing these keys continues to work without changes.
    """
    # ── Domain calibration ────────────────────────────────────────────────────
    # WHY: role_description (free-form title) is preferred over broad role_type for
    # domain detection. This allows fine-grained calibration (e.g. "Senior Digital
    # Marketing Manager" → Digital Marketing) without changing the broad role_type
    # enum used by other parts of the pipeline.
    domain_str = screening_input.role_description or screening_input.role_type
    calibration = get_calibration(domain_str)

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

    # ── All role bullets as single text (used by multiple checks below) ───────
    all_achievements_text = " ".join(all_bullets)

    # ── Production deployment (domain-calibrated) ─────────────────────────────
    # WHY: Previously hardcoded for ML/DS only. Now any domain with
    # production_check_enabled=True (engineering, devops, cybersecurity, design,
    # product management) triggers this check. Domains like Marketing, Sales, HR
    # have production_check_enabled=False — the concept does not apply to them.
    if calibration.production_check_enabled:
        has_production_deployment = any(
            kw in all_achievements_text
            for kw in calibration.production_check_keywords
        )
    else:
        has_production_deployment = None  # Not applicable for this domain

    # ── Skill-level conflicts (domain-calibrated) ─────────────────────────────
    # WHY: Skill conflict detection is enabled only for tech domains where engineers
    # name specific tools in every role bullet (Python, Kubernetes, TensorFlow).
    # For outcome-language domains (Sales, Marketing, HR, Operations, Finance) this
    # check produces systematic false positives — e.g. "Expert: Salesforce" fails
    # conflict check because a sales rep writes "closed $2M ARR" not "used Salesforce
    # to close $2M ARR". calibration.skill_conflict_check_enabled handles this.
    skill_conflicts: list[str] = []
    if calibration.skill_conflict_check_enabled:
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

    # ── Domain keyword count (domain-calibrated, applied to all domains) ──────
    # WHY: Previously only computed for operations/supply-chain roles. Now computed
    # for every domain using calibrated keyword lists. This enables domain mismatch
    # detection across all 20 domains, not just operations.
    cv_lower = screening_input.cv_text.lower()
    domain_keyword_count = sum(
        1 for kw in calibration.domain_keywords if kw in cv_lower
    )

    # ── Hard anchor count ────────────────────────────────────────────────────
    # WHY: Hard anchors are domain-specific phrases that indicate Tier A or B evidence.
    # A candidate with zero hard anchors in a domain is highly suspicious — these are
    # the phrases that real practitioners use naturally. Counting them in role bullets
    # (not the full CV) prevents keyword-stuffing in skills/summary sections.
    hard_anchor_count = sum(
        1 for pattern in calibration.hard_anchor_patterns
        if pattern in all_achievements_text
    )

    # ── Tier C trap count ────────────────────────────────────────────────────
    # WHY: These are the generic phrases that look professional but carry no signal.
    # A high count (>3) is a yellow flag — the candidate writes well but says nothing.
    # Counted in full CV text (not just bullets) because they often appear in summaries.
    tier_c_trap_count = sum(
        1 for trap in calibration.tier_c_traps if trap in cv_lower
    )

    # ── Backwards-compatible role type flags ─────────────────────────────────
    # WHY: Preserving these keys so any downstream code referencing is_ml_role or
    # is_ops_role continues to work. Derived from detected domain name.
    is_ml_role = "data science" in calibration.name.lower() or "ml" in calibration.name.lower()
    is_ops_role = "operations" in calibration.name.lower() or "supply chain" in calibration.name.lower()

    return {
        "supervision_pct": supervision_pct,
        "supervision_bullet_count": len(all_bullets),
        "has_production_deployment": has_production_deployment,
        "skill_conflicts": skill_conflicts,
        "domain_keyword_count": domain_keyword_count,
        "hard_anchor_count": hard_anchor_count,
        "tier_c_trap_count": tier_c_trap_count,
        "detected_domain": calibration.name,
        "minimum_domain_keyword_count": calibration.minimum_domain_keyword_count,
        "hard_cap_alien_domains": calibration.hard_cap_alien_domains,
        "tier_c_traps_list": calibration.tier_c_traps,
        # Backwards-compat keys — derived from domain calibration
        "is_ml_role": is_ml_role,
        "is_ops_role": is_ops_role,
    }


def _render_deterministic_facts(signals: dict) -> str:
    """
    WHY: Formats pre-computed signals as a structured FACTS block for the LLM.
    The LLM must treat these as ground truth — never re-derive them.
    This eliminates the 30% miss rate from LLM-based detection.

    Now includes domain calibration signals (detected_domain, hard_anchor_count,
    tier_c_trap_count) and the hard_cap_alien_domains list for domain mismatch
    detection across all 20 registered domains.
    """
    lines = [
        "--- DETERMINISTIC PRE-COMPUTED FACTS (ground truth — do NOT re-derive) ---"
    ]

    # ── Domain calibration ────────────────────────────────────────────────────
    detected_domain = signals.get("detected_domain", "General / Unknown")
    min_kw = signals.get("minimum_domain_keyword_count", 2)
    lines.append(f"Detected domain: {detected_domain}")

    # ── Supervision language ──────────────────────────────────────────────────
    pct = signals["supervision_pct"]
    n = signals["supervision_bullet_count"]
    pct_str = f"{pct:.0%}"
    flag = " ← FLAG: >70% threshold exceeded" if pct > 0.70 else ""
    lines.append(f"Supervision language: {pct_str} of {n} role bullets use subordinate language{flag}")

    # ── Production deployment ─────────────────────────────────────────────────
    if signals["has_production_deployment"] is not None:
        if signals["has_production_deployment"]:
            lines.append("Production deployment: DETECTED in role work bullets")
        else:
            lines.append(
                "Production deployment: NOT DETECTED in any role work bullet "
                f"← FLAG: candidate has never deployed to production (critical for senior {detected_domain} role)"
            )

    # ── Skill conflicts ───────────────────────────────────────────────────────
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

    # ── Domain keywords ───────────────────────────────────────────────────────
    n_kw = signals["domain_keyword_count"]
    if n_kw == 0:
        lines.append(
            f"{detected_domain} domain keywords: 0 found in entire CV "
            f"← FLAG: candidate has NO {detected_domain} vocabulary anywhere in their history"
        )
    elif n_kw < min_kw:
        lines.append(
            f"{detected_domain} domain keywords: {n_kw} found (minimum threshold: {min_kw}) "
            f"← LOW: candidate has limited {detected_domain} vocabulary"
        )
    else:
        lines.append(f"{detected_domain} domain keywords: {n_kw} found in CV")

    # ── Hard anchor count ─────────────────────────────────────────────────────
    hard_anchor_count = signals.get("hard_anchor_count", 0)
    if hard_anchor_count == 0:
        lines.append(
            f"Hard anchor signals found: 0 "
            f"← FLAG: no specific {detected_domain} practitioner phrases detected in role bullets"
        )
    else:
        lines.append(f"Hard anchor signals found: {hard_anchor_count}")

    # ── Tier C trap count ─────────────────────────────────────────────────────
    tier_c_trap_count = signals.get("tier_c_trap_count", 0)
    if tier_c_trap_count > 3:
        lines.append(
            f"Tier-C trap phrases found: {tier_c_trap_count} "
            f"← YELLOW FLAG: high proportion of generic/unverifiable language for {detected_domain}"
        )
    else:
        lines.append(f"Tier-C trap phrases found: {tier_c_trap_count}")

    # ── Hard cap alien domains ─────────────────────────────────────────────────
    alien_domains = signals.get("hard_cap_alien_domains", [])
    if alien_domains:
        lines.append(f"Non-transferable backgrounds for {detected_domain} (hard-cap triggers):")
        for ad in alien_domains:
            lines.append(f"  • {ad}")

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
