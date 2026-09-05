"""
WHY: d01 is the STRONG_YES calibration anchor for batch 2. This candidate
represents the ideal ceiling for the Senior Data Scientist — Credit Risk role.
A system that scores this candidate anything below YES has a broken signal chain.

HOW: PhD in Machine Learning, 6 years of credit risk modelling experience split
across Equity Bank and a Kenyan fintech, production-deployed models with quantified
portfolio outcomes, and every hard requirement met with clear evidence. No inference
required — every claim is supported by concrete, measurable results.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate holds a PhD in Machine Learning and has 6 years of direct credit risk "
    "modelling experience, including 3 years in Kenyan fintech deploying alternative-data "
    "models to production. Quantified outcomes are present in every role: a 23% reduction "
    "in NPL ratio, a KES 1.2B portfolio managed by her models, and A/B tests she ran that "
    "increased approval rates by 14% without increasing default rates. All three hard "
    "requirements are unambiguously met. Mentorship, MLflow usage, and MPESA feature "
    "engineering directly match the nice-to-haves. Confidence: 91%."
)

CV_TEXT: str = """
WANJIKU KAMAU, PhD
wanjiku.kamau@gmail.com | linkedin.com/in/wanjiku-kamau-ds | Nairobi, Kenya
github.com/wkamau-ds

SUMMARY
Machine learning researcher turned industry data scientist with 6 years building and
deploying credit risk models in East African financial markets. PhD in Machine Learning
from Strathmore University (2018). Deep expertise in alternative data — MPESA transaction
history, utility payment records, and USSD behavioural logs. Fluent in Python, SQL, and
MLflow. Comfortable presenting model results to credit committees and regulators.

EXPERIENCE

Senior Data Scientist — Credit Risk, Kopa Digital (Series A, Nairobi)
February 2021 – Present (3 years 6 months)
- Designed and deployed a gradient boosting scorecard (XGBoost) for BNPL credit limits
  on Kopa's MSME product; model is live in production, assessed KES 1.2B in credit
  decisions in the 12 months to June 2024
- Engineered 47 features from MPESA M-Ledger data and KPLC utility payment history;
  Gini coefficient improved from 0.41 (logistic baseline) to 0.63 post-feature expansion
- Ran A/B test across two model versions (Champion/Challenger framework); new model
  increased approvals by 14% with a statistically non-significant change in 90-day default
  rate — result presented to credit committee and approved for full rollout
- Reduced model training and experiment turnaround from 3 days to 4 hours by introducing
  MLflow experiment tracking and a feature store backed by PostgreSQL
- Mentored 2 junior data analysts; one progressed to data scientist role within 14 months
- Built an automated model monitoring dashboard (Python + Grafana) that alerts on PSI > 0.2
  and triggers retraining pipeline within 24 hours

Credit Risk Data Scientist, Equity Bank Kenya — Risk Analytics Division, Nairobi
March 2018 – January 2021 (2 years 11 months)
- Built a Nairobi-market microfinance scorecard using logistic regression and decision tree
  ensembles; contributed to a 23% reduction in 90-day NPL ratio across the MSME portfolio
  (KES 4.3B book) over 18 months
- Automated the monthly credit performance reporting pipeline in Python/pandas; reduced
  analyst hours from 40 hours/month to 6 hours/month
- Wrote complex SQL queries against Equity's Oracle data warehouse to extract 5 years of
  transaction history for 800,000+ borrowers — primary dataset for scorecard development
- Presented quarterly model performance reports to Equity's Credit Risk Committee

Research Assistant (Data Science), Strathmore University @iLabAfrica, Nairobi
2016 – 2018
- Conducted research on machine learning for financial inclusion in East Africa as part of
  PhD programme; published 2 papers in peer-reviewed journals (IEEE Access, Springer FAIA)
- Implemented neural network models (Keras/TensorFlow) for default prediction using
  mobile money proxy variables; dataset sourced from anonymised Safaricom transaction logs

EDUCATION
PhD, Machine Learning — Strathmore University, Nairobi, 2018
Dissertation: "Alternative Data Features for Credit Scoring in Low-Documentation Markets:
Evidence from East Africa" | Supervised by Prof. Ciira wa Maina

BSc, Mathematics and Computer Science — University of Nairobi, 2015
First Class Honours

SKILLS
Python (expert): scikit-learn, XGBoost, LightGBM, pandas, NumPy, Keras, FastAPI
SQL (expert): PostgreSQL, Oracle, BigQuery — complex joins, window functions, CTEs
MLflow, Grafana, Docker, Git, Jupyter, Airflow (basic)
Statistics: logistic regression, survival analysis, hypothesis testing, Gini/KS/PSI
Domain: credit scoring, BNPL risk, alternative data (MPESA, utility, USSD)

PUBLICATIONS
- Kamau, W. et al. (2018). "Mobile Money Transaction Patterns as Proxies for Creditworthiness."
  IEEE Access, Vol. 6, pp. 47821–47833.
- Kamau, W. & Mwangi, J. (2017). "Neural Networks for Credit Scoring in Data-Sparse Markets."
  Springer FAIA Conference Proceedings.
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
    candidate_id="d01_strong_yes",
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
