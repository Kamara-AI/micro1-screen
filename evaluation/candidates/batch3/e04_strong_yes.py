"""
WHY: e04_strong_yes tests STRONG_YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "10 years including 6 at Unilever Kenya. Team of 30, KES 1.2B distribution budget, "
    "launched 3 routes from scratch, SAP expert. Confidence: 96%."
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
BEATRICE AUMA ODHIAMBO
Nairobi, Kenya | beatrice.odhiambo@email.com | +254 700 678 901

PROFESSIONAL EXPERIENCE

Head of Distribution Operations — Unilever Kenya Ltd, Nairobi
March 2018 – Present (7 years 5 months)
- Lead team of 30 field operations coordinators, warehouse supervisors, and 3PL account managers
- Own KES 1.2B annual distribution budget — delivered 2.3% under plan for 3 consecutive years
- Launched 3 new distribution routes from scratch (Coast, Western, Mt Kenya regions) — all break-even in 8 months against 14-month target
- Sustained fill rate of 98.4% across all routes
- Consolidated 3PL provider base from 7 to 3 strategic partners, saving KES 34M annually
- SAP APO: led demand planning module rollout for East Africa cluster (Kenya, Uganda, Tanzania)
- Report weekly to Africa Regional COO on expansion KPIs and milestone tracking

Supply Chain Manager — Procter and Gamble East Africa, Nairobi
June 2014 – February 2018 (3 years 9 months)
- Managed team of 12 supply chain coordinators and procurement officers
- Improved OTIF (On-Time-In-Full) from 84% to 96% in 18 months
- Reduced SAP APO forecast error from 18% to 7% through collaborative forecasting with top 20 distributors

EDUCATION
BBA International Business — United States International University – Africa (USIU-Africa), Nairobi, 2013
Cum Laude

SKILLS
SAP APO | SAP MM | SAP SD | 3PL Strategic Sourcing | Distribution Network Design
Route-to-Market Strategy | Demand Planning | KPI Governance | Team Leadership (30+)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e04_strong_yes",
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
