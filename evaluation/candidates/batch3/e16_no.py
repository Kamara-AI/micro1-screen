"""
WHY: e16_no tests NO verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "5 years contact centre operations. 'Operations Manager' in CX context — SLA management, "
    "IVR, agent coaching. No supply chain, no logistics, no FMCG. Confidence: 18%."
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
KEVIN ODHIAMBO ONYANGO
Nairobi, Kenya | kevin.onyango@email.com | +254 715 890 123

PROFESSIONAL EXPERIENCE

Call Centre Operations Manager — Safaricom PLC, Nairobi
April 2020 – Present (5 years 4 months)
- Manage 180-agent contact centre serving M-PESA and mobile service customers
- Lead team of 8 team leaders and quality assurance coaches
- Achieved 94% First Call Resolution (FCR) rate — up from 81% at appointment
- Maintained Average Handle Time (AHT) of 3.2 minutes against 4.0-minute target
- Developed workforce management model that saved KES 2.1M annually in overtime costs
- Oversee IVR system performance and escalation routing configuration

Customer Service Supervisor — Airtel Kenya, Nairobi
January 2018 – March 2020 (2 years 3 months)
- Supervised team of 22 customer service agents across inbound and outbound desks
- Improved CSAT score from 71% to 84% in 18 months through coaching and call calibration
- Designed quality monitoring scorecard adopted across the department

EDUCATION
BCom Marketing — Multimedia University of Kenya, Nairobi, 2017

SKILLS
Contact Centre Operations | Workforce Management | IVR Configuration | FCR Optimisation
CSAT Management | Agent Coaching | Quality Assurance | SLA Management | Genesys | Avaya
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e16_no",
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
