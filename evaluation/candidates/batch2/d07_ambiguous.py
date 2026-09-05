"""
WHY: d07 tests AMBIGUOUS routing — the case where the CV is present but analytically
empty. Role titles exist, company names exist, skills are listed, but there are no
dates on any role (so experience length and trajectory are unknown), no quantified
outcomes, and no description of what was actually built or deployed. The data is
technically present but provides no basis for a confident verdict either way.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "CV contains role titles and company names but no dates on any role (experience length "
    "is unknown), no quantified outcomes, skills listed but never connected to actual work "
    "in any role description. Cannot assess: years of experience, whether Python/SQL were "
    "used professionally, whether any ML models were deployed, or career trajectory. The "
    "correct output is AMBIGUOUS — recommend a phone screen to fill the evidence gaps. "
    "Confidence: ~48%."
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
BRIAN OTIENO OMONDI
Kisumu, Kenya | b.otieno.data@gmail.com

WORK HISTORY

Data Scientist — NovaTech Analytics
Responsibilities: Data analysis and machine learning projects for clients.

Junior Data Analyst — AfricaData Solutions
Responsibilities: Data processing, reporting, and analysis support.

Data Science Intern — KenyaInsight Research
Responsibilities: Assisted with data collection and analysis tasks.

Business Intelligence Analyst — Savanna Digital
Responsibilities: BI reporting and dashboard development for business units.

TECHNICAL SKILLS
Python, R, SQL, pandas, scikit-learn, TensorFlow, Tableau, Power BI,
Excel, MySQL, PostgreSQL, Git, Jupyter Notebook

EDUCATION
Bachelor of Science in Statistics
University of Nairobi

ADDITIONAL INFORMATION
Passionate about data science and machine learning. Quick learner.
Available to start immediately. References available on request.
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="d07_ambiguous",
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
