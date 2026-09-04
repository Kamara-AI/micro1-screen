"""WHY: f11_yes tests YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Meets all four hard requirements — 6 years experience with 2+ years management, KES 5.4M/month ad spend, team of 3 direct reports, and BSc Marketing from Strathmore — with solid ROAS and SEO growth metrics despite operating at a slightly smaller scale than Kweli. Confidence: 88%."
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
AMARA NJERI WAWERU
Nairobi, Kenya | amara.waweru@email.com | +254 712 344 890
LinkedIn: linkedin.com/in/amarawaweru

PROFESSIONAL SUMMARY
Results-driven E-commerce Marketing Manager with 6 years of progressive digital marketing experience, including 2.5 years in a people-management role. Deep expertise in performance marketing, SEO, and CRM for Kenyan D2C e-commerce. Proven track record growing organic traffic and delivering consistent ROAS across Meta and Google channels.

WORK EXPERIENCE

E-commerce Marketing Manager
Maisha Mart — Nairobi, Kenya
March 2022 – Present (2 years 5 months)

- Own and manage KES 5.4M/month digital advertising budget across Meta Ads and Google Ads (Shopping, Search, Display)
- Lead a team of 3 digital marketing specialists (1 paid media, 1 SEO/content, 1 email/CRM)
- Achieved and maintained ROAS of 2.9x on Meta Ads across personal care and home-goods product lines
- Grew organic search traffic by 140% in 18 months through technical SEO audits, content strategy, and backlink acquisition using Ahrefs
- Built and scaled email marketing programme from 42,000 to 115,000 subscribers; average open rate 26%, CTR 3.8%
- Launched Maisha Mart affiliate programme, onboarding 65 Kenyan micro-influencers, contributing 12% of monthly revenue
- Reduced customer acquisition cost (CAC) from KES 1,450 to KES 980 over 12 months through audience segmentation and creative testing

Digital Marketing Specialist
Jumia Kenya — Nairobi, Kenya
June 2019 – February 2022 (2 years 9 months)

- Managed Google Shopping and Search campaigns for electronics and fashion verticals (budget KES 1.8M/month)
- Supported senior manager on Meta Ads strategy; executed A/B tests on ad creatives and landing pages
- Produced weekly performance reports in GA4 and Google Data Studio for stakeholders
- Collaborated with the merchandising team to align promotional campaigns with inventory cycles

Marketing Executive (Graduate Trainee)
Safaricom PLC — Nairobi, Kenya
August 2018 – May 2019 (10 months)

- Rotated across Brand, Digital, and Customer Experience teams as part of the graduate programme
- Assisted with social media scheduling, community management, and campaign asset coordination

EDUCATION

BSc Marketing — Strathmore University, Nairobi
Graduated: 2018 | Upper Second Class Honours

SKILLS & TOOLS
- Paid Media: Meta Business Suite, Google Ads, TikTok for Business
- Analytics: GA4, Google Data Studio, Ahrefs, SEMrush
- CRM & Email: Mailchimp, Klaviyo
- E-commerce: Shopify, WooCommerce
- Other: Microsoft Excel (advanced), Canva, Notion

CERTIFICATIONS
- Google Ads Search Certification (2024)
- Meta Blueprint — Media Buying Professional (2023)
- HubSpot Email Marketing Certification (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f11_yes",
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
