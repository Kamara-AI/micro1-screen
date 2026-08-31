"""
WHY: e12_no tests NO verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "5 years operations entirely in events and hospitality. No supply chain, no logistics, "
    "no distribution anywhere. Wrong domain. Confidence: 28%."
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
ALICE MUTHONI KARIUKI
Nairobi, Kenya | alice.kariuki@email.com | +254 718 456 789

PROFESSIONAL EXPERIENCE

Events Operations Manager — Hemingways Hotel, Nairobi
March 2021 – Present (4 years 5 months)
- Lead team of 12 events coordinators and setup technicians
- Deliver 120+ events per year including corporate conferences, weddings, and gala dinners
- Manage vendor relationships for décor, catering, AV equipment, and entertainment
- Oversee event budgets ranging from KES 500K to KES 8M per event
- Coordinate with hotel F&B, accommodation, and security teams for seamless event execution

Operations Supervisor — Carnivore Restaurant, Nairobi
September 2018 – February 2021 (2 years 6 months)
- Supervised team of 18 F&B service staff across indoor and outdoor dining areas
- Reduced no-show rate for large group reservations by 34% through confirmation call protocol
- Managed shift scheduling for 6-day operating week
- Coordinated with kitchen and bar teams on service flow and guest experience

EDUCATION
BA Tourism and Hospitality Management — Kenyatta University, Nairobi, 2017
Second Class Upper Division

SKILLS
Event Operations | Vendor Management | Team Supervision | F&B Service Management
Budget Management | Guest Relations | Shift Scheduling | MS Excel | Opera PMS
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e12_no",
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
