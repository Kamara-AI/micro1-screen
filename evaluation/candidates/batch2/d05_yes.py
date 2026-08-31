"""
WHY: d05 tests the YES tier — a solid, credible candidate who meets all requirements
and shows real production ML experience, but does not reach the STRONG_YES ceiling.
The candidate is competent, not exceptional: outcomes are quantified but modest,
depth is genuine but not outstanding, and domain fit is partial (some fintech but
not specifically credit risk at scale).

HOW: 5 years data science experience, 2 of them in a Kenyan insurtech (adjacent
fintech domain). Has deployed 2 ML models to production. Metrics are present but
mid-range (not KES 1B+ portfolio outcomes). No PhD, no alternative data specifics,
no MLflow — enough to hire, not enough to fast-track. Expected: YES (~72% confidence).
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate meets all three hard requirements with clear evidence: 5 years professional "
    "data science experience, Python proficiency demonstrated across multiple roles, and SQL "
    "proficiency with production usage. Two ML models deployed to production are documented "
    "with measurable outcomes (18% churn reduction, 12% faster claims processing). Fintech "
    "domain experience is adjacent (insurtech, not direct credit risk) rather than exact. "
    "No alternative data (MPESA/utility) experience mentioned. No MLflow or experiment "
    "tracking tooling. No mentorship history. Outcomes are quantified and credible but "
    "not at the scale or sophistication of a STRONG_YES profile. Confidence: 72% YES — "
    "recommend standard interview process."
)

CV_TEXT: str = """
FELIX OMONDI
felix.omondi.data@gmail.com | Nairobi, Kenya | linkedin.com/in/felix-omondi-ds

SUMMARY
Data scientist with 5 years of experience building and deploying machine learning models
in financial services and telecommunications. Strong Python and SQL skills. Comfortable
taking models from exploratory notebooks into production APIs. Looking to deepen my
expertise in credit risk decisioning.

EXPERIENCE

Data Scientist — Jubilee Insurance Kenya, Nairobi
September 2022 – Present (2 years)
- Built a customer churn prediction model (LightGBM) for the retail health insurance
  portfolio; model deployed as a Python Flask microservice consumed by the CRM team;
  churn rate in targeted segment dropped 18% in the 6 months following deployment
- Engineered features from 3 years of policy renewal, claims, and payment records
  using Python (pandas, scikit-learn pipelines); training dataset covered 90,000+
  policyholders
- Built a claims triage model (random forest classifier) that routes incoming claims
  by complexity; reduced average claims processing time by 12% over 4 months
- Write SQL queries against the company's PostgreSQL data warehouse daily for ad hoc
  analysis and model dataset construction

Data Scientist — Safaricom PLC, Nairobi (M-PESA Analytics Team)
April 2020 – August 2022 (2 years 4 months)
- Supported the M-PESA analytics team in building customer segmentation models
  (K-means clustering, logistic regression) for targeted product campaigns
- Wrote Python scripts to automate weekly reporting pipelines; reduced report
  generation time from 8 hours to 45 minutes
- Extracted and cleaned large datasets (10M+ rows) from BigQuery using SQL for
  the team's modelling work
- Produced model performance monitoring reports monthly using Python and matplotlib

Data Analyst — Cellulant Kenya, Nairobi
January 2019 – March 2020 (1 year 3 months)
- Built Excel and Python dashboards for transaction volume reporting across 8
  African markets
- Cleaned and validated payment transaction datasets using pandas for the
  finance reconciliation team
- Wrote basic SQL queries for ad hoc data extraction requests

EDUCATION
BSc, Mathematics — University of Nairobi, 2018
Second Class Upper Honours (GPA: 3.5/4.0)
Relevant coursework: Statistical Inference, Linear Models, Numerical Analysis

Online Training: Coursera Machine Learning Specialisation (Andrew Ng, 2019),
Kaggle Data Science Certificate (2020)

SKILLS
Python: scikit-learn, LightGBM, pandas, NumPy, Flask, matplotlib
SQL: PostgreSQL, BigQuery — complex queries, CTEs, window functions
Tools: Jupyter, Git, Docker (basic), Power BI
Statistics: classification, regression, clustering, model evaluation (AUC, F1, KS)
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
    candidate_id="d05_yes",
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
