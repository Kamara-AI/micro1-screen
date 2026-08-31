"""
WHY: e03_strong_yes tests STRONG_YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "6 years at Kenya Breweries — exact FMCG manufacturing analogue. Team 20, "
    "4-county distribution, fill rate 96%+, KES 320M budget. Confidence: 93%."
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
DAVID KIPROP MUTAI
Nakuru, Kenya | david.mutai@email.com | +254 733 567 890

PROFESSIONAL EXPERIENCE

Operations Manager, Nakuru Plant — Kenya Breweries Ltd (EABL Group), Nakuru
January 2021 – Present (4 years 7 months)
- Lead team of 20 warehouse supervisors, logistics coordinators, and field distribution officers
- Own end-to-end distribution across 4 counties: Nakuru, Baringo, Laikipia, Nyandarua
- Sustained fill rate above 96% for 38 consecutive months
- On-time delivery rate: 98.1% (industry benchmark: 91%)
- Reduced cold chain loss from 2.8% to 0.6% through temperature-logging protocol rollout across 11 distribution vehicles
- Manage KES 320M annual operations budget — consistently 4% under plan for 3 years
- Report directly to Regional COO on weekly expansion milestones and KPI dashboards

Distribution Supervisor — East African Breweries Ltd (EABL), Nairobi
May 2018 – December 2020 (2 years 8 months)
- Supervised team of 11 drivers and 4 loading assistants across Nairobi North corridor
- Redesigned stop sequencing to increase stops-per-route from 14 to 22 (+57%)
- Reduced breakage claims by 38% through padding protocol and load-securing training

EDUCATION
BBA Business Administration — University of Nairobi, 2017
Second Class Upper Division

SKILLS
Distribution Planning | KPI Dashboard Management | Cold Chain Logistics | Fleet Management
3PL Partner Management | SAP MM | Team Leadership | MS Power BI
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e03_strong_yes",
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
