"""
WHY: c06 is the pure-builder STRONG_YES — a candidate whose track record is
characterised by zero-to-one builds, quantified outcomes on every item, and
a founder-mode side project with real traction. This tests the builder/maintainer
classifier and verifies that SCREEN correctly rewards ownership vocabulary
and outcome evidence over title seniority.

HOW: Serial product builder who started a startup, built an OSS library with
real adoption, and has shipped from zero in every role. The builder signals
are densely present. A maintainer-pattern recruiter might under-value this
candidate; SCREEN should strongly recommend.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Pure builder profile with zero-to-one track record across all roles. Every job entry "
    "contains quantified outcomes with ownership language ('architected', 'launched', "
    "'built from scratch', 'founded'). Side project (Huduma API) has 5,100 GitHub stars "
    "and is used in production by 3 companies. OSS library has 820 stars. Promoted twice, "
    "founded a startup (failed, with documented learning). Career shape is accelerating. "
    "Technical fit for a staff-level builder role at Series A is extremely high. Confidence: 91%."
)

CV_TEXT: str = """
JABARI KAMAU
Nairobi, Kenya / Remote | jabari@hudumaapi.com
github.com/jabari-kamau | linkedin.com/in/jabari-kamau

SUMMARY
Product-obsessed software engineer. I build things from scratch, ship them to users, and
measure what happens. Founded a B2B SaaS (wound down after 18 months, documented learnings
published). Built and maintain Huduma API — an open-source M-Pesa + mobile money abstraction
layer used in production by 3 Kenyan fintechs, 5,100 GitHub stars. I join early-stage
companies to build the first version of things that didn't exist before.

EXPERIENCE

Senior Software Engineer / Tech Lead — Lipa Later, Nairobi
Nov 2022 – Present (1 year 9 months)
- Built the first version of the merchant API from scratch (Node.js + PostgreSQL); onboarded
  the first 50 merchants in 6 weeks from kickoff
- Architected the instalment calculation engine that now powers 35,000+ active loan accounts
- Led a 3-person squad through a 4-month platform migration from a monolith to a service-oriented
  architecture; zero downtime during the cut-over window
- Designed and shipped the fraud pre-screening integration (ML model + rules engine) that
  reduced default rate among new merchant cohorts from 9.1% to 5.4% in the first 6 months
- Promoted from SWE → Tech Lead in 10 months

Software Engineer — Twiga Foods, Nairobi
Mar 2020 – Oct 2022 (2 years 8 months)
- Built the order dispatch system (zero to one) that coordinates 240+ daily delivery routes;
  now handles KES 3.2B/year in B2B food distribution
- Integrated real-time GPS tracking for the driver fleet (40+ vehicles); reduced failed
  deliveries from 11% to 3.8%
- Built the supplier onboarding portal (React + Django REST); reduced onboarding time from
  14 days (manual) to 3 days (self-serve)
- Promoted from Junior → Software Engineer in 14 months

Founder / CTO — Senti (failed startup), Nairobi
Jan 2019 – Feb 2020 (14 months)
- Built the MVP of an NLP-powered customer feedback aggregator for Kenyan SMEs
- Reached 12 paying customers before running out of runway
- Key learnings published at medium.com/@jabari-kamau/senti-postmortem (1.2K reads)

OPEN SOURCE
Huduma API (github.com/jabari-kamau/huduma-api)
- Unified abstraction layer for M-Pesa, Airtel Money, and MTN Mobile Money APIs
- 5,100 GitHub stars, 87 contributors, used in production by Koa Health, Pezesha, and one
  undisclosed bank
- Published as npm package: 8,400 monthly downloads

node-safaricom (github.com/jabari-kamau/node-safaricom)
- Daraja API v2 client library for Node.js
- 820 GitHub stars, 22 contributors, 3,100 monthly npm downloads

EDUCATION
BSc Computer Science — University of Nairobi, 2018
Coursework: Algorithms, Operating Systems, Databases, Software Engineering

SKILLS
Node.js (TypeScript), Python, PostgreSQL, Redis, Kafka (basic), Docker, AWS (ECS, RDS,
S3, Lambda), Terraform (basic), React (proficient), REST + GraphQL API design,
Jest, pytest, Datadog, mobile money APIs
"""

JOB_DESCRIPTION: str = """
Staff Engineer — Core Product
Koa Health (Series A, $31M raised), Nairobi (Hybrid)

Koa Health is building digital mental health tools for East Africa. Our app has 280,000
registered users across Kenya, Uganda, and Tanzania. We process 1.2M therapy session
bookings annually. We are 28 people; engineering team is 9.

THE ROLE
This is a Staff IC role with a mandate to build. You will own our most foundational
product components — the session booking engine, the therapist matching algorithm, and
the payment infrastructure. We need someone who has built core systems before, not someone
who has maintained them.

WHAT YOU WILL DO
- Own and evolve the therapist matching engine (currently rule-based; roadmap to ML-assisted)
- Build the next generation of our session scheduling infrastructure (from current monolith
  to a service that supports 5x current volume)
- Define engineering standards adopted by the full 9-person team
- Contribute to technical hiring decisions (interview loop design, bar calibration)

REQUIREMENTS
- 5+ years software engineering, with demonstrable zero-to-one builds
- Strong Node.js or Python backend experience
- Track record of shipping and iterating in a resource-constrained environment
- Comfortable owning the full lifecycle: design → build → operate → improve

STRONG PREFERENCE
- Prior experience in health tech, fintech, or other regulated product domains
- Open source contributions with real-world adoption
- Founder or early-stage startup experience (success OR failure — we care about the learning)

COMPENSATION
KES 350,000–480,000/month + equity (0.1–0.3%)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c06_builder_signal",
    role_seniority="staff",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "5+ years software engineering",
        "demonstrable zero-to-one builds",
        "Node.js or Python backend experience",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
