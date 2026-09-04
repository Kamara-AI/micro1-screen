"""WHY: f10_no tests NO verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate fails three of four hard requirements: only 4 years experience (vs. 5+ required), "
    "never managed a team (individual contributor throughout), and maximum ad spend of KES 800K/month is far below the KES 5M threshold; "
    "also holds a diploma rather than a degree. Confidence: 99%. Correctly hard-rejected by tier1_prefilter — STRONG_NO is the expected verdict."
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
KEVIN MUTHOMI WAWERU
Nairobi, Kenya | kevin.waweru94@gmail.com | +254 707 341 128

PROFESSIONAL SUMMARY
Enthusiastic digital marketing professional with 4 years of hands-on experience in social media management and digital campaign execution. Skilled in Meta Business Suite and Google Analytics. Currently a Digital Marketing Executive at Equity Bank, where I support the wider digital marketing team on campaign delivery and social media content. Looking to grow into a more senior role where I can take on greater campaign responsibility.

WORK EXPERIENCE

Digital Marketing Executive — Equity Bank Kenya, Nairobi
May 2022 – Present
- Execute organic social media content across Equity Bank's Facebook, Instagram, and Twitter accounts (combined following: 1.2M)
- Support the digital marketing team with asset preparation and scheduling for paid Meta campaigns
- Pull weekly Google Analytics (UA) performance reports and compile into internal summary decks
- Manage Meta Business Suite posting calendar; track post-level engagement metrics (reach, likes, comments, shares)
- Coordinate with the design team for campaign creative assets; review and approve content for brand compliance
- Ad spend directly managed: up to KES 350K/month on boosted posts and small Meta awareness campaigns

Social Media Manager — Safaricom PLC, Nairobi
August 2020 – April 2022 (1 year 8 months)
- Managed Safaricom's community management across Facebook and Twitter; responded to 400+ customer queries per week
- Scheduled and published social media content developed by the brand team
- Ran small Meta boosted post campaigns (budget: KES 80,000–450,000/month) approved by the senior manager
- Produced monthly social media engagement reports in Excel for the marketing department

EDUCATION
Diploma in Digital Marketing — Kenya College of Accountancy (KCA University), Nairobi, 2020

CERTIFICATIONS
- Meta Blueprint: Digital Marketing Associate (2022)
- Google Analytics Individual Qualification — Universal Analytics (2021, now lapsed)
- Canva Design Essentials (2022)

SKILLS
Social Media Management | Community Management | Meta Business Suite | Google Analytics (UA) | Content Scheduling | Canva | Campaign Reporting | Basic Copywriting | Email Newsletters

HARD REQUIREMENT ASSESSMENT (for evaluator — not shown to AI)
- Years of experience: 4 years (FAILS — requires 5+)
- Management role: None (FAILS — individual contributor throughout both roles)
- Ad spend managed: Maximum KES 800K/month across both roles combined (FAILS — requires KES 5M+/month)
- Degree: Diploma only, not a degree (FAILS — requires degree in marketing/business/communications)
- All four hard gates fail; this is a clear NO
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f10_no",
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
