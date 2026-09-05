"""
WHY: e01_strong_yes tests STRONG_YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "8 years FMCG operations, grew distribution from 2 to 5 counties, team of 25, "
    "all KPIs quantified, SAP expert, degree in Supply Chain Management. Confidence: 94%."
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
JAMES OCHIENG OTIENO
Nairobi, Kenya | james.otieno@email.com | +254 712 345 678

PROFESSIONAL EXPERIENCE

Senior Distribution Manager — Unga Group Ltd, Nairobi
January 2019 – Present (6 years 7 months)
- Lead a team of 25 field operations coordinators and warehouse supervisors across 5 distribution counties
- Expanded distribution network from 2 to 5 counties (Nairobi, Kiambu, Machakos, Nakuru, Meru) over 3 years
- Improved fill rate from 71% to 94% through route optimisation and 3PL SLA renegotiation
- Reduced cost-per-unit-delivered by 18% (KES 4.2 → KES 3.4) via consolidated truck loading and route sequencing
- Drove shrinkage down from 4.2% to 1.1% through real-time SAP WM bin-level stock tracking
- Manage KES 280M annual distribution budget, consistently within 2% of plan
- Own 4 active 3PL contracts (Siginon, Faulu Logistics, TransAfrica, NikoJet) — total 3PL spend KES 64M/year

Operations Manager — Bidco Africa Ltd, Thika
March 2016 – December 2018 (2 years 10 months)
- Managed team of 13 warehouse supervisors and distribution coordinators at Thika plant
- Oversaw 12,000 MT annual throughput of edible oils and detergents across 3 warehouses
- Led SAP MM/WM implementation for Thika site — went live on time and 6% under budget
- Achieved on-time delivery rate of 91.4% against 88% target in first full year as manager

EDUCATION
BSc Supply Chain Management — Jomo Kenyatta University of Agriculture and Technology (JKUAT), 2015
Second Class Upper Division

SKILLS
SAP WM, SAP MM, SAP SD | 3PL Contract Management | Route Optimisation | KPI Dashboard Design
Last-Mile Distribution | Warehouse Operations | Demand Planning | Team Leadership
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e01_strong_yes",
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
