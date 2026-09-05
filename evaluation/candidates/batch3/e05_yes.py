"""
WHY: e05_yes tests YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "5 years ops in beverage sector, team of 8 (slightly below 10+ requirement but close), "
    "good quantification, degree. Confidence: 69%."
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
PETER NJOROGE MWANGI
Nairobi, Kenya | peter.mwangi@email.com | +254 711 789 012

PROFESSIONAL EXPERIENCE

Operations Manager — Keroche Breweries Ltd, Naivasha
February 2021 – Present (4 years 6 months)
- Manage operations team of 8 (distribution coordinators and warehouse officers) at Naivasha plant
- Improved on-time delivery rate from 81% to 93% across Rift Valley and Central distribution corridors
- Manage 3 active 3PL partners covering Nakuru, Naivasha, and Narok routes
- Reduced fleet idle time by 29% through dynamic route scheduling
- Oversee KES 42M annual distribution operations budget

Supply Chain Coordinator — Highlands Mineral Water Ltd, Naivasha
January 2019 – January 2021 (2 years)
- Managed 120 active distributor accounts across Central and Rift Valley regions
- Reduced order processing errors by 27% through order-entry checklist and double-verification protocol
- Coordinated inbound raw materials (PET preforms, caps, labels) from suppliers in Nairobi and Mombasa

EDUCATION
BSc Operations Management — Dedan Kimathi University of Technology, Nyeri, 2018
Second Class Upper Division

SKILLS
3PL Partner Management | Distribution Planning | Fleet Management | Last-Mile Logistics
KPI Tracking | Distributor Account Management | MS Excel (Advanced) | Inventory Management
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e05_yes",
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
