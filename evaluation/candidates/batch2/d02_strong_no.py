"""
WHY: d02 is the hard-reject calibration anchor. The candidate is a recent graduate
on a university internship with 1 year of experience. The hard requirement of
"4+ years professional data science or ML experience" is unambiguously unmet.

HOW: CV is written clearly and honestly — this is not a confusing edge case. The
candidate is simply not qualified at the experience level required. Any system that
does not route this to STRONG_NO is failing its hard-requirement check. No ambiguity
is present; the year count is explicit. Expected: STRONG_NO.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Hard requirement breach: the role requires 4+ years of professional data science or "
    "ML experience. The candidate has approximately 1 year of experience, consisting of a "
    "final-year university internship (6 months) and a graduate data analyst role started "
    "in January 2024 (~8 months to August 2024). Total professional tenure is under 1.5 "
    "years. The candidate shows genuine enthusiasm and some Python/SQL exposure, but the "
    "experience gap is 3+ years — this is not a borderline case. Confidence: 96% STRONG_NO."
)

CV_TEXT: str = """
BRIAN OTIENO
brian.otieno2024@gmail.com | Nairobi, Kenya | linkedin.com/in/brian-otieno-data

OBJECTIVE
Enthusiastic and hardworking recent graduate eager to apply my data analysis skills in a
fast-paced fintech environment. I am passionate about financial inclusion and machine
learning and am looking for my first full-time data science role.

EDUCATION
BSc, Statistics and Computer Science — Kenyatta University, Nairobi
Graduated: November 2023 | Second Class Upper Honours (GPA: 3.6/4.0)
Relevant coursework: Machine Learning (R, Python), Database Systems (SQL), Statistical
Modelling, Probability Theory, Data Structures

Final Year Project: "Predicting M-PESA Transaction Churn Using Logistic Regression"
— Built a logistic regression model on a synthetic dataset provided by a lecturer.
— Achieved 74% accuracy on the test set.
— Presented findings to a panel of 4 lecturers.

EXPERIENCE

Graduate Data Analyst (Entry Level) — PeoplePay Africa, Nairobi
January 2024 – Present (~8 months)
- Assist senior analysts in preparing monthly performance dashboards in Power BI
- Write basic SQL queries to pull data from the company's MySQL database for ad hoc reports
- Clean and format datasets in Excel and Python (pandas) for handoff to the analytics team
- Attended two internal training sessions on fintech risk fundamentals

Data Intern — Kenya Revenue Authority (KRA), Nairobi
June 2023 – November 2023 (6 months, final-year internship)
- Supported the data team in formatting and validating CSV exports from the KRA Oracle system
- Wrote 3 SQL queries to extract VAT filing records for the compliance team
- Prepared PowerPoint summaries of monthly compliance statistics for a manager's presentation

SKILLS
Python (beginner-intermediate): pandas, matplotlib, scikit-learn (coursework only)
SQL: basic SELECT, JOIN, WHERE — MySQL, some PostgreSQL exposure
Excel: advanced (pivot tables, VLOOKUP, conditional formatting)
Tools: Power BI (basic), Jupyter Notebook, Git (basic)

INTERESTS
Financial inclusion, machine learning, football analytics, reading about AI trends
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
    candidate_id="d02_strong_no",
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
