# SCREEN Screening Report

**Candidate ID:** `c04_skill_conflict`  
**Role:** Mid Engineering  
**Screened:** 2026-08-31T12:53:35.346662+03:00  
**Pipeline:** SCREEN v0.1.0 — Structured Candidate Reasoning and Evaluation Engine

---

## ⚠ Verdict: ⚠ ESCALATE — HUMAN REVIEW REQUIRED

**Confidence:** [████████████░░░░░░░░] 60.6%

> **Why escalated:** Critical contradiction detected in the candidate's profile. A human reviewer must verify before any decision is made.

### Primary Evidence

- • Contradiction (critical): The candidate claims expertise in Kubernetes and Terraform, but there is no evidence of these skills being applied in any of the roles listed.
- • Silence flag (high): Quantified outcomes for senior role
- • Probe required: What specific experience do you have with Kubernetes and Terraform in production environments?

### External Claim Verification

| Claim | Tier | Change | Verified By | Finding |
|-------|------|--------|-------------|---------|
| Created a customer-facing web portal for S... | B | — | Web Search | Web search returned no results. Claim remains at current tier. |

---

## Candidate Strengths & Gaps

**Strength:** Your experience building and maintaining the product catalogue API with Django REST Framework, alongside developing React-based dashboards and customer portals, demonstrates strong full-stack development capabilities.

**Gap for this role:** This role requires specific experience with ML pipelines and infrastructure management, including areas like Kubernetes and Terraform in production, which were not evident in your profile. Additionally, quantifying the impact of your previous work would strengthen future applications.

**Next step:** To strengthen your profile for similar roles in the future, consider seeking opportunities to gain hands-on experience with ML infrastructure and MLOps, and focus on quantifying the outcomes and impact of your projects.

---

## ⚠ Escalation Brief — Human Review Required

**Escalation category:** `critical_contradiction`

> The candidate has been flagged due to a critical contradiction regarding their claimed expertise in Kubernetes and Terraform, which is not supported by their listed experience. A human review is necessary to clarify these discrepancies before making a hiring decision.

### What We Know

- Built and maintained the product catalogue API using Django REST Framework at Retail Orbit (2022-10 — Present).
- Developed the React-based admin dashboard for warehouse staff at Retail Orbit (2022-10 — Present).
- Created a customer-facing web portal for SME loan applications using Django and React at BizConnect Africa (2021-03 — 2022-09).
- Integrated M-Pesa payment flow via Daraja API at BizConnect Africa (2021-03 — 2022-09).
- Managed the MySQL database schema for loan application records at BizConnect Africa (2021-03 — 2022-09).
- Claims expertise in Python, Kubernetes, Terraform, and ML pipelines (Kubeflow, MLflow) as stated in skills section.
- Claims proficiency in Django, React, PostgreSQL, MySQL, and Redis as stated in skills section.

### What We Cannot Verify

- The candidate's claimed expertise in Kubernetes and Terraform is not evidenced by their work history, which is critical for assessing their fit for the role.
- The temporal overlap of the candidate's role at Retail Orbit with their career start date raises questions about the company's founding date and the candidate's timeline.

### Verification Tasks

1. Check LinkedIn for the founding date of Retail Orbit to verify the candidate's employment timeline.
2. Search for any public repositories or contributions related to Kubernetes and Terraform that the candidate may have made on GitHub or similar platforms.

### Open the Interview With This Question

> Can you walk me through your experience with Kubernetes and Terraform, specifically in production environments?

### Primary Risk to Probe

> If the candidate cannot provide concrete examples of their experience with Kubernetes and Terraform, it would likely disqualify them for this role.

### Suggested Interview Questions

1. What specific experience do you have with Kubernetes and Terraform in production environments?
2. Can you provide examples of how you've contributed to ML infrastructure or MLOps?
3. What quantifiable outcomes can you share from your previous roles that demonstrate your impact?
4. How do you stay updated with new technologies and frameworks in your field?
5. Can you describe a challenging project you worked on and the role you played in its success?

---

## Pipeline Audit Trail

| Step | Summary | Duration | Model | Cost |
|------|---------|----------|-------|------|
| `structural_precheck` | Structural precheck passed. No explicit year contradiction found in... | 0ms | deterministic | $0.00000 |
| `parse_candidate` | Parsed CV into structured profile. Found 5 roles, 21 stated skills,... | 4851ms | openrouter:google/gemini-2.5-flash-lite | $0.00008 |
| `tier1_prefilter` | All 4 hard requirement(s) satisfied. Candidate passes Tier 1 pre-fi... | 0ms | deterministic | $0.00000 |
| `extract_evidence` | Extracted 15 evidence claims (0 Tier A, 8 Tier B, 7 Tier C, 0 Tier ... | 11447ms | openrouter:openai/gpt-4o-mini | $0.00286 |
| `verify_claims` | Verified 1 claim(s) using external tools. 0 claim(s) upgraded to Ti... | 679ms | deterministic | $0.00000 |
| `analyze_fit` | Multi-dimensional fit analysis complete. Technical fit: 0.30. Exper... | 5880ms | openrouter:openai/gpt-4o-mini | $0.00296 |
| `detect_bias` | Bias audit complete. I reviewed the FitAnalysis for cognitive biase... | 1482ms | openrouter:openai/gpt-4o-mini | $0.00099 |
| `make_decision` | Deterministic decision. Evidence score: 0.789 (weighted claims − si... | 0ms | deterministic | $0.00000 |
| `build_human_brief` | Human brief generated for escalated candidate. Escalation category:... | 4485ms | openrouter:openai/gpt-4o-mini | $0.00182 |
| `candidate_feedback` | Candidate feedback generated for verdict: ESCALATE. Genuine strengt... | 1783ms | openrouter:google/gemini-2.5-flash-lite | $0.00004 |
| `comparative_rank` | Only 1 candidate(s) in batch 'eval_batch_001'. Need ≥2 for comparat... | 0ms | deterministic | $0.00000 |

**Total pipeline cost:** $0.0088  
**Total pipeline time:** 30607ms  
**Nodes executed:** 11

---

*Report generated by SCREEN — Structured Candidate Reasoning and Evaluation Engine*  
*micro1 Agentic Workflows Hackathon 2026*