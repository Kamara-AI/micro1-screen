"""
WHY: e07_yes tests YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Non-linear: 3yr military logistics (commanded 15-person platoon) + 3yr civilian "
    "Twiga Foods. Combined 6 years, team management in both contexts. Confidence: 68%."
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
SAMUEL KIBET KOECH
Eldoret, Kenya | samuel.koech@email.com | +254 701 901 234

PROFESSIONAL EXPERIENCE

Operations Supervisor — Twiga Foods Ltd, Eldoret Hub
August 2021 – Present (4 years)
- Promoted from Logistics Analyst to Operations Supervisor in 11 months
- Lead team of 11 warehouse and distribution staff at Eldoret regional hub
- Reduced wastage (fresh produce shrinkage) from 8.1% to 3.4% through FIFO enforcement and
  pre-delivery condition checks
- Track daily KPIs: fill rate, shrinkage rate, on-time dispatch, vehicle utilisation

Logistics Platoon Commander — Kenya Army, Corps of Supply and Transport, Nairobi
June 2018 – July 2021 (3 years 1 month)
- Commanded a 15-person logistics platoon supporting a 450-person battalion
- Managed fleet of 12 military transport vehicles — zero unplanned downtime over 3 years
- Controlled KES 4.2M monthly operational logistics budget with zero audit findings across 6 annual audits
- Coordinated supply requisitioning, warehousing, and field distribution for battalion operations

EDUCATION
BBA Business Administration — Moi University, Eldoret, 2017
Second Class Upper Division

SKILLS
Logistics Planning | Platoon and Team Leadership | Warehouse Operations | Fleet Management
Last-Mile Distribution | KPI Tracking | Inventory Management | MS Excel | Supply Requisitioning
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e07_yes",
    role_seniority="senior",
    role_type="operations",
    batch_id="eval_batch_003",
    hard_requirements=[
        "5+ years operations or supply chain management experience",
        "managed a team of 10+ people",
        "degree in business administration, operations management, supply chain, or related field",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
