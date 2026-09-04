"""WHY: f06_yes tests YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate satisfies all four hard requirements (5 years, KES 5.2M/month, 4 direct reports, BSc Commerce) "
    "with solid retail/FMCG results, but has no TikTok exposure and limited pure D2C or advanced CRM tooling. Confidence: 80%."
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
GEORGE KIPCHOGE ROTICH
Nairobi, Kenya | george.rotich@gmail.com | +254 718 664 307 | linkedin.com/in/georgekipchoge

PROFESSIONAL SUMMARY
Digital Marketing Manager with 5 years of experience in retail and FMCG digital marketing. Currently leading a 4-person digital team at Naivas Supermarkets, managing KES 5.2M/month in paid media and driving meaningful online order growth through performance-focused Meta and Google campaigns. Strong on paid social, SEM, and email. Looking to grow into a more advanced D2C role with greater channel diversity.

WORK EXPERIENCE

Digital Marketing Manager — Naivas Supermarkets, Nairobi
March 2021 – Present
- Manage KES 5.2M/month digital advertising budget across Meta Ads (55%) and Google Ads (45%)
- Lead a team of 4 digital marketing specialists covering paid social, paid search, email, and content
- Achieved average ROAS of 3.0x across Meta and Google over 2023; peak ROAS 3.9x during festive season campaigns
- Grew Naivas online order volume by 180% in 2 years through continuous landing page optimisation, audience segmentation, and promotional calendar management
- Oversee email marketing via Mailchimp to a list of 190,000 subscribers; current open rate 24%, CTR 6.1%
- Managed 18 local food and lifestyle influencers for campaign activations; tracked reach and conversion via UTM-tagged landing pages
- Tools: GA4, Meta Business Suite, Google Ads, Mailchimp, Google Search Console, Looker Studio, Canva

Digital Marketing Executive — Naivas Supermarkets, Nairobi
February 2019 – February 2021 (2 years)
- Executed paid social and SEM campaigns under direction of Head of Marketing
- Produced weekly paid media performance dashboards; coordinated with creative team on ad assets
- Supported email campaign calendar; built and scheduled Mailchimp campaigns for weekly promotions

EDUCATION
BSc Commerce (Marketing Concentration) — Jomo Kenyatta University of Agriculture and Technology (JKUAT), Nairobi, 2019 (Second Class Upper)

CERTIFICATIONS
- Google Ads Search Certification (2023)
- Meta Blueprint: Media Planning Professional (2022)
- Google Analytics Certification — GA4 (2023)

SKILLS
Paid Social | SEM | Email Marketing | SEO | Influencer Coordination | Team Leadership | GA4 | Meta Business Suite | Google Ads | Mailchimp | Looker Studio | Google Search Console | Canva

NOTABLE GAPS (for evaluator awareness)
- No TikTok for Business experience; Naivas did not run TikTok paid campaigns during tenure
- No Klaviyo or HubSpot experience; CRM work limited to Mailchimp
- Background is traditional retail (physical-first with online component), not pure D2C
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f06_yes",
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
