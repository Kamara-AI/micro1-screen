"""WHY: f26_date_contradiction tests ESCALATE verdict (date_contradiction) in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "Strong candidate on all four hard requirements, but CV contains an irreconcilable temporal contradiction: the candidate lists her AdPulse Kenya start date as January 2019, while the CV's own company description states AdPulse Kenya was founded in February 2020 — she claims employment 13 months before the company existed. Confidence: 95%."
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
DIANA WAMBUI GITHINJI
Nairobi, Kenya | diana.githinji@email.com | +254 720 334 891
LinkedIn: linkedin.com/in/dianagithinji

PROFESSIONAL SUMMARY
Results-oriented Digital Marketing Director with 6 years of experience leading performance marketing functions for digital-first agencies and brand clients across East Africa. Expertise in full-funnel digital strategy, paid media optimisation, and cross-channel attribution. Consistent track record of delivering ROAS above 3.5x across D2C and fintech verticals.

WORK EXPERIENCE

Digital Marketing Director
AdPulse Kenya — Nairobi, Kenya
January 2019 – Present (5 years 7 months)

About AdPulse Kenya: AdPulse Kenya is a performance marketing agency specialising in paid digital advertising for East African brands. The agency was founded in February 2020 by CEO James Kariuki and has grown to a team of 22 staff.

- Own and manage a combined digital advertising portfolio of KES 6M/month across all agency clients, spanning Meta Ads, Google Ads, and programmatic display
- Lead a team of 4 digital marketing specialists (2 paid media, 1 SEO/content, 1 analytics) plus 1 junior account manager
- Deliver average ROAS of 3.8x across D2C beauty, wellness, and fintech client accounts
- Architect full-funnel Meta Ads strategies including Advantage+ Shopping Campaigns, retargeting funnels, and lookalike audience scaling
- Oversee monthly Google Ads Search, Performance Max, and YouTube campaigns; manage Smart Bidding strategy transitions for 6 client accounts
- Conduct quarterly business reviews with clients presenting CAC trends, LTV cohort analysis, and channel attribution findings
- Introduced GA4 migration framework adopted across all 8 agency client accounts, reducing attribution gaps by 30%

Digital Marketing Manager
Liquid Intelligent Technologies — Nairobi, Kenya
March 2017 – December 2018 (1 year 10 months)

- Managed KES 1.8M/month digital advertising budget across Google Ads and LinkedIn Ads for B2B and enterprise ICT solutions
- Led a team of 2 digital marketing executives covering paid search and content marketing
- Drove a 34% increase in qualified inbound leads over 12 months through Google Search campaign restructuring and landing page optimisation
- Managed SEO strategy for liquidtelecom.co.ke resulting in 78% organic traffic growth in 18 months
- Produced bi-weekly campaign performance reports for the CMO and regional sales directors

EDUCATION

BSc Marketing — University of Nairobi, Nairobi
Graduated: 2016 | Upper Second Class Honours

SKILLS & TOOLS
- Paid Media: Meta Ads Manager (Advantage+, DPA, CBO), Google Ads (Search, PMax, YouTube), LinkedIn Ads, Programmatic (DV360 basic)
- Analytics: GA4, Google Looker Studio, Supermetrics
- SEO: Ahrefs, SEMrush, Screaming Frog
- CRM: HubSpot, Klaviyo
- Other: Microsoft Excel (advanced), Notion, Slack

CERTIFICATIONS
- Meta Blueprint — Media Buying Professional (2023)
- Google Ads — Search, Performance Max, and Measurement Certifications (2024)
- HubSpot Marketing Hub Certification (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f26_date_contradiction",
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
