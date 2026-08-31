"""
WHY: e18_strong_no tests STRONG_NO verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "7 years warehouse and logistics experience — would otherwise be competitive. "
    "No degree mentioned anywhere. Hard requirement for degree not met. Hard-reject. Confidence: 100%."
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
STEPHEN KAMAU NJUGUNA
Nairobi, Kenya | stephen.njuguna@email.com | +254 732 012 345

PROFESSIONAL EXPERIENCE

Warehouse Operations Supervisor — Pwani Oil Products Ltd, Mombasa
2020 – Present (5 years)
- Supervise team of 14 warehouse operatives and loading staff at Mombasa distribution centre
- Implemented FIFO stock rotation system — reduced write-offs by KES 1.8M in first year
- Achieved 99% inventory accuracy on monthly cycle counts for 18 consecutive months
- Oversee 3 shift rotations across 6-day operating week

Logistics Coordinator — Mastermind Tobacco Kenya Ltd, Nairobi
2017 – 2020 (3 years)
- Managed relationships with 18 regional distributor accounts across Nairobi and Central Kenya
- Coordinated fleet of 9 delivery vehicles — maintained 98% schedule adherence
- Eliminated disputed delivery claims through photo-confirmation protocol, saving KES 450K annually

EDUCATION
Certificate in Warehouse Management — Kenya Institute of Management, Nairobi, 2018

SKILLS
Warehouse Management | FIFO Stock Control | Inventory Accuracy | Fleet Coordination
Distributor Account Management | Shift Management | Loading Supervision | MS Excel
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e18_strong_no",
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
