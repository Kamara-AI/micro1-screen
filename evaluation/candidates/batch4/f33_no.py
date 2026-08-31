"""WHY: f33_no tests NO verdict in digital marketing context — insufficient digital years, no management, below-threshold budget, and no degree."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Only 2 years of digital marketing experience (vs 5+ required), no team management history, no personal budget authority (senior manager owns the KES 1.8M/month spend), and a diploma rather than a degree — fails on four of four hard requirements simultaneously. Confidence: 97%."
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
FATUMA AISHA OMAR
Mombasa, Kenya | fatuma.omar@email.com | +254 741 883 156
LinkedIn: linkedin.com/in/fatumaomar

PROFESSIONAL SUMMARY
Enthusiastic and fast-learning marketing professional with 6 years of combined experience across sales and marketing roles. Recently transitioned into digital marketing and passionate about growing my skills in paid social and content strategy. Eager to take on greater responsibility and contribute to a high-growth brand's digital presence.

WORK EXPERIENCE

Digital Marketing Coordinator
Zana Beauty — Nairobi, Kenya (Remote)
January 2023 – Present (1 year 8 months)

- Support the Head of Digital Marketing in implementing Meta Ads and Google Ads campaigns for Zana Beauty's DTC skincare range
- Upload approved ad creatives into Meta Business Suite and Google Ads dashboard as directed by the Head of Digital
- Monitor daily campaign spend and flag anomalies to the Head of Marketing; the KES 1.8M/month ad budget is owned and approved by my manager
- Produce weekly performance snapshots (CTR, CPC, impressions) using Google Analytics 4 and Meta Ads Manager exports
- Coordinate content calendar for organic Instagram and TikTok posts; brief the graphic designer on visual assets
- Assist in compiling influencer outreach lists and drafting introductory emails to nano-creators

Marketing Coordinator
Mombasa Cement Ltd — Mombasa, Kenya
June 2021 – December 2022 (1 year 7 months)

- Supported the marketing manager in planning product launch events and trade exhibitions
- Managed logistics for 4 branch opening activations across the Coast region
- Designed basic promotional flyers using Canva for distribution to hardware dealers and construction contractors
- Maintained the company's Facebook page with organic posts (no paid budget)

Sales Representative
Bidco Africa — Mombasa, Kenya
September 2018 – May 2021 (2 years 8 months)

- Sold Bidco cooking oil, soap, and personal care products to wholesale and retail outlets across the Mombasa and Kilifi routes
- Achieved 108% of monthly sales targets in FY2020 across assigned route of 140 active outlets
- Tracked orders and returns using Bidco's sales force automation app

EDUCATION

Diploma in Marketing
NIBS College — Nairobi, Kenya
Graduated: August 2018

SKILLS & TOOLS
- Digital Platforms: Meta Ads Manager (intermediate — implementation, not strategy), Google Ads (basic), Google Analytics 4 (basic)
- Content: Canva, CapCut (basic video edits), Instagram and TikTok organic posting
- Productivity: Microsoft Office, Google Workspace, Trello
- Languages: English (fluent), Kiswahili (fluent), Arabic (basic)

CERTIFICATIONS
- Meta Blueprint — Digital Marketing Associate (2023)
- Google Digital Garage — Fundamentals of Digital Marketing (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f33_no",
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
