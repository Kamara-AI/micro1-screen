"""WHY: f27_skill_conflict tests ESCALATE verdict (skill_conflict) in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate meets hard requirements on budget, team size, and years of experience, but the Skills section claims Expert-level proficiency in GA4, Salesforce Marketing Cloud, Adobe Analytics, and Marketo while every single role bullet describes manual Excel and PDF-based reporting with zero reference to any of these tools in any work context — a critical skill-level contradiction requiring human review. Confidence: 94%."
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
SAMUEL OCHIENG ONYANGO
Nairobi, Kenya | samuel.onyango@email.com | +254 701 228 445
LinkedIn: linkedin.com/in/samuelonyango

PROFESSIONAL SUMMARY
Digital Marketing Manager with 7 years of experience driving customer acquisition and retention campaigns in the East African fintech and payments sector. Experienced people manager with a strong commercial background. Expert-level proficiency in enterprise marketing analytics and automation platforms.

WORK EXPERIENCE

Digital Marketing Manager
Pesapal Limited — Nairobi, Kenya
March 2020 – Present (4 years 5 months)

- Manage a monthly digital advertising budget of KES 5.5M across Meta Ads and Google Ads, targeting SME merchants and individual payment users across Kenya, Uganda, and Tanzania
- Lead a team of 3 digital marketing specialists covering paid media, content, and merchant communications
- Oversee monthly merchant acquisition campaigns; tracked campaigns using Excel dashboards shared with the Head of Marketing via email every Friday
- Monthly PDF reports prepared manually for the CMO covering spend, clicks, and estimated lead volumes
- Reduced merchant onboarding cost by 18% over 24 months by refining Meta Ads audience targeting for fintech decision-makers
- Managed seasonal push campaigns around salary periods and school-fee cycles to drive payment volume spikes
- Used spreadsheets for attribution across Meta and Google Ads — allocated conversions proportionally based on last-click channel spend ratios documented in shared Google Sheets
- Coordinated with the product team on merchant portal landing page updates to improve form completion rates

Senior Digital Marketing Executive
Cellulant Corporation — Nairobi, Kenya
January 2018 – February 2020 (2 years 2 months)

- Executed digital acquisition campaigns for Cellulant's Agrikore and Tingg platforms across 4 African markets
- Managed Google Ads Search and Display budget of KES 1.1M/month with oversight from the Marketing Director
- Monthly PDF campaign reports prepared manually using data exported from ad platform dashboards into Excel
- Supported the CRM team with email campaign scheduling; used spreadsheets for list segmentation and send-time tracking
- Assisted in writing creative briefs for the in-house design team

Digital Marketing Executive
Interswitch East Africa — Nairobi, Kenya
February 2017 – December 2017 (11 months)

- Managed organic social media content and scheduled low-budget boosted posts for Quickteller Kenya
- Produced weekly social media performance summaries in Excel for the Marketing Manager

EDUCATION

BSc Information Technology — Multimedia University of Kenya, Nairobi
Graduated: 2016 | Second Class Honours

SKILLS & TOOLS
- Analytics: Expert: Google Analytics 4 (GA4), Adobe Analytics, Expert: Salesforce Marketing Cloud
- Marketing Automation: Expert: Marketo, Expert: HubSpot Marketing Hub
- Paid Media: Meta Ads Manager, Google Ads
- Other: Microsoft Excel (advanced), PowerPoint, Google Workspace

CERTIFICATIONS
- Google Ads Search Certification (2023)
- Meta Blueprint — Digital Marketing Associate (2022)
- Salesforce Marketing Cloud Email Specialist (2021)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f27_skill_conflict",
    role_seniority="senior",
    role_type="other",
    role_description="Senior Digital Marketing Manager",
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
