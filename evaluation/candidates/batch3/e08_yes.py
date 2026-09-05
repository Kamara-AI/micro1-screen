"""
WHY: e08_yes tests YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "5 years supply chain at Kapa Oil (cooking oils — direct sector match), team of 14, "
    "strong metrics. No ERP but that is nice-to-have. Confidence: 70%."
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
DIANA WAMBUI KAMAU
Nairobi, Kenya | diana.kamau@email.com | +254 723 012 345

PROFESSIONAL EXPERIENCE

Supply Chain Manager — Kapa Oil Refineries Ltd, Nairobi
July 2019 – Present (6 years 1 month)
- Lead team of 14 supply chain officers, warehouse supervisors, and logistics coordinators
- Manage KES 1.1B annual product throughput (refined cooking oils, vegetable ghee, margarine)
- Sustained fill rate above 95% for 4 consecutive years
- Reduced supplier average unit cost by 14% through competitive re-tendering and long-term volume contracts
- Introduced S&OP (Sales and Operations Planning) process — reduced forecast variance from 22% to 9%
- Manage 3 active 3PL partners for Nairobi Metro, Coast, and Western distribution corridors

Procurement Officer — Crown Paints Kenya Ltd, Nairobi
February 2017 – June 2019 (2 years 5 months)
- Managed KES 380M annual procurement spend across raw materials and indirect categories
- Led vendor rationalisation programme — reduced vendor base from 60 to 18 preferred suppliers
- Negotiated new payment terms improving working capital by KES 12M

EDUCATION
BCom Supply Chain Management — University of Nairobi, 2016
Second Class Upper Division

SKILLS
S&OP Planning | 3PL Management | Procurement | Supplier Negotiation | Fill Rate Optimisation
Warehouse Operations | KPI Governance | MS Excel (Advanced) | Power BI | Inventory Planning
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e08_yes",
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
