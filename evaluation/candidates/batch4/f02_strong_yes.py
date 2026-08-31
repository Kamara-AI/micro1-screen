"""WHY: f02_strong_yes tests STRONG_YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate surpasses all hard requirements with 9 years experience, USD 42,000/month ad budget, "
    "a 7-person growth team, a relevant degree, and exceptional measurable outcomes (5.1x ROAS, 34% CAC reduction) in D2C FMCG. Confidence: 98%."
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
BRIAN OTIENO KAMAU
Nairobi, Kenya | brian.kamau@outlook.com | +254 733 460 219 | linkedin.com/in/brianotieno-kamau

PROFESSIONAL SUMMARY
Growth marketing leader with 9 years of experience driving customer acquisition and retention across D2C FMCG and fintech in East Africa. Proven track record managing seven-figure USD ad budgets, scaling cross-functional growth teams, and compounding LTV through data-led CRM strategy. Currently Head of Growth at Copia Global Kenya.

WORK EXPERIENCE

Head of Growth — Copia Global Kenya, Nairobi
February 2021 – Present
- Own USD 42,000/month (approx. KES 5.9M) digital advertising budget across Google Ads, Meta Ads Manager, and TikTok for Business
- Lead a 7-person growth team: 3 paid media specialists, 2 CRM/email specialists, 1 SEO analyst, 1 data analyst
- Achieved ROAS of 5.1x across paid channels; reduced blended CAC by 34% in 18 months through creative testing and funnel optimisation
- Scaled email subscriber list from 80,000 to 310,000 via lifecycle automation in Klaviyo; open rate improved from 19% to 33%
- Built affiliate programme with 60 community resellers; programme contributes 18% of monthly GMV
- Tools: GA4, Google Ads, Meta Ads Manager, TikTok for Business, Klaviyo, Ahrefs, Looker Studio, Segment

Growth Lead — Sendy, Nairobi
July 2019 – January 2021 (1 year 7 months)
- Managed KES 3.8M/month performance marketing budget across Meta and Google for SME logistics acquisition
- Led team of 3 growth marketers; introduced weekly experiment retrospectives that reduced wasted spend by 21%
- Grew Sendy Business active accounts by 140% in 12 months

Performance Marketing Manager — Cellulant, Nairobi
May 2017 – June 2019 (2 years 1 month)
- Executed multi-market digital campaigns for AgriPay and Tingg payment products across Kenya, Uganda, and Ghana
- Managed Google Search, Display, and Facebook campaigns; combined budget approx. KES 2.5M/month
- Introduced UTM tracking standards adopted across all Cellulant digital properties

Digital Marketing Executive — Safaricom PLC, Nairobi
August 2015 – April 2017 (1 year 8 months)
- Supported M-PESA SME campaign execution; produced monthly paid media performance reports for leadership

EDUCATION
BCom Business Administration — Strathmore University, Nairobi, 2015 (First Class Honours)

CERTIFICATIONS
- Google Ads Search Certification (2024)
- Meta Blueprint: Marketing Science Professional (2023)
- HubSpot Marketing Hub Certified (2022)

SKILLS
Growth Strategy | Paid Social | SEM | SEO | Email/CRM | Affiliate Marketing | Team Leadership | GA4 | Google Ads | Meta Ads Manager | TikTok for Business | Klaviyo | Ahrefs | Segment | Looker Studio
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f02_strong_yes",
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
