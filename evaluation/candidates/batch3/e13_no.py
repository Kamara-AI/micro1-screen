"""
WHY: e13_no tests NO verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Diploma in Shipping and Logistics — hard requirement is a university degree. "
    "Hard-reject via degree gate before LLM analysis. Additionally: 100% subordinate language, "
    "no team management, no owned outcomes. Confidence: 100%."
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
MICHAEL OTIENO OKELLO
Mombasa, Kenya | michael.okello@email.com | +254 741 567 890

PROFESSIONAL EXPERIENCE

Logistics Officer — Bollore Transport and Logistics Kenya, Mombasa
January 2019 – Present (6 years 7 months)
- Assisted the operations team with daily logistics coordination tasks
- Supported the logistics manager in preparing daily dispatch reports
- Participated in weekly operations review meetings
- Responsible for filing and maintaining logistics documentation records
- Assisted with compiling data for monthly performance reports under supervision of the manager
- Helped coordinate communication between warehouse and transport teams as directed

Documentation Clerk — CMA CGM Kenya, Mombasa
August 2017 – December 2018 (1 year 5 months)
- Processed bills of lading and shipping documentation
- Supported the documentation team with data entry and filing
- Assisted senior documentation officers with client queries
- Maintained accurate records of import and export shipments

EDUCATION
Diploma in Shipping and Logistics — Kenya Coast National Polytechnic, Mombasa, 2016

SKILLS
Documentation Processing | Data Entry | Filing | Logistics Support | MS Word | MS Excel
Bills of Lading | Shipping Records | Communication | Teamwork
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e13_no",
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
