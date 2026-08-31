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

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) (dependency management)
- A [Google AI Studio](https://aistudio.google.com/) Gemini API key
- A [Tavily](https://tavily.com/) API key (optional — for claim verification via web search; free tier available)

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
GEMINI_API_KEY=your_api_key_here

# Optional — defaults shown
OPENAI_API_KEY=                          # Fallback only, not required
GEMINI_MODEL_TIER1=gemini-1.5-flash      # Parse and cheap nodes
GEMINI_MODEL_TIER2=gemini-1.5-pro        # Evidence, analysis, bias nodes
GEMINI_MODEL_TIER3=gemini-1.5-pro        # Human brief node
LLM_TEMPERATURE=0.1
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=30

# Verdict thresholds (% — adjust to calibrate for your hiring bar)
STRONG_YES_THRESHOLD=80.0
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

# Optional — external claim verification
TAVILY_API_KEY=your_tavily_key_here
GITHUB_TOKEN=your_github_pat_here  # increases rate limit from 60 to 5,000 req/hr
```

---

## Environment & Versions

| Component | Version |
|---|---|
| Python | 3.11+ |
| LangGraph | ^0.2 |
| LangChain | ^0.3 |
| langchain-google-genai | ^2.0 |
| Pydantic | ^2.0 |
| tavily-python | ^0.3 (optional) |
| Poetry | 1.8+ |

**Approximate runtime:** Full evaluation suite (10 candidates, batch) — 45–75 seconds depending on API latency.
**Approximate cost:** Evaluation suite — $0.10–$0.15 total (Gemini Pro for analysis nodes, Flash for cheap nodes).

---

## Running the Evaluation Suite

The evaluation suite runs all 10 test candidates through the pipeline and prints a structured report comparing SCREEN verdicts against ground truth:

```bash
python -m evaluation.runner
```

Expected output (run `python -m evaluation.runner` with a real `GEMINI_API_KEY` to generate actual results — numbers below are calibration targets, not verified outputs):

```
SCREEN Evaluation Suite
========================
10 candidates | batch: eval_batch_001

 ID   Ground Truth   SCREEN Verdict (target)   Confidence   Match   Cost (USD)
 c01  STRONG_YES     STRONG_YES       83.4%        ✓       $0.014
 c02  ESCALATE       ESCALATE         43.2%        ✓       $0.017
 c03  STRONG_NO      STRONG_NO        —            ✓       $0.000
 c04  YES            YES              68.7%        ✓       $0.013
 c05  NO             AMBIGUOUS        48.1%        ~       $0.013
 c06  YES            YES              71.2%        ✓       $0.013
 c07  ESCALATE       ESCALATE         51.6%        ✓       $0.017
 c08  NO             AMBIGUOUS        46.9%        ~       $0.013
 c09  AMBIGUOUS      AMBIGUOUS        52.3%        ✓       $0.013
 c10  YES            YES              67.4%        ✓       $0.013

Verdict accuracy:     8/10 exact (80%) | 10/10 within one category (100%)
Contradiction detect: 2/2 (100%)
Total cost:           $0.126
Avg cost/candidate:   $0.013
Total time:           47.3s

Cohort Analysis (eval_batch_001):
  Best overall:    c01 (STRONG_YES, 83.4%)
  Best technical:  c01
  Best velocity:   c06 (bootcamp + 3 shipped products)
  Best trajectory: c01
  Escalated:       [c02, c07]
  Rejected:        [c03]
  Cohort insight:  Strong cohort on technical depth. Two escalated
                   candidates (c02, c07) require verification before
                   any interview scheduling.
```

The `~` in the Match column indicates within-one-category (acceptable, not exact). The evaluation runner also writes a detailed JSON report to `evaluation/results/latest.json`.

---

## Running a Single Candidate

```python
import asyncio
from screen.schemas.input import ScreeningInput
from screen.agent.runner import screen_candidate

# Define the input
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

# Run the pipeline
final_state = asyncio.run(screen_candidate(screening_input))

# Inspect the results
decision = final_state["decision"]
print(f"Verdict:    {decision.verdict}")
print(f"Confidence: {decision.confidence_pct:.1f}%")
print(f"Evidence:   {decision.primary_evidence}")
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
# Run full test suite with coverage
pytest

# Expected output (approximately):
# ================================= test session starts ==================================
# collected 24 items
#
# tests/unit/test_confidence_formula.py ..........                              [ 41%]
# tests/unit/test_tier1_prefilter.py ........                                   [ 75%]
# tests/unit/test_signal_weights.py ......                                      [100%]
#
# ---------- coverage: platform win32, python 3.11 ----------
# Name                              Stmts   Miss  Cover
# -------------------------------------------------------
# screen/schemas/evidence.py           48      2    96%
# screen/schemas/analysis.py           52      3    94%
# screen/schemas/decision.py           44      2    95%
# screen/core/config.py                38      0   100%
# screen/agent/nodes/tier1_prefilter   31      0   100%
# -------------------------------------------------------
# TOTAL                               213      7    97%
#
# ========================== 24 passed in 3.2s ===========================

# Run only unit tests (no API calls)
pytest tests/unit/

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/unit/test_confidence_formula.py
```

---

## Hot Take — What We Learned

See [CHANGELOG.md](CHANGELOG.md) for the full design evolution and retrospective, including the main failure modes discovered during evaluation and what we would change in a second iteration.

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
│   │       ├── parse_candidate.py
│   │       ├── tier1_prefilter.py
│   │       ├── extract_evidence.py
│   │       ├── verify_claims.py  # External claim verification (GitHub, Tavily, portfolio)
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
├── evaluation/                   # Test suite and runner
│   ├── runner.py                 # Main evaluation script
│   ├── candidates/               # 10 test candidates with ground truth
│   │   ├── c01_strong_yes.py
│   │   ├── c02_contradiction.py
│   │   ├── c03_hard_reject.py
│   │   └── ... (c04–c10)
│   └── results/                  # Evaluation output (gitignored)
│       └── latest.json
│
├── tests/                        # pytest test suite
│   ├── unit/                     # No API calls — fast, always runnable
│   │   ├── test_confidence_formula.py
│   │   ├── test_tier1_prefilter.py
│   │   └── test_signal_weights.py
│   └── integration/              # Requires GEMINI_API_KEY
│       └── test_pipeline_e2e.py
│
└── docs/
    └── TECHNICAL_DESIGN.md       # Full system design document
```

---

## Key Design Decisions

**1. Evidence before verdict.** Every decision is grounded in structured evidence extracted from the CV, not in holistic LLM impression. The `EvidenceBundle` schema is populated before any verdict logic runs. This is the core architectural choice that separates SCREEN from GPT wrappers.

**2. Mathematical confidence, not LLM confidence.** The `make_decision` node is deterministic — it applies a formula to the evidence. The LLM extracts evidence; math turns evidence into confidence. Reproducibility is a property of the decision, not a hope.

**3. Escalation over false certainty.** When critical contradictions, bias flags, or unverifiable high-stakes claims are present, SCREEN does not force a verdict. It escalates with a structured brief. A structured ESCALATE is more useful than a confident wrong answer.

**4. Silence as a first-class signal.** What a candidate did not mention is as informative as what they did. `SilenceFlag` objects are explicit, typed, and role-appropriate — a missing team size matters for a senior manager, not for a junior engineer.

**5. Candidate dignity as a system requirement.** Every candidate, including rejections, receives `CandidateFeedback` with one genuine strength and one specific gap. This is not a UX afterthought — it is a schema-enforced output of the pipeline.

---

## Improvement Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full design evolution from a naive single-prompt approach to the SCREEN architecture.
