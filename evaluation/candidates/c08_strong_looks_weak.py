"""
WHY: c08 tests the non-obvious fit detector from the opposite direction to c05.
This candidate has no 'software' in any job title. Five years in operations and
logistics. An ATS would reject immediately — no title match, no degree match.
But a careful recruiter sees: self-taught Python, 3 internal tools shipped and
documented, measurable outcomes, and a clear learning trajectory that ends at a
junior PM role — exactly where her operations expertise becomes an asset.

HOW: The signal is in what she did, not her titles. The learning velocity is
real and documented. SCREEN should surface this as a YES; the non-obvious
fit signal is that operations expertise is a structural advantage for a PM
building supply chain or logistics tooling.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Career changer who looks wrong on paper but is an elite recruiter's YES. Five years in "
    "operations — the domain expertise is directly relevant for a PM role at a logistics company. "
    "Self-taught Python with 3 documented internal automation tools (not toy projects — tools used "
    "by her team, with outcome metrics). Learning velocity is exceptional for a non-traditional "
    "path. Operations background means she already understands the user deeply — she is the user. "
    "ATS would reject on title mismatch. SCREEN should flag as non-obvious fit. Confidence: 71%."
)

CV_TEXT: str = """
SADIA HASSAN ABDI
Nairobi, Kenya | sadia.hassan@outlook.com | github.com/sadia-builds | linkedin.com/in/sadia-hassan-abdi

SUMMARY
Operations professional turned aspiring Product Manager. Five years managing logistics and
supply chain operations at a fast-growing e-commerce company. I taught myself Python over
12 months to automate repetitive parts of my job — and ended up building 3 tools that my
team now relies on daily. I want to move into product management where I can build the
tools that operational teams like mine actually need.

WORK EXPERIENCE

Operations Supervisor — Jumia Kenya, Nairobi
Mar 2022 – Present (2 years 5 months)
- Manage daily fulfilment operations for the Nairobi hub: 800–1,200 orders/day, team of 14
  warehouse staff
- Reduced order picking error rate from 4.2% to 1.1% by redesigning the bin-labelling system
  and introducing a scan-verify step (no tech investment required)
- Built and deployed "RouteBot" — a Python script that auto-generates optimised daily
  delivery routes from the orders spreadsheet, saving 2.5 hours/day of manual dispatcher work
- Created a Google Sheets dashboard (Apps Script + Python backend via webhook) tracking
  real-time hub KPIs; presented to country leadership for the first time during Q3 2023
  review — data adopted in the monthly ops report format

Operations Analyst — Sendy, Nairobi
Aug 2019 – Feb 2022 (2 years 7 months)
- Analysed delivery failure data to identify the top 5 root causes of last-mile failures
  in Nairobi; findings led to a new driver briefing process, reducing failure rate from
  12% to 7.3% in 3 months
- Built "DelayTracker" — a Python + pandas script that automated the weekly SLA compliance
  report, replacing a 4-hour manual Excel process with a 6-minute automated run
- Coordinated vendor onboarding for 40+ logistics partners; reduced onboarding cycle from
  21 days to 8 days by building a self-serve document submission checklist and follow-up
  automation in Zapier

Logistics Coordinator — Twiga Foods, Nairobi
Jan 2019 – Jul 2019 (7 months)
- Coordinated daily cold-chain delivery routes for fresh produce distribution across
  Nairobi's 17 distribution zones
- Tracked delivery performance in Excel; flagged route inefficiencies that reduced fuel
  spend by KES 40,000/month

SELF-DIRECTED LEARNING
Python for Everybody (Coursera / University of Michigan) — Completed 2020
Python Data Analysis with Pandas (Udemy) — Completed 2021
Product Management Fundamentals (Product School, online) — Completed 2023
Introduction to SQL (Mode Analytics) — Completed 2022

PERSONAL PROJECTS
RouteBot (github.com/sadia-builds/routebot): Python route optimisation script for logistics
ops teams — 140 GitHub stars, used by 2 other ops coordinators at different companies who
found it via LinkedIn

EDUCATION
Bachelor of Commerce (Logistics & Supply Chain Management) — University of Nairobi, 2018

SKILLS (TECHNICAL)
Python (pandas, openpyxl, requests), Google Apps Script, SQL (basic), Git, Zapier, Excel
(advanced), Google Sheets (advanced), Notion

SKILLS (OPERATIONAL)
Last-mile logistics, warehouse management, SLA design, vendor management, KPI dashboarding,
process optimisation, root cause analysis
"""

JOB_DESCRIPTION: str = """
Junior Product Manager — Logistics & Operations
Lori Systems (Series B), Nairobi (On-site)

Lori Systems is Africa's leading B2B trucking and logistics platform. We connect cargo owners
to vetted truck operators across East and West Africa. We move 2.4M+ tonnes of cargo annually.

THE ROLE
We need a Junior PM who can own the product for our internal operations tools — the dashboards,
workflow automation, and dispatch interfaces that our logistics coordinators and operations
managers use every day. The best candidate for this role is someone who has been an operations
manager or coordinator, understands the pain deeply, and is now ready to build the tools that
teams like theirs need.

WHAT YOU WILL DO
- Own the product roadmap for our internal ops tooling (2 engineering resources dedicated)
- Run discovery with operations teams across 3 countries (Kenya, Ghana, Nigeria)
- Write clear product specs and user stories that engineers can build from
- Define success metrics for every feature and track them in our analytics stack

REQUIREMENTS
- 2+ years experience in operations, logistics, or supply chain (hard requirement)
- Strong analytical background — you are comfortable with data, not just narratives
- Ability to write clear, structured product documentation

NICE TO HAVE
- Technical background or basic programming skills
- Prior experience as a PM or APM
- Experience with logistics tech or marketplace platforms

COMPENSATION
KES 150,000–200,000/month + performance bonus
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c08_strong_looks_weak",
    role_seniority="junior",
    role_type="product",
    batch_id="eval_batch_001",
    hard_requirements=[
        "2+ years experience in operations, logistics, or supply chain",
        "strong analytical background",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
