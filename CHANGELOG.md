# SCREEN Improvement Changelog

This document traces the design evolution from the first naive approach to the SCREEN architecture. Each iteration describes a specific failure, the solution applied, and the measurable impact on output quality.

---

## The Problem with Naive AI Screening

The simplest possible AI screening implementation is this:

```python
response = llm.invoke(f"""
You are a recruiter. Review this CV for this job and tell me if the candidate
should proceed to interview.

CV: {cv_text}
Job: {job_description}

Your recommendation:
""")
print(response.content)
```

This is approximately what most "AI screening" tools deliver beneath their interface. It produces a paragraph of text. That paragraph has no structure, no confidence level, no citations, no audit trail, and no reproducibility. Run it twice and you may get different answers. It cannot be calibrated. It cannot be audited. It cannot be improved systematically. It is not a system — it is a prompt.

Every iteration below is a specific response to a specific failure of this baseline.

---

## Iteration 1 — Structured Output

**From:** Unstructured text response  
**To:** Pydantic-validated schema at every stage

**Problem:** The naive output is a paragraph. A paragraph cannot be routed, aggregated, compared, or reliably parsed. When you ask "what was the verdict?" you have to read the paragraph and interpret it. When you ask "why?" there is no structured answer. When you want to store it in a database, you need to write a parser that will break on edge cases.

**Solution:** Define a `Decision` schema before writing any node logic (schema-first development). Every node in the pipeline produces a typed, validated output. The `ScreeningInput` schema validates all input before any processing begins. Pydantic v2 with `ConfigDict(frozen=True)` enforces immutability — an output cannot be silently modified after it is produced.

**Impact:** Every output is machine-readable and human-readable simultaneously. Downstream processing is deterministic. Validation failures are caught at the boundary, not discovered later in production. The structured output is the foundation that makes every subsequent iteration possible.

---

## Iteration 2 — Evidence Tiers

**From:** Binary pass/fail based on holistic LLM impression  
**To:** Weighted evidence with quality classification (Tiers A, B, C, D)

**Problem:** The naive approach treats "I redesigned a fraud detection system" and "I worked on impactful projects" as equivalent evidence. They are not. One is a specific, plausible, potentially verifiable claim. The other is resume boilerplate. A system that cannot distinguish them will always be gamed by keyword stuffing and always miss candidates who describe real work without optimised phrasing.

**Solution:** The `extract_evidence` node classifies every claim into one of four tiers: A (verified, cross-referenceable), B (specific, plausible, uncontradicted), C (vague, generic), D (contradicted). Weights are assigned deterministically: A=+1.0, B=+0.7, C=+0.3, D=−1.5. The `EvidenceBundle` schema holds all claims with their tiers — not a summary of the CV, but a structured evidence record.

**Impact:** A candidate with three genuine Tier A claims scores higher than one with twenty Tier C boilerplate phrases. Keyword stuffing no longer passes the evidence quality threshold. Evidence quality becomes auditable: judges and reviewers can inspect exactly what weight was assigned to what claim and why.

---

## Iteration 3 — Silence Detection

**From:** Analysis of what is present in the CV  
**To:** Analysis of what is absent (and should be present)

**Problem:** Elite recruiters read absence as signal. A senior manager who never mentions team size across five roles is suspicious. A senior engineer whose entire CV has no architectural decisions is suspicious. The naive approach, and even a structured evidence approach, only processes what is written — it cannot flag what is missing.

**Solution:** The `SilenceFlag` schema captures expected signals that are absent, with a severity rating (high, medium, low) calibrated to role seniority and type. A missing team size is a high-severity flag for a senior/executive role, not for a junior one. Silence flags carry a numerical penalty (−0.30 for high, −0.15 for medium) that is applied separately from claim quality, so the two signals remain independently auditable.

**Impact:** Candidates who write impressive but content-free CVs — senior titles with no quantified outcomes, leadership claims with no team sizes, technical depth claims with no architecture decisions — are appropriately penalised. The penalty is proportionate and role-contextual, not a blanket CV length penalty.

---

## Iteration 4 — Deterministic Decision Engine

**From:** LLM-assigned verdict ("I think this candidate should proceed")  
**To:** Mathematical formula applied to evidence quality and fit scores

**Problem:** An LLM-assigned verdict is not reproducible. At temperature > 0, the same candidate through the same pipeline may receive YES one run and AMBIGUOUS the next. This is not calibrated confidence — it is stochastic opinion. A hiring decision system that is not reproducible cannot be audited, improved, or trusted.

**Solution:** The `make_decision` node contains no LLM call. It applies a deterministic formula:

```
evidence_score = (total_weighted_score - silence_penalty) / max(claim_count, 1)
fit_score      = composite_fit_score  (weighted blend of 4 dimensions)
confidence_pct = (evidence_score × 0.6 + fit_score × 0.4) × 100
```

The LLM is responsible for evidence extraction (Nodes 3–5). The math is responsible for the verdict (Node 6). All thresholds live in `Settings` — not hardcoded in node logic — so recalibration requires only an `.env` change.

**Impact:** Identical input always produces identical confidence and verdict. Threshold miscalibration is visible and fixable. The formula is auditable — every judge, recruiter, or candidate can understand exactly how the number was derived. Reproducibility is a property of the system, not a hope.

---

## Iteration 5 — Bias Audit Node

**From:** Invisible bias in reasoning  
**To:** Explicit first-class bias detection with escalation authority

**Problem:** Every LLM carries the biases in its training data. An AI screening system that does not audit its own reasoning will systematically advantage candidates from certain universities, names that read as majority-demographic, traditional career paths, and prestigious company names — without anyone noticing. This is not a theoretical risk; it is the documented failure mode of deployed AI hiring tools.

**Solution:** `detect_bias` is a standalone node — not a check embedded in `analyze_fit`, but an independent audit of the analysis outputs. It checks for prestige university weighting, name-based demographic inference, disproportionate gap penalisation, non-linear path penalties, and technical school-of-thought bias. When bias is flagged and `escalate_on_bias_flag = True` (default), the verdict is ESCALATE — not just noted in a log.

Two structural defences compound this: `anonymised_name` in `CandidateProfile` strips the candidate's name before analysis begins. Batch-level `cohort_bias_flags` in `CohortAnalysis` check for systematic rejection patterns across a screening batch.

**Impact:** Bias is surface-level visible in the audit trail. Human escalation is triggered when bias is detected. The batch-level check catches patterns that individual candidate analysis would miss. This is not a disclaimer — it is a routing decision.

---

## Iteration 6 — Human Brief

**From:** "Flag for review" (a boolean)  
**To:** Structured actionable brief with specific questions and verification tasks

**Problem:** "This candidate needs human review" is not useful. It tells the recruiter that something is wrong but not what, not how to investigate, and not what to ask. The recruiter opens the CV cold, reads it again, and does their own analysis from scratch. The agent's work has produced no leverage.

**Solution:** The `HumanBrief` schema captures everything the human reviewer needs: what we know (Tier A and strong Tier B claims), what we cannot verify (specific unverifiable claims that are material to the verdict), concrete verification tasks (not "check references" — "check DataCorp's Companies House registration date"), specific interview questions, the single most important question to open with, and the one thing that, if it turns out to be true, would likely disqualify the candidate.

The brief is structured by escalation category — a `critical_contradiction` brief reads differently from an `ambiguous_non_linear_background` brief. The agent's investment in analysis produces a concrete deliverable for the human reviewer.

**Impact:** Human review time is cut significantly. The reviewer starts from structured findings rather than a blank CV. The `first_question` ensures that the most material uncertainty is addressed before the interview proceeds. The `risk_to_probe` ensures that the disqualifying risk is surfaced early.

---

## Iteration 7 — Candidate Feedback

**From:** Zero communication to rejected candidates  
**To:** Dignified, specific feedback for every verdict including rejections

**Problem:** Most AI screening systems are optimised entirely for the recruiter and the company. The candidate is processed, judged, and — if rejected — receives nothing or a form rejection email. Candidates are people in a stressful situation. They have invested time in an application. A system that cannot even tell them one genuine thing they do well is not a complete system.

**Solution:** `candidate_feedback` is a mandatory node that runs for every verdict, including `STRONG_NO`. It produces one `genuine_strength` (schema-enforced: minimum 20 characters, must be specific — "strong Python background" does not satisfy the constraint), one `gap_for_this_role` (specific to the role mismatch, not a generic criticism), and optional `encouragement` when the gap is genuinely closable.

The `verdict_communicated` field uses plain language ("not selected for this role at this time") — the internal codes `STRONG_NO`, `NO` etc. never surface to the candidate.

**Impact:** Every candidate interaction is dignified. Rejected candidates with genuine strengths hear them. Rejected candidates with closable gaps receive actionable direction. The system builds goodwill even in negative outcomes — a strategic advantage that ATS systems never consider.

---

## Iteration 8 — Cohort Ranking

**From:** Individual verdicts in isolation  
**To:** Cross-candidate comparative intelligence

**Problem:** A recruiter screening 50 candidates receives 50 individual verdicts. But the actual hiring question is "who is the best fit from this pool?" Individual verdicts answer "is this candidate good enough?" — not "who is the best candidate?" These are different questions. A YES verdict for 20 candidates does not tell you who to interview first.

**Solution:** The `comparative_rank` node runs after all candidates in a `batch_id` are processed. It produces a `CohortAnalysis` with per-candidate rankings across four independent dimensions (technical, learning velocity, career trajectory, builder strength) plus an overall rank. The hiring manager receives `recommended_for_interview` ordered by overall rank, `escalated_candidates` requiring verification, and `clear_rejections` in one document.

`cohort_bias_flags` at the batch level checks for systematic patterns in rejections — if all rejections share a demographic proxy, that pattern is surfaced before any decision is made.

**Impact:** The hiring manager's question is answered directly. Interview scheduling is driven by cohort rank, not arrival order. Batch-level bias patterns are caught before they become hiring patterns.

---

## Iteration 9 — Trajectory Logging

**From:** Black box (input → output, no visibility into reasoning)  
**To:** Glass box (full audit trail, node-level, append-only)

**Problem:** A system that produces a verdict with no visible reasoning cannot be audited, debugged, or improved. When a verdict is wrong, there is no way to identify which node produced the error. When a threshold needs recalibration, there is no data to guide the adjustment. When a candidate disputes a rejection, there is no audit trail to review.

**Solution:** `log_trajectory` appends a `TrajectoryEntry` for every node execution. Each entry records: the node name, timestamp in East Africa Time, a plain-English reasoning summary (readable by a hiring manager, not just a developer), the evidence keys used, the model called, execution time in milliseconds, and cost in USD. The `operator.add` LangGraph reducer makes the list append-only — no node can overwrite a prior entry.

Privacy is enforced at schema level: `reasoning_summary` must never contain raw CV text, candidate names, or PII — it summarises what was found without reproducing what was said.

**Impact:** Every verdict is fully traceable. Debugging is fast. Calibration is data-driven. The trajectory log is the foundation for the `HumanOverride` feedback loop — when a human disagrees with a verdict, their override (with reason) is recorded against the trajectory. Over time, this builds the correction dataset that improves calibration systematically.

---

## What Remains to Build (Honest About Scope)

SCREEN at v0.1.0 is the schema layer, pipeline architecture, and evaluation framework. The following are designed but not fully implemented within the hackathon scope:

**Full node implementations (Nodes 3–10):** The `parse_candidate` and `tier1_prefilter` nodes are implemented. The remaining nodes have their schemas and contracts defined; the LLM prompt engineering and integration work is the next phase.

**Full evaluation suite (c02–c10):** Only c01 is fully defined. The remaining 9 test candidates and the evaluation runner are specified in the schema and README but require population.

**Production graph wiring:** `screen/agent/graph.py` is designed but not implemented — the LangGraph conditional edge definitions and node wiring require the node implementations to be complete.

**HumanOverride feedback loop:** The schema is defined. The API endpoint or review interface that captures human overrides in production does not exist in v0.1.0.

**Prompt hardening:** Evidence tier classification is only as good as the prompts that instruct the LLM. Prompt adversarial testing (candidates who try to game the tier system) is future work.

**Cost tracking precision:** Token counts in the economics section are estimates based on typical CV and JD lengths. Production cost tracking requires per-call token counting via the Gemini API response metadata.

These are scope limitations, not design limitations. The architecture is built to accommodate all of them without structural change.
