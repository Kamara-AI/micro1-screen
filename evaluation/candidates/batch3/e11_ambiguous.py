"""
WHY: e11_ambiguous tests AMBIGUOUS verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "MBA ops focus, team of 16, but 4 years in university campus operations "
    "(facilities/procurement) not commercial supply chain. Limited commercial FMCG exposure. "
    "AMBIGUOUS. Confidence: 50%."
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
JOSEPH WAWERU NGUGI
Nairobi, Kenya | joseph.ngugi@email.com | +254 709 345 678

PROFESSIONAL EXPERIENCE

Operations Manager — Strathmore University, Nairobi
January 2020 – Present (5 years 7 months)
- Lead team of 16 staff covering facilities management, procurement, transport, and catering operations
- Manage KES 85M annual procurement budget — achieved 11% cost reduction in FY2022/23 through competitive tendering
- Implemented asset tracking system for 2,400 university assets — reduced asset loss incidents by 44%
- Oversee transport fleet of 8 vehicles serving 6,000 students and 400 staff
- Coordinate 12 service vendors (cleaning, security, catering, maintenance)

Supply Chain Analyst — Centum Investment Company, Nairobi
June 2018 – December 2019 (1 year 7 months)
- Analysed supply chain performance for portfolio companies in manufacturing and real estate
- Produced quarterly benchmarking reports comparing portfolio companies against sector peers
- Supported due diligence exercises for 2 acquisition targets in the FMCG sector

EDUCATION
MBA Operations Management — Strathmore Business School, Nairobi, 2019
BCom Accounting — Kenyatta University, Nairobi, 2016

SKILLS
Facilities Operations | Procurement | Vendor Management | Asset Management
Supply Chain Analysis | Budget Management | Fleet Management | Team Leadership | MS Excel
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e11_ambiguous",
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
