"""
WHY: e06_yes tests YES verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "6 years in regulated supply chain (pharma), team of 12, strong quantification. "
    "Not direct FMCG but adjacent and rigorous. Confidence: 71%."
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
GRACE ATIENO OMONDI
Nairobi, Kenya | grace.omondi@email.com | +254 720 890 123

PROFESSIONAL EXPERIENCE

Regional Operations Manager — Medisel Kenya Ltd, Nairobi
April 2020 – Present (5 years 4 months)
- Lead team of 12 logistics coordinators, warehouse officers, and field distribution agents
- Maintained cold-chain compliance at 99.1% across temperature-sensitive pharmaceutical product lines
- Reduced stock-outs across 214 client facilities from 11% to 3.2% through safety-stock recalibration
- Renegotiated 3PL contracts with 2 providers, saving KES 3.1M annually
- Own KES 78M annual distribution operations budget

Logistics Coordinator — Medical Equipment and Drugs Supplies (MEDS), Nairobi
January 2018 – March 2020 (2 years 3 months)
- Coordinated deliveries to 47 health facilities across Nairobi and Central Kenya
- Improved fleet utilisation from 67% to 89% through dynamic route allocation
- On-time delivery rate: 97% against 90% organisational target

EDUCATION
BA Procurement and Logistics — Maseno University, 2017
Second Class Upper Division

SKILLS
Cold Chain Management | 3PL Contract Management | Last-Mile Distribution | Fleet Utilisation
Inventory Optimisation | KPI Dashboard Design | Regulatory Compliance | Team Leadership
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e06_yes",
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
