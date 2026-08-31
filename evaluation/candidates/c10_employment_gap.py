"""
WHY: c10 tests the employment gap handling and bias detection logic. A 3-year
gap is a genuine data point that many systems (and humans) apply bias to —
automatically assuming the worst. SCREEN should: (1) detect the gap, (2) read
the explanation provided on the CV, (3) evaluate the before-gap and after-gap
trajectory, and (4) flag the gap-bias risk to the human reviewer.

HOW: Strong trajectory before the gap (two promotions, quantified outcomes).
The gap is 2020–2023 with a clear, specific explanation: primary caregiver for
an ill parent. Strong return trajectory after the gap. The verdict is YES with
a bias check flag noting the gap should not be used as a rejection criterion.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Employment gap 2020–2023 is fully explained (primary caregiver) and should not be weighted "
    "negatively. Pre-gap trajectory: promoted twice in 4 years, quantified outcomes in both roles, "
    "senior-level responsibilities. Post-gap return: immediately returned at senior level, shipped "
    "a major product in first 18 months. Career is 7 years total (excluding gap), appropriate for "
    "a senior SWE role. Verdict: YES — strong pre/post gap track record. Bias check should flag "
    "caregiver gap bias risk and note that this gap is explained, specific, and should not reduce "
    "the score. Escalation note: human reviewer should be aware of bias risk in subsequent "
    "interview steps, particularly if gap is raised by an interviewer without a clear technical "
    "reason. Confidence: 74%."
)

CV_TEXT: str = """
ELIZABETH WANJIKU MAINA
Nairobi, Kenya | elizabeth.maina.swe@gmail.com | linkedin.com/in/elizabeth-maina-swe
github.com/wanjiku-builds

CAREER NOTE
Between 2020 and 2023 I was a full-time primary caregiver for my mother, who was undergoing
treatment for Stage III breast cancer. She has made a full recovery. During this period I
maintained my technical skills through part-time open-source contributions and self-directed
study. I returned to full-time employment in May 2023.

EXPERIENCE

Senior Software Engineer — M-KOPA Solar, Nairobi
May 2023 – Present (1 year 3 months)
- Joined as Senior SWE; own the customer collections API serving 650,000 active accounts
  across Kenya, Uganda, and Ghana
- Shipped a retry logic redesign that improved payment recovery rate by 11 percentage points
  (from 67% to 78% on first retry attempt), recovering KES 180M/month in previously
  uncollected payments
- Led a 3-person squad migration of the collections service from a monolith to an async
  event-driven architecture (Kafka + Python workers); reduced p95 processing time from
  4.2 seconds to 340ms
- Conducted 8 technical interviews in the past 6 months; improved offer acceptance rate
  from 60% to 83% by introducing structured take-home project rubrics

Software Engineer II — Equity Bank (Technology Division), Nairobi
Jan 2018 – Feb 2020 (2 years 2 months)
- Promoted from Software Engineer I to SWE II in 16 months
- Built the first version of the Equity EazzyBanking API used by 14 third-party fintech
  integrations; API processed KES 2.3B in transactions in first year of operation
- Reduced critical payment API error rate from 0.8% to 0.09% by identifying and fixing
  a race condition in the ledger update sequence
- Implemented automated regression test suite (pytest); reduced regression testing cycle
  from 3 days to 4 hours before each monthly release

Software Engineer I — Cellulant, Nairobi
Mar 2016 – Dec 2017 (1 year 10 months)
- Promoted to SWE I from Graduate Trainee in 4 months (standard pathway: 12 months)
- Built 3 payment notification handlers for Visa, Mastercard, and Airtel Money webhooks
- Maintained and extended the PHP-based merchant dashboard; handled 40+ merchant accounts

Graduate Trainee — Cellulant, Nairobi
Nov 2015 – Feb 2016 (4 months)

CAREER BREAK — PRIMARY CAREGIVER
March 2020 – April 2023 (3 years 2 months)
My mother was diagnosed with breast cancer in January 2020. I made the decision to become
her primary caregiver through treatment, which required me to step back from full-time
employment. During this period: completed AWS Solutions Architect Associate certification
(2021), contributed 4 merged PRs to the python-mpesa open-source library, and completed
a 6-week online course in Kafka fundamentals.

EDUCATION
BSc Computer Science — Jomo Kenyatta University of Agriculture and Technology, 2015
Second Class Honours (Upper Division)

CERTIFICATIONS
AWS Solutions Architect Associate (2021, valid) — Credly badge: credly.com/badges/ew-maina

SKILLS
Python (expert), PHP (proficient), Kafka, PostgreSQL, MySQL, Django REST Framework,
Redis, Docker, AWS (ECS, RDS, SQS, Lambda), pytest, Git, OpenTelemetry (basic)

OPEN SOURCE
python-mpesa contributor (github.com/safaricom/python-mpesa): 4 merged PRs — webhook
validation utilities and error handling improvements
"""

JOB_DESCRIPTION: str = """
Senior Software Engineer — Financial Infrastructure
PesaLink, Nairobi (Hybrid)

PesaLink is Kenya's interbank payment switch, regulated by the Central Bank of Kenya.
We process 2.4M transactions/day across 40 member banks. Our engineering team of 22
is rebuilding our core transaction processing layer over the next 18 months.

THE ROLE
You will own components of our core payment infrastructure — the settlement engine,
exception handling pipeline, and API layer used by 40 member banks. This is a high-stakes
engineering environment: correctness and reliability are more important than speed of delivery.

WHAT YOU WILL DO
- Own the settlement reconciliation service (Python + PostgreSQL)
- Design and implement exception handling for failed or disputed transactions
- Build and maintain APIs consumed by 40 member bank integrations
- Participate in the 24/7 on-call rotation (2 weeks/quarter)

REQUIREMENTS (hard)
- 5+ years software engineering experience
- Financial services or payment systems experience
- Python proficiency at senior level
- Experience with high-availability systems (99.9%+ uptime SLA)

WHAT WE ARE LOOKING FOR
- Candidates who have worked on money-movement systems — not just web apps
- Evidence of owning reliability improvements (not just feature shipping)
- Comfortable in a highly regulated, audit-heavy environment

COMPENSATION
KES 280,000–380,000/month + benefits (medical, pension, performance bonus)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c10_employment_gap",
    role_seniority="senior",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "5+ years software engineering experience",
        "financial services or payment systems experience",
        "Python proficiency at senior level",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
