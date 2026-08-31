# SCREEN — Structured Candidate Reasoning and Evaluation Engine

SCREEN is an AI pre-screening agent that reasons like a senior recruiter: it extracts evidence from CVs, weights claims by verifiability, detects contradictions and suspicious absences, and produces structured verdicts with calibrated confidence percentages. Unlike keyword matchers or GPT wrappers, every verdict cites specific evidence from the CV and can be traced step-by-step through a full audit trail.

Built for the **micro1 Agentic Workflows Hackathon**, 2026-08-30.

---

## The Wow Moment

Here is the same candidate processed by a naive LLM call versus SCREEN.

**Candidate:** "Led DataCorp as Head of Engineering from Feb 2019. DataCorp was founded in June 2019."

### Naive baseline (single Gemini Flash prompt)

```
This candidate has strong leadership experience as Head of Engineering and demonstrates
good progression in their career. Recommend proceeding to interview.
```

No detection of the contradiction. No flag. Proceeds to interview.

### SCREEN output

```json
{
  "verdict": "ESCALATE",
  "confidence_pct": 43.2,
  "escalation_category": "critical_contradiction",
  "primary_evidence": [
    "CONTRADICTION (temporal/critical): Candidate states 'Head of Engineering at DataCorp from Feb 2019' but DataCorp was founded in June 2019 — a 4-month impossibility.",
    "SILENCE (high severity): No quantified outcomes in 3 years of stated leadership — unusual for a Head of Engineering claiming system ownership.",
    "CLAIM (Tier B): Demonstrated people management across 2 earlier roles — credible but uncorroborated at senior scope."
  ],
  "human_brief": {
    "summary": "Candidate claims a role that began 4 months before the company existed. Combined with a complete absence of quantified outcomes at leadership level, this requires verification before any decision.",
    "what_we_know": ["2 years people management at prior roles (Tier B)", "Python and Go skills consistent across CV"],
    "what_we_cannot_verify": ["DataCorp tenure dates", "Any claimed technical outcomes from DataCorp period"],
    "verification_tasks": ["Check DataCorp Companies House registration date", "Cross-reference LinkedIn for founding date"],
    "first_question": "Walk me through exactly when you joined DataCorp and what the team structure looked like in those first months.",
    "risk_to_probe": "If the DataCorp tenure is fabricated or significantly misrepresented, the entire CV's credibility is in question."
  },
  "candidate_feedback": {
    "genuine_strength": "Your Python-to-Go skill progression across roles is a strong learning agility signal — this is harder to fake than a certification.",
    "gap_for_this_role": "This role requires verified system-level ownership at scale. The DataCorp dates require clarification before we can assess that.",
    "encouragement": null
  }
}
```

The contradiction was caught. A human brief was constructed. The candidate still received dignified feedback.

---

## Pipeline Architecture

SCREEN is a 10-node LangGraph state machine. Each node has a single responsibility; the pipeline is fully traceable via a `trajectory` log on every run.

| # | Node | Type | What it does |
|---|------|------|--------------|
| 1 | `structural_precheck` | Deterministic | Hard-rejects if stated years < JD minimum. Zero LLM cost. |
| 2 | `parse_candidate` | LLM (Tier 1) | Pydantic-structured extraction: roles with dates, skills_stated, education → `CandidateProfile`. |
| 3 | `tier1_prefilter` | Deterministic | Degree check (word-boundary regex) runs **before** keyword scan. Zero LLM. |
| 4 | `extract_evidence` | LLM (Tier 2) | Produces `EvidenceBundle`: claims with quality tiers A/B/C/D, contradictions (temporal / skill_level / scope), silence flags. |
| 5 | `verify_claims` | External | Tavily web search for verifiable facts. Skips gracefully if no API key. |
| 6 | `analyze_fit` | LLM (Tier 2) | 5 independent dimensions: technical_fit, experience_level_fit, learning_velocity, builder_maintainer, career_trajectory_fit. |
| 7 | `detect_bias` | LLM (Tier 2) | Audits for protected-characteristic influence on prior node outputs. |
| 8 | `make_decision` | Deterministic | Formula: `(evidence_score × domain_relevance × 0.6 + fit_score × 0.4) × 100`. Maps to verdict band. |
| 9 | `build_human_brief` | LLM (Tier 2) | Structured escalation package: what we know, what we can't verify, 5 targeted interview questions. |
| 10 | `candidate_feedback` | LLM (Tier 1) | Dignified candidate-facing feedback for every verdict, including rejections. |

### Verdict bands

| Verdict | Threshold |
|---------|-----------|
| STRONG_YES | ≥ 86% |
| YES | ≥ 65% |
| AMBIGUOUS | ≥ 45% |
| NO | ≥ 25% |
| STRONG_NO | < 25% |
| ESCALATE | Critical contradiction, bias flag, or unverifiable high-stakes claim |

### Scoring formula

- **Signal tier weights:** A = 1.0, B = 0.7, C = 0.3, D = −1.5 (fabrication penalty)
- **Confidence normalisation:** `(per_claim_score + 1.5) / 2.5`
- **Final score:** `evidence_score × domain_relevance × 0.6 + fit_score × 0.4`
- **Domain relevance multiplier:** 0 keywords → 0.60 | 1–2 → 0.60 | 3–5 → 0.80 | 6+ → 1.0
- **Deterministic signal injection:** Python pre-computes `supervision_pct`, `production_deployment`, `skill_conflicts` before the LLM call — skill conflict detection is scoped to non-ops roles only
- **Models:** Tier 1 = `google/gemini-2.5-flash-lite` | Tier 2 = `openai/gpt-4o-mini` (both via OpenRouter)

---

## Cross-Batch Evaluation Results

| Batch | Domain | Candidates | Baseline Accuracy | SCREEN (Best) | Delta |
|-------|--------|------------|-------------------|---------------|-------|
| 1 | Senior Software Engineer | 10 | 30% | 80% | +50 pp |
| 2 | Senior Data Scientist | 8 | 38% | 88% | +50 pp |
| 3 | FMCG Operations Manager | 20 | 55% | 75% | +20 pp |
| 4 | Senior Digital Marketing Manager | 33 | 61% | 42% | −19 pp _(first uncalibrated domain run)_ |

### Batch 4 timing (sequential, 33 candidates)

| Metric | Value |
|--------|-------|
| Wall clock | 20m 51s |
| Hard-gate path | 3.6s avg, $0.00/candidate |
| LLM path | 42.4s avg, $0.0051/candidate |
| Throughput | 1.6 candidates/min sequential |

---

## Improvement Changelog

### Round 1 — Batch 1 (Senior SWE): 30% → 80%
Stopword expansion, passthrough condition fix, temporal contradiction precision (CV-text-only), bias escalation confidence gate, employment gap clarification.

### Round 2 — Batch 2 (Senior Data Scientist): 72.5% → 88%
Production deployment silence flag, supervision language dominance detection, academic vs. production distinction in experience scoring.

### Round 3 — Batch 3 (FMCG Ops Manager): 50% → 75%
Degree gate order bug fixed (runs before keyword scan), operations domain mismatch silence flag, domain mismatch scoring constraint (technical_fit cap), ERP skill conflict example.

### Stabilisation sprint
Deterministic signal injection, skill conflict detection scoped to non-ops roles, domain relevance multiplier → stable 75% on Batch 3.

### Known residual limitations
- **e15 (NGO ops) → AMBIGUOUS not NO:** NGO health vocabulary overlaps with supply chain terminology
- **e09 (hotel ops) → NO not AMBIGUOUS:** scoring ceiling at `domain_relevance = 0.60`
- **LLM variance:** ±8% on borderline candidates
- **Batch 4 (marketing):** 42% — uncalibrated domain, needs marketing-specific silence flags

---

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) (dependency management)
- An [OpenRouter](https://openrouter.ai/) API key (covers both Gemini Flash Lite and GPT-4o-mini)
- A [Tavily](https://tavily.com/) API key (optional — for claim verification; free tier available)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Kamara-AI/micro1-screen.git
cd micro1-screen

# 2. Install dependencies with Poetry
poetry install

# 3. Activate the virtual environment
poetry shell
```

---

## Configuration

Copy the example env file and populate it:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional — external claim verification
TAVILY_API_KEY=your_tavily_key_here

# Verdict thresholds (% — adjust to calibrate for your hiring bar)
STRONG_YES_THRESHOLD=86.0
YES_THRESHOLD=65.0
AMBIGUOUS_THRESHOLD=45.0
NO_THRESHOLD=25.0

# Escalation triggers (set to false to disable)
ESCALATE_ON_CRITICAL_CONTRADICTION=true
ESCALATE_ON_BIAS_FLAG=true
ESCALATE_ON_UNVERIFIABLE_HIGH_CONFIDENCE=true

# Environment
ENV=dev
LOG_LEVEL=INFO
TIMEZONE=Africa/Nairobi
```

---

## Running the Evaluation Suite

```bash
# Batch 1 — Senior Software Engineer (10 candidates)
python -m evaluation.runner --batch1

# Batch 2 — Senior Data Scientist (8 candidates)
python -m evaluation.runner --batch2

# Batch 3 — FMCG Operations Manager (20 candidates)
python -m evaluation.runner --batch3

# Batch 4 — Senior Digital Marketing Manager (33 candidates)
python -m evaluation.runner --batch4

# Sequential timing runner — simulates real queue, measures wall clock + cost
python -m evaluation.timing_runner

# Baseline only (single-LLM comparison)
python -m evaluation.baseline --batch1
```

The evaluation runner writes a detailed JSON report to `evaluation/results/` and prints a structured summary to stdout. See `evaluation/SCREEN_EVALUATION_REPORT.md` for the full cross-batch analysis.

---

## Running a Single Candidate

```python
import asyncio
from screen.schemas.input import ScreeningInput
from screen.agent.runner import screen_candidate

screening_input = ScreeningInput(
    candidate_id="candidate_001",
    role_seniority="senior",
    role_type="engineering",
    cv_text="""
    Jane Smith
    7 years backend engineering at payments companies.
    Led migration of core payment service from monolith to microservices.
    Reduced p99 latency from 450ms to 62ms.
    Python, Go, PostgreSQL, Kafka.
    """,
    job_description="""
    Senior Backend Engineer — Payments
    We are a Series A fintech processing $20M/month in transactions.
    Requirements: 5+ years backend, Python or Go, financial systems experience.
    """,
    hard_requirements=[
        "minimum 5 years backend engineering",
        "Python or Go proficiency",
        "financial systems experience",
    ],
    batch_id="my_batch_001",  # optional — enables cohort ranking
)

final_state = asyncio.run(screen_candidate(screening_input))

decision = final_state["decision"]
print(f"Verdict:    {decision.verdict}")
print(f"Confidence: {decision.confidence_pct:.1f}%")
print(f"Cost:       ${decision.estimated_cost_usd:.4f}")

# If escalated, read the human brief
if final_state.get("human_brief"):
    brief = final_state["human_brief"]
    print(f"\nFirst question: {brief.first_question}")
    print(f"Risk to probe:  {brief.risk_to_probe}")

# Candidate feedback (always present)
feedback = final_state["candidate_feedback"]
print(f"\nStrength: {feedback.genuine_strength}")
print(f"Gap:      {feedback.gap_for_this_role}")

# Full audit trail
for entry in final_state["trajectory"]:
    print(f"[{entry.node}] {entry.reasoning_summary} ({entry.duration_ms}ms, ${entry.cost_usd:.5f})")
```

---

## Running Tests

```bash
# Full test suite with coverage
pytest

# Unit tests only (no API calls — always runnable)
pytest tests/unit/

# Verbose output
pytest -v
```

---

## Key Design Decisions

**1. Evidence before verdict.** Every decision is grounded in structured evidence extracted from the CV, not in holistic LLM impression. The `EvidenceBundle` schema is populated before any verdict logic runs. This is the core architectural choice that separates SCREEN from GPT wrappers.

**2. Mathematical confidence, not LLM confidence.** The `make_decision` node is fully deterministic — it applies a formula to the extracted evidence. The LLM extracts evidence; math turns evidence into confidence. Reproducibility is a property of the decision, not a hope.

**3. Escalation over false certainty.** When critical contradictions, bias flags, or unverifiable high-stakes claims are present, SCREEN does not force a verdict. It escalates with a structured brief. A structured ESCALATE is more useful than a confident wrong answer.

**4. Silence as a first-class signal.** What a candidate did not mention is as informative as what they did. `SilenceFlag` objects are explicit, typed, and role-appropriate — a missing team size matters for a senior manager, not for a junior engineer.

**5. Candidate dignity as a system requirement.** Every candidate, including rejections, receives `CandidateFeedback` with one genuine strength and one specific gap. This is not a UX afterthought — it is a schema-enforced output of the pipeline.

**6. Deterministic gates run first, LLM runs second.** `structural_precheck` and `tier1_prefilter` are zero-cost Python nodes. Hard rejects never touch the LLM. On Batch 4, 9 of 33 candidates were eliminated at the gate at $0.00 cost.

---

## Project Structure

```
micro1-screen/
├── .env                          # Local secrets — never committed
├── .env.example                  # Template for .env setup
├── pyproject.toml                # Poetry dependencies and tool config
├── README.md                     # This file
├── CHANGELOG.md                  # Design evolution from v0 to v1
│
├── screen/                       # Main package
│   ├── schemas/                  # Pydantic models — the data contract
│   │   ├── input.py              # ScreeningInput — pipeline entry
│   │   ├── candidate.py          # CandidateProfile, RoleEntry, EducationEntry
│   │   ├── evidence.py           # EvidenceBundle, Claim, Contradiction, SilenceFlag
│   │   ├── analysis.py           # FitAnalysis, CareerShape, CompanyContext
│   │   ├── decision.py           # Decision, HumanBrief, CandidateFeedback, Verdict
│   │   ├── cohort.py             # CohortAnalysis, CandidateRank
│   │   ├── trajectory.py         # TrajectoryEntry, HumanOverride
│   │   └── state.py              # ScreeningState (LangGraph TypedDict)
│   │
│   ├── agent/                    # LangGraph pipeline
│   │   ├── graph.py              # Graph definition + conditional edges
│   │   ├── runner.py             # Public interface — screen_candidate(), screen_batch()
│   │   ├── output_formatter.py   # Markdown, console, and evaluation report formatters
│   │   └── nodes/                # One file per pipeline node
│   │       ├── structural_precheck.py
│   │       ├── parse_candidate.py
│   │       ├── tier1_prefilter.py
│   │       ├── extract_evidence.py
│   │       ├── verify_claims.py
│   │       ├── analyze_fit.py
│   │       ├── detect_bias.py
│   │       ├── make_decision.py
│   │       ├── build_human_brief.py
│   │       ├── candidate_feedback.py
│   │       └── comparative_rank.py
│   │
│   └── core/                     # Shared infrastructure
│       ├── config.py             # Settings (pydantic-settings, .env)
│       ├── exceptions.py         # Typed exceptions per failure class
│       ├── logging_config.py     # structlog setup
│       └── trajectory.py         # Trajectory helper — log_trajectory()
│
├── evaluation/                   # Evaluation harness
│   ├── runner.py                 # Parallel batch runner (--batch1 through --batch4)
│   ├── timing_runner.py          # Sequential timing harness — wall clock + cost
│   ├── baseline.py               # Single-LLM baseline for comparison
│   ├── SCREEN_EVALUATION_REPORT.md  # Full cross-batch analysis
│   ├── candidates/
│   │   ├── batch1/               # 10 Senior SWE candidates
│   │   ├── batch2/               # 8 Senior Data Scientist candidates
│   │   ├── batch3/               # 20 FMCG Ops Manager candidates
│   │   └── batch4/               # 33 Senior Digital Marketing Manager candidates
│   └── results/                  # Evaluation output JSON
│
├── reports/                      # Supplementary analysis reports
│
└── tests/                        # pytest test suite
    ├── unit/                     # No API calls — fast, always runnable
    │   ├── test_confidence_formula.py
    │   ├── test_tier1_prefilter.py
    │   └── test_signal_weights.py
    └── integration/              # Requires OPENROUTER_API_KEY
        └── test_pipeline_e2e.py
```

---

## Environment & Versions

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| LangGraph | ^0.2 |
| LangChain | ^0.3 |
| Pydantic | ^2.0 |
| Poetry | 1.8+ |
| tavily-python | ^0.3 (optional) |

---

For the full design evolution — including every failure mode discovered during evaluation and what we would change in a second iteration — see [CHANGELOG.md](CHANGELOG.md).
