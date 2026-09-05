"""
WHY: e15_no tests NO verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "5 years NGO programme operations and M&E. Programme monitoring, grant reporting, "
    "beneficiary data — not commercial supply chain. Confidence: 20%."
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
ANNE WANJIKU GITHAE
Nairobi, Kenya | anne.githae@email.com | +254 703 789 012

PROFESSIONAL EXPERIENCE

Operations and M&E Manager — Amref Health Africa, Nairobi
January 2021 – Present (4 years 7 months)
- Lead team of 9 M&E officers and data management coordinators
- Manage USD 4.2M programme budget across 3 active health system strengthening projects
- Design and oversee data collection using ODK and KoBoToolbox across 62 field sites
- Produce quarterly donor reports for USAID, DFID, and Bill and Melinda Gates Foundation
- Coordinate with Ministry of Health for programme implementation compliance

Senior Programme Officer — PATH Kenya, Nairobi
March 2018 – December 2020 (2 years 10 months)
- Coordinated malaria commodity distribution in partnership with MOH supply chain division
- Managed KES 280M disbursements for malaria prevention programme activities
- Monitored programme KPIs: beneficiary reach, stockout rates at facility level, net distribution
- Prepared quarterly progress reports for PATH global headquarters

EDUCATION
MSc Public Health — University of Nairobi, 2018
BA Sociology — Kenyatta University, Nairobi, 2015

SKILLS
M&E Framework Design | ODK/KoBoToolbox | Donor Reporting | Programme Budget Management
USAID/DFID Compliance | Beneficiary Data Management | Stakeholder Coordination | Stata | SPSS
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e15_no",
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
