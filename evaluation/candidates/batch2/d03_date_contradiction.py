"""
WHY: d03 tests the contradiction detection node on a data science CV. The candidate
is a plausible YES on all experience dimensions — if the contradiction were not
present, this would route to YES without hesitation. The contradiction must cause
escalation, proving SCREEN catches integrity signals, not just keyword signals.

HOW: The CV explicitly states "KreditAI, a startup founded in March 2021 by CEO
David Njihia" in the company description, yet the candidate lists their start date
at KreditAI as January 2019 — a 2-year impossible overlap. The contradiction is
embedded naturally in the CV body, not in a footnote, so the LLM must read and
cross-reference within the same document. Expected: ESCALATE.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "Critical temporal contradiction detected: the candidate claims to have joined KreditAI "
    "in January 2019, but the CV itself states that KreditAI 'was founded in March 2021 by "
    "CEO David Njihia.' A company founded in March 2021 cannot have employed someone from "
    "January 2019 — the claimed tenure predates the company's existence by over 2 years. "
    "Absent this contradiction, the candidate's profile (5 years total experience, credit "
    "risk ML deployment, Python and SQL skills) would comfortably support a YES verdict. "
    "Escalation category: critical_contradiction. The discrepancy must be resolved by a "
    "human recruiter before any hiring decision is made."
)

CV_TEXT: str = """
SAMUEL KIPCHOGE
samuel.kipchoge.ds@gmail.com | Nairobi, Kenya | linkedin.com/in/samuel-kipchoge

SUMMARY
Data scientist with 5 years of experience in machine learning and credit risk modelling
across Kenyan fintech and banking. Strong command of Python and SQL. Experienced in
building scorecard models from alternative data sources including MPESA and utility
payment histories. Thrives in small, high-ownership data teams.

EXPERIENCE

Senior Data Scientist — KreditAI, Nairobi
January 2019 – June 2024 (5 years 6 months)
KreditAI is a credit-scoring startup founded in March 2021 by CEO David Njihia, with
a mission to extend affordable credit to unbanked Kenyan MSMEs using alternative data.
- Built and maintained the core credit scorecard using XGBoost; model scores 12,000+
  loan applications per month and is the primary decisioning tool for KES 800M in
  annual disbursements
- Engineered features from MPESA M-Ledger API, KPLC utility payment data, and
  Safaricom USSD session logs — feature set grew from 18 to 63 variables over 2 years
- Deployed models to production using a Python Flask API containerised with Docker;
  integrated into the loan origination system via REST endpoints
- Ran quarterly model validation cycles and presented results to the credit committee
  and external auditors
- Wrote SQL queries (PostgreSQL) to build training datasets from 3 years of loan
  performance records — 200,000+ borrower records in the primary analysis table

Data Analyst — I&M Bank Kenya, Nairobi
August 2017 – December 2018 (1 year 4 months)
- Built monthly risk reporting dashboards in Python and Excel for the retail lending team
- Extracted and cleaned loan performance data using SQL from the bank's Oracle system
- Supported the credit risk team in portfolio analysis for the KES 6B SME lending book

EDUCATION
BSc, Actuarial Science — University of Nairobi, 2017
Second Class Upper Honours

SKILLS
Python: scikit-learn, XGBoost, pandas, Flask, NumPy
SQL: PostgreSQL, Oracle — complex queries, window functions, stored procedures
Tools: Docker, Git, Jupyter, Power BI, Excel (advanced)
Domain: credit scoring, alternative data, BNPL risk, Kenyan financial markets
"""

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

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="d03_date_contradiction",
    role_seniority="senior",
    role_type="data",
    batch_id="eval_batch_002",
    hard_requirements=[
        "4+ years professional data science or ML experience",
        "Python proficiency",
        "SQL proficiency",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
