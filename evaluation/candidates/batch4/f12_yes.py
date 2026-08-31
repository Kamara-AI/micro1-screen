"""WHY: f12_yes tests YES verdict where vertical differs from D2C personal care but all hard requirements are met."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Clears all four hard gates — 5 years experience with 2 years as Digital Marketing Lead, USD 36,000/month ad budget (above threshold), team of 3 direct reports, and BCom Marketing from University of Nairobi — though the food-delivery vertical is a mild fit gap versus D2C personal care. Confidence: 85%."
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
BRIAN OTIENO ODHIAMBO
Nairobi, Kenya | brian.odhiambo@email.com | +254 722 581 034
LinkedIn: linkedin.com/in/brianotieno-dmk

PROFESSIONAL SUMMARY
Performance-focused Digital Marketing Lead with 5 years of experience in high-growth consumer technology and food-delivery markets. Skilled in full-funnel paid media, CRM automation, and app growth marketing. Managed multi-million-shilling budgets and cross-functional teams delivering measurable acquisition and retention outcomes.

WORK EXPERIENCE

Digital Marketing Lead
HelloFood Kenya — Nairobi, Kenya
January 2022 – Present (2 years 7 months)

- Lead digital marketing strategy and execution for HelloFood Kenya's consumer-facing growth channels
- Manage USD 36,000/month (approx. KES 5.1M) digital advertising budget across Meta Ads, Google Ads (UAC, Search), and TikTok for Business
- Directly manage a team of 3: 2 paid media specialists and 1 content/social media specialist
- Delivered app install ROAS of 3.1x consistently over the last 4 quarters
- Achieved email CTR of 4.2% and push notification open rate of 22% through Braze-powered segmentation and personalised messaging
- Reduced CAC for new app installs by 28% through creative iteration and audience exclusion strategies
- Managed relationships with 30 food and lifestyle micro-influencers; influencer-driven orders up 18% YoY
- Collaborated with product and data teams to build attribution dashboards using Adjust and GA4

Digital Marketing Specialist
Sendy Ltd — Nairobi, Kenya
September 2019 – December 2021 (2 years 4 months)

- Executed paid campaigns on Meta and Google for Sendy's B2C logistics product targeting SME owners
- Managed campaign budgets up to KES 1.2M/month; reported weekly on CPL, CTR, and conversion rates
- Built and maintained Google Analytics (UA) tracking across web and app touchpoints
- Coordinated with the design team on ad creative briefs and landing page optimisation

EDUCATION

BCom Marketing — University of Nairobi
Graduated: 2019 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- Paid Media: Meta Business Suite, Google Ads, TikTok for Business, YouTube Ads
- App Marketing: Adjust (MMP), AppsFlyer (basic), Firebase
- CRM & Push: Braze, Mailchimp
- Analytics: GA4, Google Data Studio, Looker Studio
- Other: Notion, Asana, Slack, Excel (pivot tables, VLOOKUP)

CERTIFICATIONS
- Google Ads App Certification (2024)
- Meta Blueprint — Digital Marketing Associate (2023)
- Braze Practitioner Certification (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f12_yes",
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
