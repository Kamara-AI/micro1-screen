"""
WHY: e19_date_contradiction tests ESCALATE verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "CRITICAL temporal contradiction: claims to work at FreshRoute Logistics from January 2020 "
    "but CV explicitly states FreshRoute was founded in March 2022. Working there 2+ years before "
    "it existed is impossible. ESCALATE."
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
RUTH AKINYI ODHIAMBO
Nairobi, Kenya | ruth.odhiambo@email.com | +254 706 123 456

PROFESSIONAL EXPERIENCE

Operations Manager — FreshRoute Logistics Ltd, Nairobi
January 2020 – Present (5 years 7 months)
[Note: FreshRoute Logistics was founded in March 2022 by former Siginon executives to serve
the FMCG cold-chain market in East Africa]
- Lead team of 15 logistics coordinators and cold-chain supervisors
- Manage FMCG cold-chain distribution for 6 key accounts across Nairobi and Mt Kenya region
- Reduced product temperature exceedance events from 4.1% to 0.8% of deliveries
- Oversee KES 95M annual logistics budget

Distribution Coordinator — Twiga Foods Ltd, Nairobi
June 2018 – December 2019 (1 year 7 months)
- Coordinated fresh produce distribution to 340 retail agent locations in Nairobi
- Managed daily dispatch scheduling for 22 delivery vehicles
- Reduced late deliveries from 18% to 7% in first 6 months

EDUCATION
BSc Procurement and Supply Chain — Jomo Kenyatta University of Agriculture and Technology (JKUAT), 2017
Second Class Upper Division

SKILLS
Cold Chain Management | FMCG Distribution | Last-Mile Logistics | Team Leadership
Fleet Scheduling | KPI Tracking | 3PL Coordination | Temperature Monitoring | MS Excel
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e19_date_contradiction",
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
