# SCREEN — Technical Design Document

**Structured Candidate Reasoning and Evaluation Engine**
Version 0.1.0 | micro1 Agentic Workflows Hackathon | 2026-08-30

---

## 1. System Overview

### What SCREEN Is

SCREEN is a production-grade AI pre-screening agent that reasons the way a senior recruiter thinks — not the way most AI screeners are built. It is not a keyword matcher, a score normaliser, or a GPT wrapper that summarises CVs. It is an evidence-extraction and decision-making pipeline that produces structured, auditable, calibrated verdicts on job candidates.

The name is intentional: **Structured Candidate Reasoning and Evaluation Engine**. Every word matters. Structured means Pydantic-validated output at every stage. Reasoning means evidence is cited, not implied. Evaluation means multi-dimensional, not binary. Engine means the logic is deterministic and inspectable.

### The Problem It Solves

Modern hiring has two failure modes:

**Failure mode 1 — ATS keyword matching.** A candidate who built Stripe's fraud detection engine but calls it a "risk scoring system" fails the keyword filter. A candidate who lists every required keyword but has never shipped anything real passes. The system optimises for vocabulary alignment, not capability.

**Failure mode 2 — GPT wrapper summarisation.** An LLM reads a CV and generates a paragraph like "This candidate seems well-suited for the role given their strong Python background and fintech experience." This is not a decision. It is a paraphrase. It cannot be audited, calibrated, or improved.

SCREEN solves both. It extracts structured evidence, weights claims by verifiability, detects contradictions and suspicious absences, applies a mathematical confidence formula, routes edge cases to human review with a structured brief, and logs every step in an append-only audit trail.

### Why It Matters

Automated employment decisions are high-stakes in two directions: they affect candidates' livelihoods, and they affect companies' ability to hire the right people. A system that cannot explain its verdicts is not safe to deploy at scale. SCREEN makes explainability a first-class requirement, not a retrospective add-on.

At the micro1 hackathon level: SCREEN demonstrates that agentic AI systems can go beyond "impressive demo" to "production-grade reasoning" — with evidence tiers, calibrated uncertainty, bias detection, human escalation, and audit trails. That is the bar we built to.

---

## 2. Architecture Diagram

```
                        ┌─────────────────────────────────────────────┐
                        │              ScreeningInput                 │
                        │  (candidate_id, cv_text, job_description,  │
                        │   role_seniority, role_type, batch_id,     │
                        │   hard_requirements)                        │
                        └──────────────────┬──────────────────────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                         [1]  │    parse_candidate     │  Gemini 1.5 Flash
                              │  Extract + anonymise   │  ~$0.0005/candidate
                              └────────────┬───────────┘
                                           │ CandidateProfile
                                           ▼
                              ┌────────────────────────┐
                         [2]  │   tier1_prefilter      │  Deterministic (no LLM)
                              │  Hard requirements     │  <1ms
                              └────────────┬───────────┘
                                           │
                         ┌─────────────────┴──────────────────┐
                         │ hard_rejected?                       │
                    YES  │                               NO    │
                         ▼                                     ▼
                   ┌──────────┐              ┌────────────────────────┐
                   │   END    │         [3]  │   extract_evidence     │  Gemini 1.5 Pro
                   │ STRONG_NO│              │  Claims, contradictions │  ~$0.003/candidate
                   └──────────┘              │  silence flags,         │
                                             │  builder/maintainer     │
                                             └────────────┬───────────┘
                                                          │ EvidenceBundle
                                                          ▼
                                             ┌────────────────────────┐
                                        [4]  │     analyze_fit        │  Gemini 1.5 Pro
                                             │  4-dimension scoring,  │  ~$0.003/candidate
                                             │  career shape,         │
                                             │  company context       │
                                             └────────────┬───────────┘
                                                          │ FitAnalysis
                                                          ▼
                                             ┌────────────────────────┐
                                        [5]  │    detect_bias         │  Gemini 1.5 Pro
                                             │  Demographic proxies,  │  ~$0.002/candidate
                                             │  prestige bias,        │
                                             │  structural bias audit │
                                             └────────────┬───────────┘
                                                          │ bias_flags → FitAnalysis
                                                          ▼
                                             ┌────────────────────────┐
                                        [6]  │    make_decision       │  Deterministic
                                             │  Confidence formula,   │  (reads settings)
                                             │  verdict routing       │
                                             └────────────┬───────────┘
                                                          │
                                      ┌───────────────────┴──────────────────┐
                                      │ should_escalate?                      │
                                 YES  │                                  NO   │
                                      ▼                                       ▼
                         ┌─────────────────────┐              ┌──────────────────────┐
                    [7]  │  build_human_brief  │         [8]  │  candidate_feedback  │
                         │  Structured brief   │              │  Strength + gap,     │
                         │  for reviewer       │              │  all verdicts        │
                         └──────────┬──────────┘              └──────────┬───────────┘
                                    │                                     │
                                    └──────────────┬──────────────────────┘
                                                   ▼
                                      ┌────────────────────────┐
                                 [9]  │   comparative_rank     │  Gemini 1.5 Flash
                                      │  Cohort ranking        │  batch mode only
                                      │  (batch_id required)   │
                                      └────────────┬───────────┘
                                                   │
                                                   ▼
                                      ┌────────────────────────┐
                                [10]  │    log_trajectory      │  Deterministic
                                      │  Append-only audit     │  ~0ms
                                      │  trail, EAT timestamp  │
                                      └────────────┬───────────┘
                                                   │
                                                   ▼
                                      ┌────────────────────────┐
                                      │        Decision        │
                                      │  verdict, confidence%, │
                                      │  primary_evidence,     │
                                      │  human_brief (or None),│
                                      │  candidate_feedback,   │
                                      │  trajectory, cost_usd  │
                                      └────────────────────────┘
```

**LangGraph state flow:** `ScreeningState` (TypedDict) is the shared state. Each node reads from it and writes only the fields it owns. The `trajectory` field uses `operator.add` as a LangGraph reducer — append-only, never overwritten. `total_cost_usd` uses the same mechanism to accumulate across LLM calls.

---

## 3. The Signal Tier System

The signal tier system is the core insight that separates SCREEN from every other AI screener. All claims on a CV are not equal. A verified, publicly cross-referenceable achievement ("promoted in 22 months at Stripe — checkable via LinkedIn, media, former colleagues") is worth more than a vague assertion ("worked on impactful projects"). The tier system makes this weighting explicit, deterministic, and auditable.

### Tier Definitions

| Tier | Name | Weight | Definition | Example |
|------|------|--------|------------|---------|
| A | Verified | +1.0 | Public, cross-referenceable. The claim can be confirmed through LinkedIn, GitHub, Companies House, Credly, media coverage, etc. | "2,400 GitHub stars on open-source library" / "Promoted to Staff Eng at Stripe in 22 months" |
| B | Stated | +0.7 | Specific, plausible, internally consistent, and not contradicted elsewhere. Cannot be easily verified externally but is coherent. | "Reduced API p99 latency from 280ms to 47ms" / "Led a 4-person squad" |
| C | Vague | +0.3 | Generic, unspecific, or common-boilerplate language that communicates little. | "Worked on challenging projects" / "Collaborated with cross-functional teams" |
| D | Contradicted | -1.5 | Directly or logically conflicts with another claim in the same CV. More damaging than a positive claim can offset. | Start date implies working at two full-time roles simultaneously / "VP Engineering" at a company founded 3 months after stated join date |

### Why the Asymmetry

The penalty for a Tier D claim (-1.5) is 1.5x the maximum positive weight (+1.0). This is deliberate. A single critical contradiction should not be neutralisable by accumulating soft positive claims. If a candidate's dates show they were "Director of Engineering" at a company that did not yet exist, adding five Tier C phrases about "strong leadership skills" should not raise their confidence score to YES. The asymmetry enforces this.

### The Silence Flag System

Beyond claim quality, SCREEN reads absences. A senior engineer with no architectural decisions mentioned is a signal. A people manager who never once states a team size is a signal. The `SilenceFlag` schema captures expected signals that are missing, with a severity rating:

- **High severity** (−0.30 penalty): This signal should definitively be present for this role and seniority. Its absence is materially suspicious.
- **Medium severity** (−0.15 penalty): We would expect this but its omission is not impossible to explain.
- **Low severity** (0 penalty): Noted in the audit trail, does not affect confidence.

The silence penalty is computed and applied separately from claim quality, so the two signals remain independently auditable.

---

## 4. The Confidence Formula

### Full Derivation

The confidence percentage is a two-input blend: evidence quality (how well the CV substantiates claims) and fit quality (how well those claims match the role). Evidence quality carries 60% weight because bad evidence about a perfect fit is still bad evidence.

**Step 1: Raw evidence score**

```
total_weighted_score = sum(claim.confidence_weight for claim in claims)
silence_penalty      = sum(flag.penalty for flag in silence_flags)  # 0.3 or 0.15 per flag
raw_evidence_score   = (total_weighted_score - silence_penalty) / max(claim_count, 1)
```

**Step 2: Normalise evidence score to 0–1**

```
# Maximum possible score if all claims were Tier A (weight 1.0):
max_possible = 1.0
evidence_score = clamp(raw_evidence_score / max_possible, 0.0, 1.0)
```

**Step 3: Fit score from FitAnalysis**

```
fit_score = (
    technical_fit         × 0.35
  + experience_level_fit  × 0.25
  + learning_velocity     × 0.25
  + builder_maintainer    × 0.15
)
# Weights from Schmidt & Hunter (1998) meta-analysis on hiring predictors
```

**Step 4: Confidence percentage**

```
confidence_pct = (evidence_score × 0.6 + fit_score × 0.4) × 100
```

### Worked Example

Candidate c01 (Amara Osei-Bonsu, STRONG_YES calibration anchor):

| Claim | Tier | Weight |
|-------|------|--------|
| "820-star OSS library used by Monzo internal test suite" | A | +1.0 |
| "40K TPS redesign — Monzo Black Friday 2023" | B | +0.7 |
| "Promoted SWE II → Senior in 22 months (median: 36)" | A | +1.0 |
| "Led 4-person squad on Python 2.7 → 3.11 migration" | B | +0.7 |
| "Reconciliation batch: 4h 20m → 23 minutes (Go)" | B | +0.7 |
| "Radar API p99: 280ms → 47ms (Redis cache)" | B | +0.7 |
| "Skilled communicator and team player" | C | +0.3 |

**total_weighted_score** = 1.0 + 0.7 + 1.0 + 0.7 + 0.7 + 0.7 + 0.3 = **5.1**
**silence_penalty** = 0 (all expected signals present for senior SWE)
**raw_evidence_score** = 5.1 / 7 = **0.729**
**evidence_score** = clamp(0.729, 0, 1) = **0.729**

FitAnalysis:
- technical_fit = 0.95 (expert Python/Go, fintech domain, all hard requirements met)
- experience_level_fit = 0.90 (8 years, two promotions, scope matches senior role)
- learning_velocity = 0.88 (Python→Go, Kafka, Terraform — clear skill expansion across roles)
- builder_maintainer = 0.95 (zero-to-one Paystack API, Stripe sandbox, Monzo ledger)

**fit_score** = (0.95 × 0.35) + (0.90 × 0.25) + (0.88 × 0.25) + (0.95 × 0.15)
             = 0.3325 + 0.225 + 0.22 + 0.1425
             = **0.920**

**confidence_pct** = (0.729 × 0.6 + 0.920 × 0.4) × 100
                   = (0.4374 + 0.3680) × 100
                   = **80.5% → STRONG_YES**

---

## 5. Verdict Routing Logic

Verdict assignment follows a strict priority order. Escalation conditions are checked before confidence thresholds. This prevents a high-confidence (but contradicted) candidate from bypassing human review.

```
IF hard_requirements NOT met:
    verdict = STRONG_NO
    tier_processed = 1
    → END immediately (skip all LLM analysis)

ELSE IF has_critical_contradiction == True:
    verdict = ESCALATE
    escalation_category = "critical_contradiction"
    → build_human_brief node

ELSE IF bias_flag_detected AND escalate_on_bias_flag == True:
    verdict = ESCALATE
    escalation_category = "bias_flag_detected"
    → build_human_brief node

ELSE IF has_unverifiable_high_stakes_claim == True AND confidence_pct >= yes_threshold:
    verdict = ESCALATE
    escalation_category = "unverifiable_high_stakes_claim"
    → build_human_brief node

ELSE IF confidence_pct >= strong_yes_threshold (default: 80%):
    verdict = STRONG_YES

ELSE IF confidence_pct >= yes_threshold (default: 65%):
    verdict = YES

ELSE IF confidence_pct >= ambiguous_threshold (default: 45%):
    verdict = AMBIGUOUS

ELSE IF confidence_pct >= no_threshold (default: 25%):
    verdict = NO

ELSE:
    verdict = STRONG_NO
```

All thresholds are loaded from `Settings` (environment variables). No threshold is hardcoded in node logic. This means the same pipeline can be recalibrated for different hiring standards without touching a single node file.

---

## 6. Schema Catalog

### `ScreeningInput`
The entry contract. All pipeline runs begin here.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `candidate_id` | `str` (max 64, no spaces) | Yes | Opaque ID, never contains PII |
| `cv_text` | `str` (min 50 chars) | Yes | Raw CV text — plain text, HTML, or Markdown |
| `job_description` | `str` (min 50 chars) | Yes | Full JD including requirements and context |
| `role_seniority` | `Literal` | Yes | `junior / mid / senior / staff / executive` |
| `role_type` | `Literal` | Yes | `engineering / product / data / design / operations / other` |
| `batch_id` | `Optional[str]` | No | Groups candidates for same role (enables cohort ranking) |
| `hard_requirements` | `list[str]` | No | Knockout criteria checked by tier1_prefilter |

### `CandidateProfile`
Structured, anonymised CV representation. Frozen after parse_candidate.

Key design decisions: `anonymised_name` replaces the real name in all downstream processing. `has_non_linear_path` is explicitly positive — non-linear careers are a learning agility signal, not a red flag. `employment_gaps` are data points with context, not automatic penalties.

### `EvidenceBundle`
The heart of SCREEN. Contains all `Claim`, `Contradiction`, and `SilenceFlag` objects.

| Field | Type | Description |
|-------|------|-------------|
| `claims` | `list[Claim]` | All evidence with tier and weight |
| `contradictions` | `list[Contradiction]` | Detected conflicts — typed by contradiction kind |
| `silence_flags` | `list[SilenceFlag]` | Absent expected signals |
| `builder_signals` | `list[str]` | Vocabulary/evidence of building from scratch |
| `maintainer_signals` | `list[str]` | Vocabulary/evidence of maintaining existing systems |
| `builder_maintainer_verdict` | `Literal` | `builder / maintainer / hybrid / insufficient_data` |
| `has_critical_contradiction` | `bool` | Triggers ESCALATE regardless of confidence |
| `has_unverifiable_high_stakes_claim` | `bool` | Triggers ESCALATE when combined with high confidence |

Computed properties (not stored fields): `total_weighted_score` (sum of claim weights), `silence_penalty` (sum of active flag penalties). These are computed fresh from the data, never cached — ensures they can't become stale.

### `FitAnalysis`
Four-dimension scoring with evidence-linked rationales.

| Dimension | Weight in `composite_fit_score` | Research basis |
|-----------|----------------------------------|----------------|
| `technical_fit` | 35% | Direct skill-to-requirement match |
| `experience_level_fit` | 25% | Seniority and scope match |
| `learning_velocity_score` | 25% | Bock (2015) — highest long-term performance predictor |
| `builder_maintainer_score` | 15% | Role-need alignment (startup vs. enterprise) |

Additional fields: `career_shape` (6 types from ascending to non_linear), `company_contexts` (per-company size/stage/outcome), `non_obvious_fit_signals` (ATS-invisible signals), `probe_points` (input to human brief).

### `Decision`
The final output of the pipeline for one candidate. Every `primary_evidence` entry is a citation from the `EvidenceBundle` — not generated fresh. This makes the verdict auditable by tracing back to a specific `Claim` or `SilenceFlag`.

Also contains `estimated_cost_usd` and `processing_time_ms` — transparent economics as a first-class output field.

### `HumanBrief`
Generated only for `ESCALATE` verdicts. Contains: `what_we_know`, `what_we_cannot_verify`, `verification_tasks`, `suggested_interview_questions`, `first_question`, and `risk_to_probe`. The `first_question` field specifically targets the most material unverifiable claim — it is not a generic opener.

### `CandidateFeedback`
Generated for every verdict, including rejections. Contains one `genuine_strength` (minimum 20 characters, must be specific) and one `gap_for_this_role` (specific to this role mismatch, not a general criticism). `encouragement` is set only when the gap is genuinely closable.

### `CohortAnalysis`
Batch-mode output. Per-candidate ranks across four dimensions (overall, technical, velocity, trajectory). Includes `cohort_bias_flags` — a batch-level check for systematic patterns in rejections.

### `TrajectoryEntry`
One entry per node. Fields: `node`, `timestamp_eat` (East Africa Time), `reasoning_summary` (PII-free, readable by a hiring manager), `evidence_keys`, `model_used`, `duration_ms`, `cost_usd`, `output_summary`. Privacy: reasoning_summary must never reproduce raw CV text or candidate names.

### `HumanOverride`
Records human disagreement with agent verdicts. The `outcome` field is populated later when the hire's real performance is known — this is the ground truth for long-term calibration.

---

## 7. Node Specifications

### Node 1 — `parse_candidate`
- **Purpose:** Extract structured data from raw CV text and anonymise the candidate
- **Input:** `ScreeningInput.cv_text`
- **Output:** `CandidateProfile`
- **LLM:** Gemini 1.5 Flash (structured output mode)
- **Key logic:** Name and photo references stripped before populating `CandidateProfile`. Duration in months calculated from dates. `has_non_linear_path` flagged if career spans ≥2 unrelated domains. `is_quantified` flagged per role if any numeric outcome is present.
- **Estimated cost:** ~$0.0005/candidate (Flash pricing, ~2K tokens)

### Node 2 — `tier1_prefilter`
- **Purpose:** Deterministic hard requirement check — no LLM involved
- **Input:** `CandidateProfile`, `ScreeningInput.hard_requirements`
- **Output:** `hard_rejected: bool` in state
- **LLM:** None — rule-based string matching + heuristics
- **Key logic:** Each hard requirement is checked against skills, roles, and education. If any requirement fails, `hard_rejected = True` and the pipeline routes to END with `STRONG_NO`. This is the cheapest possible rejection — no Pro model tokens spent on clearly unqualified candidates.
- **Estimated cost:** $0 (no LLM call)

### Node 3 — `extract_evidence`
- **Purpose:** Build the `EvidenceBundle` — classify claims, detect contradictions, identify silence flags
- **Input:** `CandidateProfile`, `ScreeningInput` (for role context)
- **Output:** `EvidenceBundle`
- **LLM:** Gemini 1.5 Pro (structured output mode)
- **Key logic:** LLM is prompted to classify each claim by tier using the ABCD taxonomy. Contradictions are identified by type (temporal, scope_inflation, skill_level, title_inflation, employment_gap). Silence flags are generated based on role_seniority and role_type — a missing team_size is flagged as high-severity for senior/executive, not for junior. Builder vs. maintainer vocabulary is extracted separately.
- **Estimated cost:** ~$0.003/candidate (~4K tokens at Pro pricing)

### Node 4 — `analyze_fit`
- **Purpose:** Multi-dimensional role fit assessment
- **Input:** `CandidateProfile`, `EvidenceBundle`, `ScreeningInput`
- **Output:** `FitAnalysis`
- **LLM:** Gemini 1.5 Pro (structured output mode)
- **Key logic:** Each dimension scored independently to prevent holistic impression bias. `career_shape` is classified into 6 types. `CompanyContext` is assessed per role — "VP Engineering at a 5-person startup managing 0 engineers" flags `role_scope_appropriate = False`. `learning_velocity_evidence` explicitly lists new skills across roles (not just skills stated).
- **Estimated cost:** ~$0.003/candidate (~4K tokens)

### Node 5 — `detect_bias`
- **Purpose:** Audit reasoning for demographic proxies and structural bias patterns
- **Input:** `CandidateProfile`, `FitAnalysis`, reasoning trace from prior nodes
- **Output:** `bias_flags` list appended to `FitAnalysis`, `has_bias_flag: bool`
- **LLM:** Gemini 1.5 Pro
- **Key logic:** Checks for prestige university bias, name-based inference, gap penalisation without context, non-linear path penalisation, school-of-thought bias in technical preferences. Writes findings back to FitAnalysis.bias_flags. Triggers ESCALATE when `escalate_on_bias_flag = True` in Settings.
- **Estimated cost:** ~$0.002/candidate (~2.5K tokens)

### Node 6 — `make_decision`
- **Purpose:** Deterministic confidence calculation and verdict routing
- **Input:** `EvidenceBundle`, `FitAnalysis`
- **Output:** `Decision` (without `human_brief` or `candidate_feedback`)
- **LLM:** None — mathematical formula from Settings thresholds
- **Key logic:** Applies the confidence formula. Checks escalation conditions in priority order (contradictions first, then bias, then unverifiable claims). Sets `should_escalate` routing flag.
- **Estimated cost:** $0

### Node 7 — `build_human_brief`
- **Purpose:** Construct a structured escalation brief for human reviewers
- **Input:** `EvidenceBundle`, `FitAnalysis`, `Decision`
- **Output:** `HumanBrief`
- **LLM:** Gemini 1.5 Pro (ESCALATE verdicts only)
- **Key logic:** Generates specific verification tasks (not generic "check references"). Produces a targeted `first_question` and `risk_to_probe`. `what_we_know` is drawn from Tier A and strong Tier B claims only. `what_we_cannot_verify` lists the specific unverifiable claims that were material to the escalation.
- **Estimated cost:** ~$0.003/candidate (only runs on ESCALATE)

### Node 8 — `candidate_feedback`
- **Purpose:** Generate candidate-facing feedback for all verdicts
- **Input:** `Decision`, `FitAnalysis`, `EvidenceBundle`
- **Output:** `CandidateFeedback`
- **LLM:** Gemini 1.5 Flash (cheap — runs for every candidate)
- **Key logic:** `genuine_strength` must cite a specific CV element — not a platitude. `gap_for_this_role` explains the mismatch in terms of this specific role's requirements. `encouragement` is generated only when `career_shape` is ascending/accelerating and the gap is a concrete skill deficit (closable), not a fundamental mismatch.
- **Estimated cost:** ~$0.0005/candidate

### Node 9 — `comparative_rank`
- **Purpose:** Cross-candidate cohort ranking (batch mode)
- **Input:** All `Decision` and `FitAnalysis` objects sharing a `batch_id`
- **Output:** `CohortAnalysis`
- **LLM:** Gemini 1.5 Flash (ranking synthesis)
- **Condition:** Only runs when `batch_id` is set and ≥2 candidates are available
- **Key logic:** Ranks candidates across four independent dimensions. Generates `cohort_bias_flags` by checking for systematic rejection patterns (e.g. all rejections from candidates with non-traditional education). Produces `cohort_insight` for the hiring manager.
- **Estimated cost:** ~$0.001/candidate in batch (amortised)

### Node 10 — `log_trajectory`
- **Purpose:** Append-only audit trail entry for the completed pipeline run
- **Input:** All state fields
- **Output:** `TrajectoryEntry` appended via LangGraph reducer
- **LLM:** None
- **Key logic:** Timestamps in EAT (Africa/Nairobi). Privacy check: no raw CV text in `reasoning_summary`. Cost accumulated via `operator.add` reducer.
- **Estimated cost:** $0

---

## 8. The Human Brief

The `HumanBrief` is the feature no ATS or AI screener provides. When a candidate is escalated, a human reviewer does not receive a flag that says "review this." They receive a structured document that tells them:

1. **What we know** — Tier A and strong Tier B claims, ranked by materiality. The reviewer starts from a foundation of verified evidence.
2. **What we cannot verify** — The specific claims that are both high-impact and externally unverifiable. Not a list of everything uncertain — only what matters.
3. **Verification tasks** — Concrete external steps. "Check LinkedIn for DataCorp founding date against the candidate's stated join date" — not "verify employment history."
4. **Suggested interview questions** — Evidence-based questions targeting the specific gaps identified in the analysis. These are generated from `FitAnalysis.probe_points`, not from a generic interview question bank.
5. **First question** — The single most important question to open with. Targets the most material unverifiable claim or the primary contradiction. Opens with this to get the answer on record before the candidate has been warmed up.
6. **Risk to probe** — The one thing that, if it turns out to be true, would likely disqualify this candidate. Ask about this early.

The `escalation_category` field determines the framing: a `critical_contradiction` brief reads differently from an `ambiguous_non_linear_background` brief. The human reviewer sees a brief calibrated to the actual reason for escalation.

---

## 9. Bias Detection

### Design Philosophy

Bias detection in SCREEN is not a disclaimer. It is a first-class node in the pipeline, with its own schema output, its own LLM call, and its own routing consequences. When bias is detected and `escalate_on_bias_flag` is enabled (default: True), the verdict is ESCALATE — not just flagged in a log somewhere.

### What `detect_bias` Checks

**Prestige bias:** Does the analysis assign higher weight to candidates from certain universities, companies, or cities? A bootcamp graduate with 3 shipped products should not be penalised relative to a top-university graduate with none.

**Name-based inference:** Does reasoning about communication style, culture fit, or collaborative ability correlate with names that carry demographic signals? `anonymised_name` is the pipeline's structural defence against this — but `detect_bias` audits whether it leaked through anyway.

**Gap penalisation without context:** Are employment gaps being penalised as red flags without considering their context (age at time of gap, explanation provided, gap duration, era)? `EmploymentGap.explanation_provided` captures whether an explanation was given — but detect_bias checks whether the penalty is proportionate.

**Non-linear path penalisation:** A career spanning multiple domains is, in our research synthesis, a signal of learning agility — not a resume defect. `detect_bias` flags when analysis treats non-linear paths as liabilities.

**Technical school-of-thought bias:** In engineering roles, does the analysis implicitly prefer certain language ecosystems, architectural styles, or tooling choices without a role-specific justification?

### Why It's Escalation-Worthy

A biased verdict is not just a lower-quality verdict — it is potentially a discriminatory one. Automated employment decisions that exhibit demographic bias are precisely the failure mode that the EU AI Act's high-risk AI category was written to prevent. SCREEN treats a detected bias flag as a reason to put a human in the loop, not as a note in the margin.

---

## 10. Evaluation Framework

### The 10 Test Cases

The evaluation suite (`evaluation/candidates/`) contains 10 candidates designed to test specific pipeline capabilities:

| ID | Scenario | Ground Truth | Tests |
|----|----------|--------------|-------|
| c01 | Senior SWE, fintech, all signals strong | STRONG_YES | Calibration anchor — confidence formula baseline |
| c02 | Strong candidate, date contradiction (temporal) | ESCALATE | Critical contradiction routing |
| c03 | Junior applying to senior role | STRONG_NO | Hard requirement detection + tier1 routing |
| c04 | Non-linear career (designer → data → PM) | YES or AMBIGUOUS | Non-linear path classification |
| c05 | Vague CV, all Tier C claims | NO or AMBIGUOUS | Silence flag system |
| c06 | Bootcamp + shipped products vs. CS degree | YES | Non-traditional education classification |
| c07 | Scope inflation (VP at 4-person company) | ESCALATE | Title inflation contradiction type |
| c08 | Prestige-bias bait (Oxbridge, no outputs) | NO or AMBIGUOUS | Bias detection for prestige signals |
| c09 | High velocity but wrong domain | AMBIGUOUS | Technical fit vs. learning velocity trade-off |
| c10 | Career descender (Director → Manager) | YES or AMBIGUOUS | Descending career shape classification |

### Metrics

**Verdict accuracy:** % of candidates whose SCREEN verdict matches the ground truth verdict in the test case. Target: ≥80% exact match, ≥95% within one category.

**Confidence calibration:** For ground truth STRONG_YES candidates, mean confidence should be ≥80%. For ground truth STRONG_NO, mean confidence should be ≤25%. Calibration error < 10%.

**Contradiction detection rate:** All test cases with planted contradictions should trigger ESCALATE. Target: 100%.

**Bias non-regression:** Prestige-bias test cases (c08) should not produce a YES verdict based on institution name alone. Target: 100%.

**Cost per candidate:** Tier 1 rejections (c03) should cost < $0.001. Full pipeline should average < $0.015/candidate.

### Baseline Comparison Methodology

The evaluation runner compares SCREEN against a naive baseline: a single Gemini 1.5 Flash call with the prompt "Review this CV for this job and tell me if the candidate should proceed to interview." The baseline is scored on the same test cases. SCREEN's improvement over baseline on contradiction detection, confidence calibration, and bias non-regression is the primary hackathon metric.

---

## 11. Competitive Differentiation

| Capability | Traditional ATS | GPT Wrapper | Eightfold.ai / HireVue | **SCREEN** |
|------------|----------------|-------------|-------------------------|------------|
| Structured output | Keywords only | Unstructured text | Black-box score | Pydantic-validated schema at every stage |
| Evidence citation | None | None | None | Every verdict cites specific claims from the CV |
| Calibrated confidence | None | None | Score (opaque) | Mathematical formula, derivation auditable |
| Contradiction detection | None | Occasional mention | Unknown | First-class Tier D claims, 5 contradiction types |
| Silence reading | None | None | None | SilenceFlag schema, role-appropriate severity |
| Bias detection | None | None | Marketed, opaque | First-class node, triggers ESCALATE |
| Human escalation | Binary flag | None | Some | Structured HumanBrief with specific questions |
| Candidate feedback | Never | None | None | CandidateFeedback for all verdicts including rejections |
| Career arc analysis | None | Ad hoc | Unknown | 6 CareerShape types, CompanyContext per role |
| Builder/Maintainer classification | None | None | None | EvidenceBundle vocabulary analysis |
| Non-linear path detection | Penalises | Inconsistent | Unknown | Explicit positive signal |
| Cohort ranking | Basic sort | None | Ranking (opaque) | Multi-dimension CohortAnalysis with bias monitoring |
| Audit trail | None | None | Some | Full TrajectoryEntry per node, EAT timestamps |
| Cost transparency | N/A | N/A | N/A | `estimated_cost_usd` in every Decision output |
| Open source | No | No | No | Yes |
| EU AI Act readiness | No | No | Partial | Trajectory log + bias node address high-risk AI requirements |

---

## 12. Architecture Decision Records (ADRs)

### ADR-01: LangGraph over custom orchestration
**Decision:** Use LangGraph for pipeline orchestration.
**Reasoning:** The pipeline requires conditional branching (tier1 rejection → END, ESCALATE → build_human_brief), append-only state reducers for trajectory, and clear node boundaries for testability. LangGraph provides all of this natively. Custom orchestration would replicate LangGraph's graph primitives with worse testing support.
**Trade-off:** Adds LangGraph as a dependency (~15MB) and requires understanding the TypedDict state contract. Accepted: the pipeline is more debuggable with explicit state than with implicit function chaining.

### ADR-02: Pydantic v2 frozen models throughout
**Decision:** All schemas use `ConfigDict(frozen=True)`.
**Reasoning:** Evidence is immutable. A node should not be able to retroactively modify what a prior node found. Frozen models make this a runtime guarantee, not a convention. If a downstream node needs a modified version of a prior schema, it creates a new model — it does not mutate the existing one.
**Trade-off:** Requires discipline in how nodes return data (always return new objects). Accepted: the correctness guarantee is worth it.

### ADR-03: Deterministic decision node, not LLM verdict
**Decision:** The `make_decision` node uses a mathematical formula, not an LLM call, to assign the verdict.
**Reasoning:** LLM-assigned verdicts are not reproducible. Running the same candidate through the same pipeline twice with temperature > 0 could produce different verdicts. A mathematical formula on top of LLM-extracted evidence gives us the best of both worlds: LLM reasoning for evidence extraction, deterministic logic for the final decision.
**Trade-off:** The formula requires well-calibrated evidence extraction. If `extract_evidence` produces bad tiers, the formula produces a bad verdict. This is explicit — bad evidence produces low confidence, which surfaces as AMBIGUOUS or requires human review.

### ADR-04: Separate bias node, not embedded in analyze_fit
**Decision:** `detect_bias` is a standalone node, not a check inside `analyze_fit`.
**Reasoning:** If bias detection is embedded in fit analysis, it can be influenced by (or influence) the analysis it's supposed to audit. A standalone node reads the analysis outputs and audits them independently — it sees the reasoning, not just the inputs. This also means bias detection can trigger ESCALATE even when the fit analysis concluded YES, which is the correct behavior.
**Trade-off:** Extra LLM call. Accepted: the independence and escalation authority are worth the cost.

### ADR-05: Silence flags as a first-class schema type
**Decision:** Absences are modelled explicitly as `SilenceFlag` objects with severity, not as a vague "low information" signal.
**Reasoning:** The difference between "I have no information about team size" and "this senior manager never once mentioned team size across 5 roles" is material. Formalising silence flags forces the extract_evidence node to reason about what is absent role-appropriately, and makes absence penalties auditable in the trajectory log.
**Trade-off:** Requires the extract_evidence prompt to explicitly reason about what should be present for a given role/seniority, which adds prompt complexity. Accepted.

### ADR-06: Gemini Flash for cheap nodes, Pro for analysis nodes
**Decision:** Parse and feedback nodes use Gemini 1.5 Flash. Evidence extraction, fit analysis, bias detection, and human brief use Gemini 1.5 Pro.
**Reasoning:** Structured extraction (parse_candidate) and short-form generation (candidate_feedback) do not require Pro-level reasoning. Evidence extraction, multi-dimensional scoring, and bias auditing do — they involve chains of reasoning over long documents. Two-tier model selection cuts cost by ~60% without sacrificing quality on the high-stakes nodes.
**Trade-off:** Different models may behave differently on edge cases. All nodes use temperature 0.1 for consistency.

### ADR-07: All thresholds in Settings, zero in node logic
**Decision:** Every confidence threshold, cost estimate, and escalation flag lives in `Settings` (pydantic-settings, loaded from `.env`). Node logic contains no literals.
**Reasoning:** Recalibrating the pipeline for a different hiring context (high-volume junior screening vs. executive search) should require only `.env` changes, not code changes. A system that hardcodes thresholds cannot be safely deployed across different hiring contexts.
**Trade-off:** All configuration must be documented in `.env.example`. Accepted: documentation cost is low, recalibration cost reduction is high.

---

## 13. EU AI Act Compliance Notes

The EU AI Act classifies automated employment decision systems as high-risk AI (Annex III, point 4). High-risk AI systems are required to maintain:

1. **Technical documentation** — This document satisfies the requirement for documentation of the system's design, purpose, and logic.

2. **Logging and audit trail** — `TrajectoryEntry` per node, with EAT timestamps, reasoning summaries, evidence keys, and model IDs. The append-only `operator.add` LangGraph reducer ensures the trail cannot be modified retroactively.

3. **Human oversight mechanism** — The ESCALATE verdict and `HumanBrief` are the mandatory human-in-the-loop mechanism. When `escalate_on_bias_flag` or `escalate_on_critical_contradiction` is enabled (default: both True), cases requiring human review are automatically routed.

4. **Accuracy, robustness, and cybersecurity** — Pydantic validation at every schema boundary prevents malformed data from propagating. `tenacity` retry logic prevents transient LLM failures from producing silent errors.

5. **Transparency to deployers** — `estimated_cost_usd` and `processing_time_ms` in every `Decision` output. `HumanOverride` schema closes the feedback loop when humans disagree.

6. **Non-discrimination** — `detect_bias` as a first-class node, with `anonymised_name` as a structural defence. Batch-level `cohort_bias_flags` provide continuous monitoring.

SCREEN is not legal advice and does not guarantee EU AI Act compliance in production deployment. These notes describe the architectural decisions made with compliance in mind.

---

## 14. Cost Economics

### Per-Candidate Cost Breakdown

| Node | Model | Estimated Tokens | Cost (USD) | Runs When |
|------|-------|------------------|------------|-----------|
| parse_candidate | Gemini 1.5 Flash | ~2,000 | $0.00015 | Always |
| tier1_prefilter | None | 0 | $0.00000 | Always |
| extract_evidence | Gemini 1.5 Pro | ~4,000 | $0.00500 | Hard requirements pass |
| analyze_fit | Gemini 1.5 Pro | ~4,000 | $0.00500 | Hard requirements pass |
| detect_bias | Gemini 1.5 Pro | ~2,500 | $0.00313 | Hard requirements pass |
| make_decision | None | 0 | $0.00000 | Hard requirements pass |
| build_human_brief | Gemini 1.5 Pro | ~3,000 | $0.00375 | ESCALATE only |
| candidate_feedback | Gemini 1.5 Flash | ~1,000 | $0.00008 | Always |
| comparative_rank | Gemini 1.5 Flash | ~2,000/batch | $0.00015 | batch_id set, amortised |
| log_trajectory | None | 0 | $0.00000 | Always |

### Scenario Costs

| Scenario | Cost | Notes |
|----------|------|-------|
| Hard rejected (Tier 1 stop) | ~$0.00023 | Flash parse + feedback only |
| Full pipeline, no escalation | ~$0.01336 | All Pro nodes, no brief |
| Full pipeline, escalated | ~$0.01711 | Includes human brief |
| 100-candidate batch | ~$1.34–$1.71 | ~$0.014 average |
| 1,000-candidate batch | ~$13–$17 | vs. typical ATS $5–$50/seat/month |

### Context

At $0.014/candidate average, SCREEN screens a 100-candidate pool for approximately $1.40. A recruiter spending 5 minutes per CV at $35/hour costs $291 for the same pool. SCREEN provides structured output, audit trail, cohort ranking, and candidate feedback for less than 0.5% of that cost — with the recruiter's time freed for the 15–20 candidates that warrant human attention.
