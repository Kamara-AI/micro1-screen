"""
WHY: e17_strong_no tests STRONG_NO verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Only 2 years total experience. 5-year hard requirement not met. "
    "Hard-reject at tier1. Confidence: 100%."
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
IAN MWANGI KARIUKI
Nairobi, Kenya | ian.kariuki@email.com | +254 729 901 234

PROFESSIONAL EXPERIENCE

Operations Graduate Trainee — Bidco Africa Ltd, Thika
September 2023 – Present (11 months)
- Rotating graduate programme covering warehouse operations, distribution planning, and procurement
- Completed rotations in WM (4 months), distribution coordination (4 months), and procurement (3 months)
- Supported team leads in daily reporting and KPI tracking
- Attended weekly operations review meetings as observer and note-taker

Logistics and Warehouse Intern — Kenya Red Cross Society, Nairobi
January 2023 – August 2023 (8 months)
- Received and entered incoming stock into warehouse management register
- Assisted with bin location updates and physical stock counts
- Supported distribution team with data entry for relief consignment tracking

EDUCATION
BSc Operations Management — Technical University of Kenya, Nairobi, 2022
First Class Honours

SKILLS
Warehouse Operations | Inventory Management | Data Entry | Stock Counting | MS Excel
Distribution Support | KPI Reporting (support role) | SAP Basics (training environment only)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e17_strong_no",
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
