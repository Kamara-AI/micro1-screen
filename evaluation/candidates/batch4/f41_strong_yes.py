"""WHY: f41_strong_yes tests STRONG_YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate exceeds all hard requirements: 7 years digital marketing with 4 years management, "
    "KES 7.5M/month ad spend above threshold, team of 7 direct reports, BCom Marketing from Strathmore, "
    "and outstanding metrics (3.9x ROAS, 44% email open rate) in a D2C-adjacent fintech context. Confidence: 96%."
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
AMARA WANJIKU MUTHONI
Nairobi, Kenya | amara.muthoni@gmail.com | +254 712 334 891
LinkedIn: linkedin.com/in/amaramuthoni

PROFESSIONAL SUMMARY
Results-driven Growth Marketing Director with 7 years of experience scaling digital acquisition for high-growth Kenyan technology and fintech brands. Proven track record managing multi-million shilling digital advertising budgets across Meta, Google, and TikTok. Skilled team leader with deep expertise in performance marketing, CRM, and data-driven attribution. Passionate about building marketing systems that scale efficiently in East African markets.

WORK EXPERIENCE

Growth Marketing Director
Lipa Later Limited — Nairobi, Kenya
March 2022 – Present

Lipa Later is Kenya's leading Buy Now Pay Later (BNPL) fintech platform with a strong D2C acquisition model targeting individual consumers across East Africa.

- Own and optimise KES 7.5M/month digital advertising budget: Meta Ads (45%), Google Ads (35%), TikTok for Business (20%)
- Lead a cross-functional growth team of 7: 3 paid media specialists, 2 CRM/email marketers, 1 SEO specialist, 1 data analyst
- Achieved 2.1M app installs over 30 months at a blended CAC of KES 290 — 18% below target
- Maintained ROAS of 3.9x across paid channels, with Meta Performance+ delivering 4.2x in Q2 2024
- Email open rate consistently at 44% (vs. 22% industry benchmark) through aggressive list hygiene and Klaviyo segmentation
- Built and scaled influencer affiliate programme: 85 active creators generating 14% of monthly new user volume
- Implemented Appsflyer MMP for cross-channel attribution; reduced mis-attributed installs by 62%
- Partnered with product team to run 40+ A/B experiments on landing pages, reducing bounce rate from 58% to 31%

Digital Marketing Manager
Sendy Limited — Nairobi, Kenya
January 2020 – February 2022

Sendy is a Kenyan logistics and last-mile delivery platform serving both B2B and consumer segments.

- Managed KES 3.2M/month paid digital budget across Meta and Google Ads
- Led team of 3 direct reports: 2 paid media executives and 1 content strategist
- Grew B2C rider acquisition by 140% in 12 months; reduced CAC by 22% through Google UAC optimisation
- Launched TikTok presence from zero: 85,000 followers in 8 months, driving 12% of new customer sign-ups
- Owned SEO roadmap: grew organic sessions from 18,000 to 71,000/month in 18 months using Ahrefs and Semrush

Digital Marketing Executive
Cellulant Corporation — Nairobi, Kenya
June 2017 – December 2019

- Supported paid social and SEM campaigns across 6 African markets
- Managed Google Ads and Facebook Ads for client accounts with combined spend of USD 18,000/month
- Produced weekly performance dashboards in GA4 and Data Studio; presented insights to C-suite monthly
- Assisted with SEO content strategy; contributed to 55% growth in organic traffic over 18 months

EDUCATION

Bachelor of Commerce — Marketing (First Class Honours)
Strathmore University, Nairobi
Graduated: June 2017

CERTIFICATIONS
- Google Ads Certified (Search, Display, Shopping, Video) — 2023
- Meta Blueprint Certified Media Buyer — 2022
- TikTok for Business Certified — 2023
- Klaviyo Product Certified — 2022
- Appsflyer Measurement Certified — 2023

SKILLS & TOOLS
- Paid Channels: Meta Business Suite (Ads Manager, Meta Pixel, CAPI), Google Ads (Search, Shopping, Display, PMax, UAC), TikTok for Business
- Analytics & Attribution: GA4, Google Tag Manager, Appsflyer, Mixpanel
- CRM & Email: Klaviyo, Mailchimp, HubSpot
- SEO: Ahrefs, SEMrush, Screaming Frog
- Data: Looker Studio, Excel (advanced), basic SQL
- Team leadership, budget forecasting, media planning, influencer management

LANGUAGES
English (fluent), Swahili (native)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f41_strong_yes",
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
