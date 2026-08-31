"""
WHY: d04 tests skill_level contradiction detection — a different class of integrity
signal from d03. A candidate who claims expert-level ML skills in a skills section
but whose entire work history contains zero ML activity is either inflating their
skills section or omitting critical job duties. Either way, the discrepancy is
material and cannot be resolved by the screener alone.

HOW: The skills section explicitly reads "Expert: XGBoost, gradient boosting, neural
networks, MLflow, scikit-learn." Every single role description — across 3 roles
spanning 5+ years — mentions only Excel, SQL queries for reporting, pivot tables,
and PowerPoint decks. No model is built, no Python script is written, no experiment
is tracked, no deployment is described anywhere in the work history. The gap between
claimed skill level and demonstrated application is the widest possible. Expected: ESCALATE.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "Critical skill_level contradiction: the skills section explicitly claims expert-level "
    "proficiency in XGBoost, gradient boosting, neural networks, MLflow, and scikit-learn. "
    "However, a complete review of every role description across 3 positions and 5+ years "
    "reveals zero ML activity: all work is described in terms of Excel pivot tables, SQL "
    "SELECT queries for reporting, PowerPoint decks, and data entry validation. No model "
    "is mentioned, no Python script is described, no experiment is tracked, and no "
    "deployment appears anywhere in the work history. The claimed skill level and the "
    "demonstrated work history are irreconcilably inconsistent. Escalation category: "
    "skill_level_contradiction. A human recruiter must probe this directly in interview "
    "before any hiring decision is made."
)

CV_TEXT: str = """
GRACE MUTHONI
grace.muthoni.analytics@gmail.com | Nairobi, Kenya | linkedin.com/in/grace-muthoni

SUMMARY
Results-driven data professional with over 5 years of experience in data analytics and
business intelligence across banking and financial services in Kenya. Strong analytical
background with expertise in machine learning tools and business reporting.

TECHNICAL SKILLS
Expert: XGBoost, gradient boosting, neural networks, MLflow, scikit-learn, Python
Advanced: SQL, Excel, PowerPoint, Power BI
Intermediate: Tableau, JIRA, Confluence

EXPERIENCE

Senior Data Analyst — KCB Bank Kenya, Nairobi
March 2021 – Present (3 years 5 months)
- Prepared monthly retail lending performance reports for the Head of Risk using Excel
  pivot tables and charts; reports distributed to 12 senior stakeholders every month
- Ran SQL queries against the bank's Oracle data warehouse to extract loan book data
  for quarterly regulatory reporting submissions to the CBK
- Maintained and updated a master Excel tracking sheet of 4,500+ active loan accounts,
  including flagging accounts 30, 60, and 90 days past due for the collections team
- Built a PowerPoint dashboard template adopted by the entire risk analytics team,
  saving approximately 3 hours per report cycle
- Validated data entry for new loan applications by cross-referencing against branch
  records — processed approximately 200 applications per month
- Responded to ad hoc data requests from the credit committee by writing SQL SELECT
  queries and formatting results in Excel for presentation

Data Analyst — Cooperative Bank of Kenya, Nairobi
July 2018 – February 2021 (2 years 8 months)
- Produced weekly and monthly lending summaries using Excel pivot tables from
  data exported out of the core banking system (T24)
- Wrote SQL queries to pull disbursement and repayment records for 6 product lines
  from the reporting database
- Prepared slide decks for the monthly credit portfolio review attended by the
  Chief Credit Officer and regional managers
- Reconciled daily transaction reports between the core banking system and the
  Excel-based shadow ledger maintained by the finance team
- Updated a shared SharePoint tracker for collateral documentation status across
  the SME lending book

Business Intelligence Intern — Equity Bank Kenya, Nairobi
January 2018 – June 2018 (6 months)
- Assisted the BI team in formatting and cleaning data exports from the data warehouse
  using Excel
- Prepared summary tables from SQL query results provided by senior analysts
- Updated PowerPoint slides for the weekly senior management briefing pack
- Filed and organised printed loan application documents in the records room

EDUCATION
BSc, Business Information Technology — JKUAT, Nairobi, 2017
Second Class Upper Honours

CERTIFICATIONS
- Microsoft Excel Expert (MOS Certification, 2019)
- Power BI Data Analyst Associate (Microsoft, 2022)
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
    candidate_id="d04_skill_conflict",
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
