"""WHY: f07_yes tests YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate meets all four hard requirements (6 years, KES 5.8M/month, 3 direct reports, BSc with Marketing minor) "
    "and has TikTok and advanced mobile attribution experience, but the food delivery vertical is a meaningful mismatch with personal care D2C. Confidence: 79%."
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
HELLEN WAITHERA NJOROGE
Nairobi, Kenya | hellen.njoroge@gmail.com | +254 723 540 882 | linkedin.com/in/hellenwaithera

PROFESSIONAL SUMMARY
Performance marketing manager with 6 years of experience in high-velocity digital advertising for consumer-facing apps and marketplace businesses in East Africa. Currently Performance Marketing Manager at Glovo East Africa, managing KES 5.8M/month across Meta, Google, and TikTok and leading a 3-person performance marketing team. Expert in mobile attribution (AppsFlyer, Adjust) and app-install campaign optimisation. Seeking to broaden into physical product D2C growth marketing.

WORK EXPERIENCE

Performance Marketing Manager — Glovo East Africa, Nairobi
September 2021 – Present
- Manage KES 5.8M/month digital advertising budget across Meta Ads, Google Ads, and TikTok for Business
- Lead a team of 3 performance marketers covering paid social, paid search, and TikTok campaigns
- Achieved blended CAC of KES 410 for new Glovo app installs (Kenya); reduced CAC 26% over 18 months via creative iteration and audience exclusion strategies
- Delivered 4.1x ROAS on TikTok for Business campaigns targeting Gen Z food delivery users in Nairobi
- Managed 30 food and lifestyle influencers for Glovo Kenya; TikTok content drove 14% of Q3 2023 new installs
- Implemented AppsFlyer MMP integration; unified cross-channel attribution enabled 22% budget reallocation toward highest-performing placements
- Tools: GA4, Meta Ads Manager, Google Ads, TikTok for Business, AppsFlyer, Adjust, Looker Studio

Digital Marketing Specialist — Jumia Kenya, Nairobi
June 2019 – August 2021 (2 years 2 months)
- Executed paid social and SEM campaigns for Jumia's fashion, electronics, and FMCG categories
- Managed Meta Dynamic Product Ads that contributed 38% of total paid social revenue during Jumia's Black Friday campaigns
- Supported influencer marketing coordinator with contract management and UGC review for 45 creators

Digital Marketing Assistant — Sarova Hotels, Nairobi
January 2018 – May 2019 (1 year 4 months)
- Created and scheduled social media content; assisted with Google Display Network campaigns for hospitality promotions
- Built weekly paid media reports for the marketing manager

EDUCATION
BSc Computer Science (Marketing Minor) — University of Nairobi, 2018 (Second Class Upper)

CERTIFICATIONS
- TikTok for Business: Campaign Management Certified (2023)
- Meta Blueprint: Media Buying Professional (2024)
- AppsFlyer Measurement Certification (2022)

SKILLS
Performance Marketing | Paid Social | SEM | TikTok Ads | Mobile Attribution | Influencer Marketing | Team Leadership | GA4 | Meta Ads Manager | Google Ads | TikTok for Business | AppsFlyer | Adjust | Looker Studio

NOTABLE GAPS (for evaluator awareness)
- All management experience in food delivery app context, not physical product D2C or e-commerce
- No CRM/email marketing ownership (Glovo growth stack is app-first, no email programme managed)
- Vertical mismatch: consumer app vs. personal care/wellness D2C
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f07_yes",
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
