"""WHY: f43_strong_yes tests STRONG_YES verdict with USD-denominated budget and technical depth."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate exceeds all hard requirements: 6 years digital marketing, 3 years management, "
    "USD 45,000/month ad spend (above USD 35,000 threshold), 5 direct reports, BSc from UoN, "
    "exceptional growth metrics (merchant base 8K to 45K), and rare technical attribution depth. Confidence: 95%."
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
FAITH NJERI KAMAU
Nairobi, Kenya | faith.kamau@gmail.com | +254 733 561 047
LinkedIn: linkedin.com/in/faithnjerikamau

PROFESSIONAL SUMMARY
Data-driven digital marketing leader with 6 years of experience driving merchant and consumer acquisition for East Africa's leading B2B e-commerce platforms. Unique combination of marketing strategy, performance advertising, and engineering cross-functionality — including building internal attribution dashboards from scratch. Managed USD 45,000/month digital advertising budgets, led multi-disciplinary teams, and delivered 5x merchant growth over three years. Passionate about marketing systems that are measurable end-to-end.

WORK EXPERIENCE

Head of Digital Marketing
Wasoko (formerly Sokowatch) — Nairobi, Kenya
February 2021 – Present

Wasoko is a pan-African B2B e-commerce platform connecting FMCG brands to informal retailers (dukas) across Kenya, Tanzania, Rwanda, and Senegal. The platform operates a D2C-adjacent model where merchant acquisition is driven through digital channels.

- Own and manage USD 45,000/month digital advertising budget across Meta Business Suite (35%), Google Ads (30%), TikTok for Business (20%), and programmatic (15%)
- Lead digital team of 5 direct reports: 2 paid media specialists, 1 SEO/content lead, 1 CRM/email marketer, 1 data analyst
- Drove merchant base growth from 8,000 to 45,000 active merchants over 3 years — 462% growth
- Achieved ROAS of 4.4x across paid channels; blended merchant CAC of USD 18 (vs. USD 31 benchmark at onboarding)
- Built an internal marketing attribution dashboard in Python + Google Looker Studio integrating GA4, Meta CAPI, and Google Ads API — replaced a USD 4,200/month third-party tool
- Scaled TikTok for Business merchant acquisition: zero to 22,000 followers, contributing 11% of new merchant sign-ups in Q3 2023
- Launched HubSpot CRM integration for merchant lifecycle marketing: onboarding email sequences increased 30-day merchant activation from 54% to 79%
- Ran SEMrush-led SEO programme: grew organic sessions from 5,200 to 38,000/month in 24 months
- Managed influencer/affiliate programme with 60 micro-influencers in informal trade verticals

Digital Marketing Analyst → Senior Digital Marketing Executive
Twiga Foods — Nairobi, Kenya
August 2018 – January 2021

Twiga Foods is a Kenyan agri-tech platform linking farmers to urban retailers via a mobile-first B2B marketplace.

- Managed Google Search and Display campaigns (USD 8,000–12,000/month) for retailer acquisition
- Built Mailchimp email sequences for vendor onboarding; open rate improved from 18% to 36% in 6 months
- Supported SEO content calendar: 45 articles published in 18 months; organic traffic grew 180%
- Created weekly performance dashboards in GA4 and Data Studio distributed to leadership team
- Promoted from Analyst to Senior Executive within 14 months based on attribution modelling contribution

EDUCATION

Bachelor of Science — Computer Science (with Marketing Minor)
University of Nairobi
Graduated: June 2018 | Second Class Upper Honours

CERTIFICATIONS
- Google Ads Certified (Search, Shopping, Performance Max, Display) — 2023
- Meta Blueprint Certified Media Buying Professional — 2022
- TikTok for Business Marketing Science Certification — 2023
- HubSpot Marketing Hub Certified — 2022
- SEMrush SEO Toolkit Certified — 2022

SKILLS & TOOLS
- Paid Channels: Meta Business Suite (Ads Manager, CAPI, Meta Pixel), Google Ads (PMax, Shopping, Search, UAC), TikTok for Business
- Analytics: GA4, Google Tag Manager, Looker Studio, Mixpanel
- CRM & Email: HubSpot, Klaviyo, Mailchimp
- SEO: SEMrush, Ahrefs, Screaming Frog
- Technical: Python (pandas, requests, matplotlib), SQL (intermediate), Google Ads API, Meta Marketing API
- Leadership: team management, media planning, attribution modelling, agency briefing, budget forecasting

LANGUAGES
English (fluent), Swahili (native), Kikuyu (conversational)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f43_strong_yes",
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
