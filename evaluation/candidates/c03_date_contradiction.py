"""
WHY: c03 tests the contradiction detection node — the most critical differentiator
between SCREEN and a naive keyword scorer. A strong CV with one critical temporal
contradiction should route to ESCALATE, not YES, because the contradiction materially
calls into question the candidate's honesty or accuracy.

HOW: The contradiction is specific and verifiable: candidate claims to have worked at
DataSync from 2018–2022, but also states in their cover note / CV summary that DataSync
"was founded in 2019 by CEO Marcus Farrell." This is a one-year impossible overlap.
Without this contradiction the candidate would be a solid YES (6 years exp, good signals).
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "Critical temporal contradiction: candidate claims 'Senior Engineer at DataSync 2018–2022' "
    "but elsewhere on the CV states DataSync was 'founded in 2019 by CEO Marcus Farrell, who "
    "recruited me as employee #3.' These two claims cannot both be true — DataSync cannot have "
    "employed a Senior Engineer in 2018 if it was founded in 2019. This is either a date error "
    "or scope inflation (claiming earlier tenure than actual). Without this contradiction the "
    "candidate's profile would warrant a YES — strong trajectory, good technical signals, "
    "appropriate seniority. Escalation category: critical_contradiction."
)

CV_TEXT: str = """
PRIYA NAIR
priya.nair.eng@gmail.com | linkedin.com/in/priya-nair-swe | Bangalore, India (Open to remote)

SUMMARY
Software engineer with 6 years building data infrastructure and real-time analytics platforms
for fast-growing startups. Joined DataSync as employee #3 when CEO Marcus Farrell founded the
company in 2019 — grew with it from seed to Series A. Strong Python and Spark background.
Shipped a data pipeline that processes 15TB/day for a Series A analytics company.

EXPERIENCE

Senior Data Engineer — DataSync Analytics, Bangalore
2018 – 2022 (4 years)
- Led the design of DataSync's core ingestion pipeline using Apache Kafka and Spark Streaming;
  pipeline handles 15TB/day at peak
- Built the customer-facing metrics API (Python/FastAPI) used by 80+ enterprise clients
- Reduced end-of-day reconciliation job runtime from 6 hours to 40 minutes via partition pruning
  and predicate pushdown optimisation
- Mentored 2 junior data engineers; both moved into senior roles within the company
- Managed migration from on-prem Hadoop cluster to AWS EMR, saving $180K/year in infra costs

Data Engineer — Zepto Analytics, Mumbai
2016 – 2018 (2 years)
- Built ETL pipelines for e-commerce transaction data (Python, Airflow, Redshift)
- Automated reporting for 12 business dashboards, saving ~15 hours/week of analyst time
- Introduced data quality monitoring using Great Expectations; caught 3 critical upstream
  data issues before they reached production dashboards

EDUCATION
B.Tech Computer Science — National Institute of Technology Trichy, 2016
Graduated with distinction (8.7/10 CGPA)

SKILLS
Python, Apache Spark, Kafka, Airflow, Redshift, AWS (EMR, S3, Glue), dbt, FastAPI,
PostgreSQL, Docker, Terraform (basic), Great Expectations, Pandas

PROJECTS
- Contributed to Apache Airflow (3 merged PRs — provider improvements)
- Technical blog: medium.com/@priya-nair-data (12 posts on Spark optimisation)
"""

JOB_DESCRIPTION: str = """
Senior Data Engineer — Real-Time Analytics
Flowmetrics (Series A, $18M raised), Bangalore / Remote

Flowmetrics builds real-time analytics infrastructure for D2C brands. Our platform ingests
event streams from 200+ brands and produces sub-second insights dashboards. We are 22
engineers and growing.

THE ROLE
You will own the reliability and performance of our data ingestion and transformation layer.
This is a hands-on senior IC role — you will design, build, and operate the pipelines that
our customers depend on for business-critical reporting.

WHAT YOU WILL DO
- Design and maintain real-time ingestion pipelines (Kafka + Spark Streaming / Flink)
- Build and own our dbt transformation layer for 50TB+ monthly data volume
- Set observability standards for the data platform (lineage, quality, latency SLAs)
- Mentor 1–2 junior data engineers

REQUIREMENTS
- 4+ years data engineering experience
- Production experience with Kafka, Spark, or Flink
- Python proficiency (data engineering context)
- Experience on AWS data stack (EMR, Glue, S3, or equivalent)

NICE TO HAVE
- dbt experience
- Open source contributions to data tooling
- Prior startup experience

COMPENSATION
₹28–40 LPA + equity
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c03_date_contradiction",
    role_seniority="senior",
    role_type="data",
    batch_id="eval_batch_001",
    hard_requirements=[
        "4+ years data engineering experience",
        "production Kafka or Spark experience",
        "Python proficiency",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
