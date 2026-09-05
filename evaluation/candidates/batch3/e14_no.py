"""
WHY: e14_no tests NO verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "5 years in financial operations (treasury, payment ops). 'Operations Manager' title "
    "but all work is banking/finance. No supply chain, no logistics, no distribution. Confidence: 22%."
)

JOB_DESCRIPTION: str = """
Senior Operations Manager — East Africa Expansion
Zawadi Foods Ltd, Nairobi (with regional travel)

Zawadi Foods is a Kenyan FMCG manufacturer (cooking oils, maize flour, breakfast cereals)
with 800 employees and KES 4.2B annual revenue. We are expanding distribution from Nairobi
to Western, Coastal, and Rift Valley regions.

THE ROLE
Design and run operational infrastructure for our regional expansion: warehousing,
last-mile distribution, 3PL partnerships, and field team management.

WHAT YOU WILL DO
- Lead a team of 15-20 field operations coordinators and warehouse supervisors
- Own end-to-end supply chain for 3 new distribution regions
- Negotiate and manage 3PL and logistics partner contracts
- Build and track KPIs: fill rate, on-time delivery, shrinkage, cost-per-unit-delivered
- Report weekly to the COO on expansion milestones

REQUIREMENTS
- 5+ years operations or supply chain management experience
- Proven experience managing a team of 10+ people directly
- Degree in Business Administration, Operations Management, Supply Chain, or related field

NICE TO HAVE
- FMCG or consumer goods operations experience
- ERP experience (SAP, Oracle, Odoo)
- Experience opening new distribution routes or warehouses from scratch

COMPENSATION
KES 180,000-250,000/month + vehicle + medical
"""

CV_TEXT: str = """
VIVIAN CHEBET RUTO
Nairobi, Kenya | vivian.ruto@email.com | +254 726 678 901

PROFESSIONAL EXPERIENCE

Payment Operations Manager — Equity Bank Kenya Ltd, Nairobi
November 2020 – Present (4 years 9 months)
- Lead team of 11 payment analysts and settlement officers
- Oversee KES 3.2B daily payment volumes across mobile banking, RTGS, and EFT channels
- Implement operational risk controls for Equitel mobile banking platform
- Manage SLA compliance for payment processing — 99.7% uptime maintained
- Coordinate with Central Bank of Kenya on regulatory reporting for payment systems

Treasury Operations Senior Analyst — KCB Group, Nairobi
July 2018 – October 2020 (2 years 4 months)
- Managed interbank money market placements and forex settlement
- Performed daily cash reconciliation across 14 nostro accounts
- Prepared daily treasury position reports for Head of Treasury
- Monitored compliance with CBK liquidity ratio requirements

EDUCATION
BCom Finance — University of Nairobi, 2017
CPA(K) Part II

SKILLS
Payment Systems Operations | Treasury Management | Forex Settlement | Reconciliation
Operational Risk | CBK Regulatory Reporting | MS Excel | Banking Systems | Team Leadership
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e14_no",
    role_seniority="senior",
    role_type="operations",
    role_description="Senior Operations Manager",
    batch_id="eval_batch_003",
    hard_requirements=[
        "5+ years operations or supply chain management experience",
        "managed a team of 10+ people",
        "degree in business administration, operations management, supply chain, or related field",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
