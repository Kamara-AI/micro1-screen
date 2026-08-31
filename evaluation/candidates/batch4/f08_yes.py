"""WHY: f08_yes tests YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate meets all hard requirements via agency-side experience (7 years, KES 15M/month combined client spend, "
    "team of 5, BA Marketing) with strong e-commerce exposure, but indirect budget ownership and account director framing "
    "introduce moderate uncertainty about direct operational fit. Confidence: 77%."
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
ISAAC MWENDA GITHINJI
Nairobi, Kenya | isaac.githinji@gmail.com | +254 710 229 614 | linkedin.com/in/isaacmwenda

PROFESSIONAL SUMMARY
Senior digital marketing strategist with 7 years of agency experience at WPP Scangroup, specialising in e-commerce and FMCG clients across East Africa. Currently Group Account Director overseeing KES 15M/month in combined client digital ad spend across 4 e-commerce accounts. Proven team leader, consistent deliverer of 3.5–4.5x ROAS benchmarks, and skilled at translating brand strategy into performance outcomes. Ready to transition into a senior in-house role with direct P&L accountability.

WORK EXPERIENCE

Group Account Director (Digital) — WPP Scangroup, Nairobi
January 2022 – Present
- Manage a portfolio of 4 e-commerce clients with a combined digital advertising budget of KES 15M/month across Meta Ads, Google Ads, TikTok for Business, and programmatic display
- Oversee a team of 5: 2 digital account managers, 1 paid media specialist, 1 SEO/content executive, 1 data & reporting analyst
- Deliver consistent ROAS of 3.5–4.5x across client e-commerce campaigns; highest single campaign ROAS: 5.2x for a Kenyan personal care client's festive season push
- Built and manage HubSpot CRM pipelines for 2 clients; integrated email workflows driving 19% of client monthly revenue
- Oversee influencer programme for 2 accounts with a combined roster of 70 Kenyan micro-creators
- Tools: GA4, Meta Business Suite, Google Ads, TikTok Ads Manager, DV360, HubSpot, various client CRMs, SEMrush, Looker Studio

Senior Digital Account Manager — WPP Scangroup, Nairobi
March 2019 – December 2021 (2 years 9 months)
- Managed digital campaigns for 2 FMCG clients (Unilever East Africa, Bidco Oil); combined budget KES 6M/month
- Led a team of 2 junior account executives; introduced performance review cadence that reduced campaign error rate by 40%
- Delivered Google Shopping campaign for a Unilever product launch; achieved cost-per-conversion 32% below target

Digital Account Executive — WPP Scangroup, Nairobi
May 2017 – February 2019 (1 year 9 months)
- Executed paid social and SEM campaigns across 3 client accounts in FMCG and financial services
- Built client-facing monthly performance decks presented to brand managers

EDUCATION
BA Marketing — Daystar University, Nairobi, 2017 (Second Class Upper)

CERTIFICATIONS
- Google Ads Search & Shopping Certifications (2024)
- Meta Blueprint: Media Buying Professional (2023)
- HubSpot Marketing Hub Certified (2022)
- TikTok for Business: Campaign Management (2023)

SKILLS
Performance Marketing | Paid Social | SEM | SEO | Email/CRM | Influencer Marketing | Team Leadership | Client Services | GA4 | Meta Business Suite | Google Ads | TikTok Ads Manager | DV360 | HubSpot | SEMrush | Looker Studio

NOTABLE GAPS (for evaluator awareness)
- All experience is agency-side; budget ownership is client-delegated, not direct P&L
- Has never held a single-brand in-house digital marketing role
- Team management is across account teams, not a dedicated in-house marketing function
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f08_yes",
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
