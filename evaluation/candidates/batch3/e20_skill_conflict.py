"""
WHY: e20_skill_conflict tests ESCALATE verdict in non-tech FMCG operations context.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "CRITICAL skill_level contradiction: claims Expert in SAP, Oracle SCM, Odoo but EVERY role "
    "across 6 years shows only Excel, WhatsApp, phone calls, and paper records. "
    "Zero ERP usage in any job. ESCALATE."
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
PAUL NJOROGE MUTHEE
Nairobi, Kenya | paul.muthee@email.com | +254 717 234 567

PROFESSIONAL EXPERIENCE

Senior Logistics Officer — Mastermind Tobacco Kenya Ltd, Nairobi
March 2021 – Present (4 years 5 months)
- Lead team of 8 logistics assistants and distribution clerks
- Track daily dispatch volumes using Excel dashboards shared via WhatsApp with depot managers
- Coordinate with subcontractors and transporters using phone and WhatsApp groups
- Maintain manual delivery confirmation records signed by receiving depot supervisors
- Reconcile actual deliveries against customer invoices weekly using Excel pivot tables

Logistics Coordinator — Premier Flour Mills Ltd, Nairobi
January 2018 – February 2021 (3 years 2 months)
- Maintained stock movement records in Excel workbooks updated daily
- Submitted weekly stock report to finance team via email attachment
- Followed up on outstanding orders via phone calls and email
- Resolved disputed deliveries by reviewing paper delivery notes and counter-signatures

EDUCATION
BCom Logistics and Supply Chain Management — United States International University – Africa (USIU-Africa), 2017

SKILLS
Expert: SAP ERP (MM, WM, SD modules), Oracle SCM, Odoo ERP, Microsoft Dynamics
Intermediate: MS Excel, MS Word, MS Outlook
Other: Team coordination, logistics planning, distributor management, route scheduling
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="e20_skill_conflict",
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
