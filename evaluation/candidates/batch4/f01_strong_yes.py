"""WHY: f01_strong_yes tests STRONG_YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate exceeds all four hard requirements with 8 years experience, KES 9M/month ad spend, "
    "a team of 6, a relevant degree, and elite D2C e-commerce metrics across all channels from a directly comparable Kenyan brand. Confidence: 97%."
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
AMARA WANJIKU ODHIAMBO
Nairobi, Kenya | amara.odhiambo@gmail.com | +254 722 881 034 | linkedin.com/in/amaraodhiambo

PROFESSIONAL SUMMARY
Results-driven Digital Marketing Director with 8 years of experience scaling D2C and e-commerce brands across East Africa. Deep expertise in performance marketing, CRM, and multi-channel campaign management. Certified Google Ads and Meta Blueprint professional. Currently overseeing KES 9M/month in digital ad spend at Twiga Foods.

WORK EXPERIENCE

Digital Marketing Director — Twiga Foods, Nairobi
January 2022 – Present
- Own and allocate KES 9M/month digital advertising budget: Meta Ads (40%), Google Ads (35%), TikTok for Business (25%)
- Lead a cross-functional team of 6: 4 digital marketing specialists, 1 data analyst, 1 content creator
- Achieved ROAS of 4.2x on Meta and 3.8x on Google for the Twiga Direct consumer app launch campaign
- Reduced customer acquisition cost (CAC) from KES 580 to KES 340 in 14 months through landing page and audience optimisation
- Built and scaled email CRM programme using Klaviyo; current email open rate 38%, click-through rate 9.4%
- Managed influencer programme with 85 active Kenyan micro-creators; drove 22% of new customer acquisitions in Q4 2023
- Tools: GA4, Meta Business Suite, Google Ads, TikTok Ads Manager, HubSpot, Klaviyo, Looker Studio

Digital Marketing Manager — Jumia Kenya, Nairobi
March 2019 – December 2021 (2 years 9 months)
- Led paid social and SEM campaigns during peak seasons (Black Friday, Jumia Anniversary Sale) with budgets up to KES 6M/month
- Managed a team of 3 performance marketing specialists
- Delivered 3.5x ROAS across Meta and Google campaigns during 2021 sale events
- Introduced GA4 migration roadmap adopted company-wide ahead of the UA sunset

Digital Marketing Specialist — Safaricom PLC, Nairobi
August 2016 – February 2019 (2 years 6 months)
- Executed Google Search and Display campaigns for M-PESA merchant acquisition
- Supported SEO content strategy that grew organic traffic 67% in 18 months

EDUCATION
BSc Marketing — University of Nairobi, 2016 (Second Class Upper)

CERTIFICATIONS
- Google Ads Search Certification (valid 2024)
- Google Ads Display Certification (valid 2024)
- Meta Blueprint: Media Buying Professional (valid 2024)

SKILLS
Performance Marketing | SEO/SEM | Email CRM | Influencer Management | Team Leadership | GA4 | Meta Business Suite | Google Ads | TikTok Ads Manager | HubSpot | Klaviyo | Looker Studio | Ahrefs | Data Analysis
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f01_strong_yes",
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
