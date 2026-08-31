"""
WHY: c01 is the STRONG_YES calibration anchor. Every evaluation suite needs a
clear positive reference — a candidate so well-matched that any reasonable
system should score them highly. If SCREEN misses this, the confidence formula
is broken, not the candidate.

HOW: Senior SWE with 8 years experience, two promotions at brand-name companies,
quantified outcomes in every role, active OSS contributions. Applying to a
Senior SWE role at a Series B fintech — the match is strong across all dimensions.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate has 8 years of progressive backend engineering experience with two documented "
    "promotions at well-known companies (Stripe, then Monzo), quantified outcomes in every role, "
    "active open-source contributions with measurable adoption, and direct fintech domain experience. "
    "All three hard requirements are met. The technical depth, career trajectory, and builder "
    "signals are exactly what a Series B fintech Senior SWE role demands. Confidence: 87%."
)

CV_TEXT: str = """
AMARA OSEI-BONSU
GitHub: github.com/aosei-bonsu | LinkedIn: linkedin.com/in/amara-ob
London, UK | amara.ob@protonmail.com

SUMMARY
Backend-first software engineer with 8 years building payment infrastructure, fraud detection
pipelines, and developer-facing APIs at fintech companies. Two promotions in 5 years at
Stripe. Shipped features that process $2B+ annually. Maintain two open-source Python libraries
with 1,400+ combined GitHub stars.

EXPERIENCE

Senior Software Engineer — Monzo Bank, London
Jan 2022 – Present (2 years 8 months)
- Redesigned the real-time fraud scoring service to handle 40K TPS (from 12K), enabling
  Monzo to process Black Friday 2023 peak load without throttling for the first time
- Led a 4-person squad to migrate 11 legacy card-processing microservices from Python 2.7
  to Python 3.11, reducing production incident rate by 34% over 6 months post-migration
- Architected a new event-sourced ledger reconciliation service in Go; cut overnight batch
  reconciliation time from 4h 20m to 23 minutes
- Mentored 3 junior engineers; two promoted to mid-level within 18 months

Software Engineer II → Senior Software Engineer — Stripe, San Francisco / Remote
Mar 2017 – Dec 2021 (4 years 10 months)
- Promoted from SWE II to Senior SWE in 22 months (median at Stripe: 36 months)
- Owned the Radar fraud rules engine API surface — 12K merchant integrations, 99.97% uptime
  over 24 months
- Built the self-serve rules testing sandbox that reduced merchant onboarding time from
  avg. 11 days to 3 days; feature shipped to GA in Q4 2019
- Reduced Radar API p99 latency from 280ms to 47ms by replacing synchronous DB reads with
  a pre-computed feature cache (Redis); presented approach at StripeConf 2020
- Wrote the internal Python SDK used by 8 internal teams for Kafka event consumption

Software Engineer — Paystack, Lagos (acquired by Stripe 2020)
Aug 2015 – Feb 2017 (1 year 6 months)
- Built the first version of the bulk transfer API, which handled KES 500M+ in disbursements
  in its first 6 months
- Implemented idempotency keys across 6 payment endpoints, eliminating a class of duplicate
  payment bugs that had caused 3 customer escalations per week
- Introduced structured logging (structlog) across the backend; reduced mean time to diagnose
  production incidents from 45min to 12min

OPEN SOURCE
- pyfixtures (github.com/aosei-bonsu/pyfixtures): Pytest fixture helper for async database tests
  — 820 stars, 47 contributors, used by Monzo internal test suite
- redis-lock-py (github.com/aosei-bonsu/redis-lock-py): Distributed lock implementation for Python
  — 610 stars, published on PyPI, 14K monthly downloads

EDUCATION
BSc Computer Science — University of Ghana, Accra, 2015
Relevant coursework: Distributed Systems, Algorithms, Operating Systems

SKILLS
Python (expert), Go (proficient), Kafka, Redis, PostgreSQL, Kubernetes, Terraform,
AWS (ECS, RDS, ElastiCache), gRPC, OpenTelemetry, Datadog, pytest, structlog
"""

JOB_DESCRIPTION: str = """
Senior Software Engineer — Payments Infrastructure
ClearLedger (Series B, $42M raised), London (Hybrid)

ClearLedger is building the financial operating system for SMEs across East Africa and the UK.
We process £180M/month in cross-border payments. We are Series B (closed Jan 2024) and scaling
our engineering team from 18 to 35 engineers over the next 12 months.

THE ROLE
You will own core components of our payment processing pipeline — from API design through to
ledger consistency guarantees. This is a high-ownership role: you will ship independently, review
your peers' most complex PRs, and contribute to architecture decisions for systems handling
millions of transactions per month.

WHAT YOU WILL DO
- Design and build payment APIs used by 3,000+ SME customers
- Own the reliability and performance of our real-time settlement service (currently at 8K TPS,
  targeting 50K TPS by end 2025)
- Lead technical design for your squad's quarterly roadmap
- Mentor 1–2 engineers below your level

REQUIREMENTS (hard)
- Minimum 5 years backend engineering
- Experience with financial systems or regulated data handling
- Python or Go proficiency — we use both

WHAT WE ARE LOOKING FOR
- Quantified track record of improving system performance or reliability
- Experience designing for scale, not just shipping features
- Comfort in a high-autonomy, low-process environment (we are post-PMF, pre-scale)

COMPENSATION
£90,000–£115,000 base + equity (0.05–0.15%) + benefits
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c01_strong_yes",
    role_seniority="senior",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "minimum 5 years backend engineering",
        "experience with financial systems or regulated data",
        "Python or Go proficiency",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
