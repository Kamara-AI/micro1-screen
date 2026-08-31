# SCREEN Screening Report

**Candidate ID:** `c03_date_contradiction`  
**Role:** Senior Data  
**Screened:** 2026-08-31T12:50:40.325544+03:00  
**Pipeline:** SCREEN v0.1.0 — Structured Candidate Reasoning and Evaluation Engine

---

## ⚠ Verdict: ⚠ ESCALATE — HUMAN REVIEW REQUIRED

**Confidence:** [████████████████░░░░] 81.7%

> **Why escalated:** Critical contradiction detected in the candidate's profile. A human reviewer must verify before any decision is made.

### Primary Evidence

- • Contradiction (critical): The candidate claims to have joined DataSync in 2019, but the role at DataSync starts in January 2018, which is before the company was founded.
- • Silence flag (high): Architectural decisions or design patterns used in data pipelines
- • Probe required: Clarify the timeline of employment at DataSync and the contradiction regarding the company's founding date.

---

## Candidate Strengths & Gaps

**Strength:** Your experience designing and building data ingestion pipelines with Kafka and Spark Streaming, handling significant data volumes, is impressive.

**Gap for this role:** We identified a critical contradiction regarding the timeline of your employment at DataSync, which requires further clarification and impacts our confidence in your candidacy for this role.

---

## ⚠ Escalation Brief — Human Review Required

**Escalation category:** `critical_contradiction`

> The candidate's timeline of employment at DataSync contradicts the company's founding date, raising significant concerns about the authenticity of their experience. A human review is necessary to clarify this critical contradiction before making a hiring decision.

### What We Know

- Led the design of DataSync's core ingestion pipeline using Apache Kafka and Spark Streaming, handling 15TB/day at peak.
- Built the customer-facing metrics API (Python/FastAPI) used by 80+ enterprise clients.
- Managed migration from on-prem Hadoop cluster to AWS EMR, saving $180K/year in infra costs.
- Built ETL pipelines for e-commerce transaction data (Python, Airflow, Redshift).

### What We Cannot Verify

- The candidate claims to have joined DataSync in 2019, but this contradicts the role starting in January 2018, which is before the company was founded. This matters as it raises questions about the candidate's integrity and the validity of their experience.

### Verification Tasks

1. Check DataSync's founding date on Crunchbase or Companies House to confirm the timeline.
2. Search LinkedIn for the candidate's profile and verify the role dates at DataSync.

### Open the Interview With This Question

> Can you clarify your timeline of employment at DataSync, specifically regarding when you joined and the company's founding date?

### Primary Risk to Probe

> If it turns out that the candidate intentionally misrepresented their employment timeline or the founding date of DataSync, this would likely disqualify them from consideration.

### Suggested Interview Questions

1. Can you clarify your timeline of employment at DataSync, specifically regarding when you joined and the company's founding date?
2. You mentioned leading the design of the core ingestion pipeline at DataSync — can you describe the architectural decisions you made during that process?
3. What specific design patterns did you implement in the data pipelines you worked on at DataSync?
4. Can you provide examples of how you mentored junior engineers and the impact it had on their careers?
5. How did you approach the migration from on-prem Hadoop to AWS EMR, and what challenges did you face during that process?

---

## Pipeline Audit Trail

| Step | Summary | Duration | Model | Cost |
|------|---------|----------|-------|------|
| `structural_precheck` | Structural precheck passed. No explicit year contradiction found in... | 0ms | deterministic | $0.00000 |
| `parse_candidate` | Parsed CV into structured profile. Found 2 roles, 13 stated skills,... | 3645ms | openrouter:google/gemini-2.5-flash-lite | $0.00007 |
| `tier1_prefilter` | All 3 hard requirement(s) satisfied. Candidate passes Tier 1 pre-fi... | 0ms | deterministic | $0.00000 |
| `extract_evidence` | Extracted 8 evidence claims (4 Tier A, 4 Tier B, 0 Tier C, 0 Tier D... | 9094ms | openrouter:openai/gpt-4o-mini | $0.00190 |
| `verify_claims` | Verified 0 claim(s) using external tools. 0 claim(s) upgraded to Ti... | 0ms | deterministic | $0.00000 |
| `analyze_fit` | Multi-dimensional fit analysis complete. Technical fit: 0.70. Exper... | 6113ms | openrouter:openai/gpt-4o-mini | $0.00242 |
| `detect_bias` | Bias audit complete. I reviewed the FitAnalysis for cognitive biase... | 2001ms | openrouter:openai/gpt-4o-mini | $0.00098 |
| `make_decision` | Deterministic decision. Evidence score: 0.918 (weighted claims − si... | 0ms | deterministic | $0.00000 |
| `build_human_brief` | Human brief generated for escalated candidate. Escalation category:... | 3685ms | openrouter:openai/gpt-4o-mini | $0.00201 |
| `candidate_feedback` | Candidate feedback generated for verdict: ESCALATE. Genuine strengt... | 2179ms | openrouter:google/gemini-2.5-flash-lite | $0.00004 |
| `comparative_rank` | Only 1 candidate(s) in batch 'eval_batch_001'. Need ≥2 for comparat... | 0ms | deterministic | $0.00000 |

**Total pipeline cost:** $0.0074  
**Total pipeline time:** 26717ms  
**Nodes executed:** 11

---

*Report generated by SCREEN — Structured Candidate Reasoning and Evaluation Engine*  
*micro1 Agentic Workflows Hackathon 2026*