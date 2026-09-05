"""
WHY: e02_strong_yes tests STRONG_YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "7 years logistics, opened 2 warehouses from scratch, team of 18, FMCG key accounts "
    "Nestle and Doinyo Lessos. Degree from Strathmore. Confidence: 91%."
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
MERCY WANJIRU KAMAU
Nairobi, Kenya | mercy.kamau@email.com | +254 722 456 789

PROFESSIONAL EXPERIENCE

Logistics Operations Manager — Siginon Freight Ltd, Nairobi
August 2020 – Present (5 years)
- Lead team of 18 warehouse supervisors, logistics officers, and last-mile coordinators
- Opened 2 greenfield warehouses from scratch: Mombasa (8,000 sqm, commissioned May 2021) and Eldoret (5,200 sqm, commissioned January 2023)
- Manage 22,000 MT monthly throughput for FMCG clients including Nestle Kenya and Doinyo Lessos Creameries
- Reduced delivery cycle time from 4.1 days to 2.3 days through hub-and-spoke route redesign
- Negotiated 3 new 3PL sub-contracts for last-mile coverage in Kisumu and Eldoret corridors
- Manage KES 190M annual operations budget

Supply Chain Team Lead — Davis and Shirtliff Ltd, Nairobi
February 2017 – July 2020 (3 years 6 months)
- Promoted from Supply Chain Analyst to Team Lead in 14 months
- Led team of 9 procurement and logistics officers
- Reduced stock-outs by 61% through safety-stock recalculation and supplier lead-time renegotiation
- Coordinated imports from South Africa, Germany, and China — average clearance time reduced from 9 to 5 days

EDUCATION
BSc Logistics and Supply Chain Management — Strathmore University, Nairobi, 2016
First Class Honours

SKILLS
3PL Management | Warehouse Design and Commissioning | Last-Mile Route Optimisation
FMCG Supply Chain | Cold Chain Management | Fleet Management | Odoo ERP | MS Excel (Advanced)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e02_strong_yes",
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
