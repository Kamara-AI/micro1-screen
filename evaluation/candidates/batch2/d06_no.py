"""
WHY: d06 tests the NO tier — a candidate who technically clears the year count (4 years)
but whose CV is full of low-signal evidence language. "Responsible for", "assisted with",
"participated in", and "supported" language dominates. No quantified outcomes anywhere.
All experience is in academic or research settings — no production system appears in
the work history. Skills are listed but never evidenced in any role description.

HOW: 4 years experience that is all academic/research. No model has been deployed to
production. No metric is cited anywhere. Role language is entirely passive and ownership-free.
The Python and SQL skills are listed but the work history only ever says "used Python
for analysis" without any system, result, or scale. Expected: NO (~35% confidence).
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "The candidate has 4 years of experience, which nominally clears the year threshold, "
    "but the quality of evidence is insufficient for a Senior Data Scientist role. All "
    "experience is in academic or research settings (2 university research roles, 1 NGO "
    "data role) — no production system, no real user impact, no business KPI appears "
    "anywhere in the CV. Every role is described in passive or subordinate language: "
    "'assisted with', 'participated in', 'responsible for analysis under supervision'. "
    "No quantified outcome is present. Python and SQL are claimed but the work context "
    "never rises above 'used for analysis' or 'ran scripts'. No ML model has been "
    "deployed or operationalised. This profile does not demonstrate the production ML "
    "ownership that a Senior role requires. Confidence: 35% YES → recommend NO."
)

CV_TEXT: str = """
PAULINE ACHIENG
pauline.achieng.research@gmail.com | Nairobi, Kenya

SUMMARY
Data science professional with 4 years of experience in research and analytical roles
across academia and the development sector. Passionate about using data for social good.
Experienced in Python, SQL, and statistical modelling.

EXPERIENCE

Research Data Analyst — African Population and Health Research Center (APHRC), Nairobi
February 2022 – Present (2 years 6 months)
- Responsible for data cleaning and preparation of household survey datasets for
  the organisation's health economics research programme
- Participated in the development of statistical analysis plans for 2 research studies
- Used Python (pandas) for data wrangling tasks under the supervision of the
  lead researcher
- Assisted with running regression models in Stata for a study on maternal health
  outcomes in Kisumu county
- Responsible for formatting and proofreading data tables for journal submission
- Supported the senior research team in responding to peer reviewer comments

Research Assistant — Strathmore University, @iLabAfrica, Nairobi
June 2020 – January 2022 (1 year 8 months)
- Participated in a university research project on mobile money adoption patterns
  in rural Kenya
- Assisted with data entry and validation of survey responses collected in
  Kakamega and Kisii counties
- Used SQL to query the project's PostgreSQL database for basic summary statistics
  as directed by the principal investigator
- Contributed to literature review sections for 2 working papers
- Responsible for maintaining the project's data dictionary and codebook

Data Officer — GIZ Kenya (Gesellschaft für Internationale Zusammenarbeit), Nairobi
January 2020 – May 2020 (5 months, contract)
- Supported the M&E team in organising beneficiary data collected from 6 field sites
  across Western Kenya
- Used Excel to clean and reformat survey data before handoff to the analytics team
- Responsible for uploading validated datasets to the project SharePoint site
- Assisted in preparing data visualisations (bar charts, pie charts) in Excel for
  the donor progress report

EDUCATION
MSc, Statistics — University of Nairobi, 2019
Dissertation: "Bayesian Hierarchical Models for Smallholder Crop Yield Prediction"
(Supervisor: Dr. James Mwangi) — desk research and simulation study using R

BSc, Mathematics and Statistics — Kenyatta University, 2017
Second Class Lower Honours

SKILLS
Python: pandas, NumPy, scikit-learn (coursework and occasional research use)
SQL: basic queries, GROUP BY, JOINS — PostgreSQL
R: linear models, ggplot2 (primarily academic use)
Tools: Stata, Excel (advanced), SPSS
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
    candidate_id="d06_no",
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
