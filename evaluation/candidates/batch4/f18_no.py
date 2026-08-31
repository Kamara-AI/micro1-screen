"""WHY: f18_no tests NO verdict where domain (B2B SaaS) is mismatched, team size is below threshold, and budget is below threshold — despite the candidate being technically strong."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Fails two hard requirements: team of 2 direct reports (vs 3+ required) and KES 1.8M/month budget (vs KES 5M+ required); domain is enterprise B2B SaaS with LinkedIn-led lead generation, fundamentally different from D2C consumer e-commerce — not a viable fit despite strong analytics capability. Confidence: 90%."
)

JOB_DESCRIPTION: str = """
Senior Digital Marketing Manager — Kweli Commerce Ltd
Nairobi, Kenya | Remote-first (quarterly in-person)

Kweli Commerce is a Kenyan D2C e-commerce brand selling locally-manufactured personal care and wellness products. 200 employees, KES 2.1B revenue, 450,000 active customers. Expanding to Mombasa, Kisumu, and Uganda.

WHAT YOU WILL DO
- Own and optimise KES 7M/month digital advertising budget across Meta Ads, Google Ads, TikTok for Business
- Lead a team of 4 digital marketing specialists and 1 data analyst
- Multi-channel campaigns: paid social, SEM, SEO, email/CRM, influencer
- KPIs: ROAS, CAC, LTV, email open rates, CTR, conversion rate
- Manage influencer/affiliate programme (120+ active creators)

HARD REQUIREMENTS
- 5+ years digital marketing experience, at least 2 years in a management role
- Managed digital advertising budget of KES 5M+/month (USD 35,000+/month)
- Managed a team of 3+ direct reports
- Degree in Marketing, Business Administration, Communications, or related field
"""

CV_TEXT: str = """
JAMES MWANGI GITHUKA
Nairobi, Kenya | james.githuka@email.com | +254 740 334 521
LinkedIn: linkedin.com/in/jamesmwangi-b2b

PROFESSIONAL SUMMARY
B2B digital marketing manager with 5 years of experience in SaaS and fintech lead generation across East and West Africa. Specialises in demand generation, ABM (account-based marketing), LinkedIn Ads, and CRM-driven nurture programmes. Track record of building high-quality enterprise sales pipelines for technical products with long sales cycles.

WORK EXPERIENCE

Digital Marketing Manager
Flutterwave — Nairobi, Kenya (Africa-wide remit)
August 2022 – Present (2 years 1 month)

- Own digital marketing strategy for Flutterwave's Africa SMB and enterprise acquisition channels
- Manage KES 1.8M/month digital advertising budget across LinkedIn Campaign Manager, Google Search (branded and non-branded), and Programmatic Display
- Directly manage a team of 2: 1 paid media specialist and 1 marketing operations / CRM specialist
- Drive MQL targets for the enterprise sales team; delivered 340 MQLs in Q1 2024 against a target of 280
- Own HubSpot CRM marketing workflows: lead scoring, nurture sequences, and sales handoff automation
- Coordinate with Salesforce admin team on attribution modelling and closed-loop reporting
- Run quarterly webinars and LinkedIn Live sessions as part of thought leadership strategy targeting CFOs and tech leads at African SMEs

Digital Marketing Specialist
Andela — Nairobi, Kenya
May 2019 – July 2022 (3 years 3 months)

- Managed Google Search campaigns targeting engineering talent recruiters and CTOs in the US and European markets
- Ran LinkedIn Ads for Andela's talent marketplace product; handled budgets up to KES 600K/month
- Built HubSpot email nurture sequences for inbound leads from blog content and gated assets
- Produced bi-weekly SEO content aligned with developer hiring and tech talent search intent
- Collaborated with the US-based growth team on A/B landing page tests and conversion rate optimisation

EDUCATION

BSc Business Administration — Strathmore University, Nairobi
Graduated: 2019 | Upper Second Class Honours

SKILLS & TOOLS
- B2B Paid Media: LinkedIn Campaign Manager, Google Ads (Search, Display), Programmatic (DV360 basic)
- CRM & Automation: HubSpot (Marketing Hub, Sales Hub), Salesforce (reporting)
- Analytics: GA4, Looker Studio, Salesforce Reports
- ABM: Demandbase (basic), LinkedIn Matched Audiences
- Other: Zoom Webinars, Canva, Notion, Slack

CERTIFICATIONS
- HubSpot Marketing Hub Certification (2024)
- LinkedIn Marketing Labs — Fundamentals (2023)
- Google Ads Search Certification (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f18_no",
    role_seniority="senior",
    role_type="other",
    batch_id="eval_batch_004",
    hard_requirements=[
        "5+ years digital marketing experience, at least 2 years in a management role",
        "managed digital advertising budget of KES 5M+ per month (or USD 35,000+/month)",
        "managed a team of 3+ direct reports",
        "degree in marketing, business administration, communications, or related field",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
