"""
WHY: e09_ambiguous tests AMBIGUOUS verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "5 years in hotel and bank branch operations — not supply chain. No logistics, "
    "no distribution, team sizes unknown. AMBIGUOUS — phone screen needed. Confidence: 47%."
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
FELIX OMONDI AUMA
Nairobi, Kenya | felix.auma@email.com | +254 714 123 456

PROFESSIONAL EXPERIENCE

Operations Manager — Sarova Hotels and Resorts, Nairobi
March 2022 – Present (3 years 5 months)
- Oversee hotel operations including vendor management, facilities, and guest services
- Leads operations team across multiple departments
- Manages vendor relationships for hotel supplies and services
- Coordinates cross-departmental scheduling and resource allocation

Branch Operations Supervisor — Family Bank Ltd, Nairobi
June 2019 – February 2022 (2 years 9 months)
- Supervised branch operations across 3 branches in Nairobi
- Managed team on daily banking operations activities
- Ensured compliance with internal controls and branch procedures
- Oversaw cash management and vault operations

Freelance Operations Coordinator
January 2018 – May 2019 (1 year 5 months)
- Provided operations consultancy to small businesses
- Supported event coordination and vendor sourcing

EDUCATION
BA Business Administration — Daystar University, Nairobi, 2017

SKILLS
Operations Management | Vendor Management | Team Coordination | Compliance
Facilities Management | Scheduling | MS Office | Customer Service
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e09_ambiguous",
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
