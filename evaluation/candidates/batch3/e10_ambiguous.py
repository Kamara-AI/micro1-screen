"""
WHY: e10_ambiguous tests AMBIGUOUS verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "Titles look right (Bidco, Promasidor, 6 years) but CV is entirely responsibilities "
    "with zero achievements, no team sizes, no metrics. Cannot assess depth. AMBIGUOUS. Confidence: 44%."
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
CAROL NJOKI MWANGI
Nairobi, Kenya | carol.mwangi@email.com | +254 725 234 567

PROFESSIONAL EXPERIENCE

Operations Manager, Distribution Division — Bidco Africa Ltd, Nairobi
2021 – Present
- Responsible for operations management in distribution division
- Managing team operations on a daily basis
- Handling 3PL relationships as required by the business
- Overseeing warehouse operations across sites
- Ensuring compliance with company policies and procedures
- Coordinating with finance and commercial teams on operational matters

Supply Chain Coordinator — Promasidor Kenya Ltd, Nairobi
2018 – 2021
- Coordinated supply chain activities for the Kenya business unit
- Worked with suppliers to ensure timely delivery of raw materials
- Ensured smooth operations across the supply chain function
- Supported the Supply Chain Manager with reporting requirements
- Assisted in managing relationships with logistics providers

EDUCATION
BSc Business Management — Kenyatta University, 2017

SKILLS
Operations Management | Supply Chain Coordination | 3PL Management | Warehouse Operations
Team Management | Supplier Relations | MS Excel | Report Writing
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e10_ambiguous",
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
