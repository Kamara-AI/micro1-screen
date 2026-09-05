"""
WHY: d08 tests non-traditional background handling — a self-taught data scientist with
no formal CS degree but strong, verifiable evidence of real ML work. GitHub repos with
stars, named clients with quantified outcomes, a publicly accessible API. This is the
profile that ATS systems kill (no degree checkbox) but SCREEN should surface as YES.
The teaching is: Tier A evidence from a non-traditional background outscores Tier C
claims from a "credential-correct" candidate.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Self-taught data scientist with no formal CS/Stats degree, but strong verifiable evidence: "
    "public GitHub repos with real star counts, a credit scoring API used by 3 named clients, "
    "quantified outcomes across 5 years of freelance ML work. 5 years professional experience "
    "(meets the 4-year requirement). Python + pandas + scikit-learn + XGBoost confirmed in "
    "production deployments. SQL confirmed in project work. The non-traditional background is "
    "not a negative signal — the evidence quality is Tier A (externally checkable repos and "
    "live deployments). Domain alignment is good: credit risk is the core of this candidate's "
    "freelance portfolio. Verdict: YES — strong verifiable evidence despite non-traditional path. "
    "Confidence: ~70%."
)

JOB_DESCRIPTION: str = """
Senior Data Scientist — Credit Risk & ML
PesaWise (Series B, $18M raised), Nairobi (Hybrid)

PesaWise is a Kenyan fintech providing BNPL and micro-lending products to 400,000 MSMEs
across East Africa. We use alternative data (mobile money, utility bills, social graph)
for credit decisioning. Our data team of 8 is building the next generation of our credit
risk models.

THE ROLE
You will own the credit risk models that decide who gets credit and at what limit. This is
a high-stakes ML role: your models directly affect who gets access to capital.

WHAT YOU WILL DO
- Build, validate, and deploy credit risk ML models (scorecard, gradient boosting, neural nets)
- Own feature engineering from alternative data sources (MPESA history, utility payments, USSD logs)
- Conduct A/B tests on model versions and report results to the credit committee
- Mentor 1–2 junior data analysts

REQUIREMENTS
- 4+ years professional data science or ML experience
- Demonstrated experience building and deploying ML models to production (not just notebooks)
- Python proficiency (scikit-learn, XGBoost, pandas)
- SQL proficiency

NICE TO HAVE
- Experience in credit risk, fintech, or regulated financial data
- Experience with alternative data sources in African markets
- MLflow or similar experiment tracking

COMPENSATION
KES 280,000–380,000/month + equity
"""

CV_TEXT: str = """
SYLVIA WANJIKU MWANGI
Nairobi, Kenya | sylvia.mwangi.ml@gmail.com | github.com/sylviawanjiku | sylviawanjiku.dev

ABOUT
Self-taught data scientist with 5 years building and deploying ML models for credit and
financial risk use cases. No formal CS degree — I have a BCom in Finance from Strathmore
University (2018) and retrained through DataCamp, fast.ai, and the Zindi Africa competition
platform. My models run in production and I can point to them.

FREELANCE ML ENGINEERING (2019 — Present, 5 years)

Credit Scoring API — Independent project (live at api.sylviawanjiku.dev)
2021 – Present
- Built and deployed a credit scoring REST API using Python (FastAPI + XGBoost) that
  evaluates creditworthiness from M-PESA transaction history and utility payment records
- Used by 3 Kenyan SACCOs: Elimika SACCO, Baraza Credit, and Jua Kali Finance Ltd
  (combined loan book: KES 340M)
- Model achieves Gini coefficient of 0.71 on holdout set; retrained monthly on new data
- Open-source feature engineering library (github.com/sylviawanjiku/mpesa-features,
  280 GitHub stars); handles M-PESA statement parsing for 12 transaction types

Freelance Data Scientist — Tala Kenya (contract, 6 months)
Jan 2022 – Jun 2022
- Built an alternative data feature store using pandas + PostgreSQL to feed Tala's
  underwriting models; reduced feature computation time from 4.2 hours to 18 minutes
- Wrote SQL pipelines extracting 47 behavioural features from USSD transaction logs
  across 1.2M user accounts

Freelance ML Engineer — Mdundo Music (contract, 4 months)
Aug 2021 – Nov 2021
- Built a recommendation model (matrix factorisation + XGBoost ranker) for music
  content; A/B tested against the rule-based baseline, achieved +14% click-through rate
- Deployed via Flask API on AWS EC2; served 85,000 daily active users

Zindi Africa Competition Record (2019–2021)
- Top 5% finish: "Financial Inclusion in Africa" prediction challenge (14,000 participants)
- Top 8% finish: "Loan Default Prediction" challenge (Zindi × UBA Bank)
- 3 published Kaggle notebooks on African credit risk feature engineering (combined 1,200 views)

EDUCATION
BCom Finance (Second Class Upper) — Strathmore University, Nairobi, 2018
DataCamp Data Scientist Track — completed 2019 (32 courses, certificate)
fast.ai Practical Deep Learning — completed 2020

TECHNICAL SKILLS
Python (pandas, scikit-learn, XGBoost, LightGBM, FastAPI, Flask), SQL (PostgreSQL,
MySQL), MLflow (experiment tracking), AWS (EC2, S3), Git, Docker (basic),
Tableau, R (basic)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="d08_non_traditional_yes",
    role_seniority="senior",
    role_type="data",
    role_description="Senior Data Scientist",
    batch_id="eval_batch_002",
    hard_requirements=[
        "4+ years professional data science or ML experience",
        "Python proficiency",
        "SQL proficiency",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
