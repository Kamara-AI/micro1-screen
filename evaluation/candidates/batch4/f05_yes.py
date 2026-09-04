"""WHY: f05_yes tests YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate clears all four hard requirements (6 years, KES 5.5M/month, 3 direct reports, BSc Marketing) "
    "but lacks TikTok experience and any D2C or e-commerce background, making her a qualified but not exceptional fit. Confidence: 82%."
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
FAITH NEKESA SIMIYU
Nairobi, Kenya | faith.simiyu@gmail.com | +254 700 813 421 | linkedin.com/in/faithnekesa

PROFESSIONAL SUMMARY
Senior digital marketing professional with 6 years of experience in paid media, SEM, and digital brand management within Kenya's telecommunications sector. Currently managing a KES 5.5M/month digital advertising budget at Safaricom PLC and leading a team of 3 marketing specialists. Recognised for delivering strong ROAS on M-PESA merchant acquisition campaigns. Seeking to bring my performance marketing skills into the D2C consumer goods space.

WORK EXPERIENCE

Senior Digital Marketing Manager — Safaricom PLC, Nairobi
April 2021 – Present
- Own KES 5.5M/month digital advertising budget allocated across Google Ads (60%) and Meta Ads (40%)
- Lead a team of 3 digital marketing specialists covering paid search, paid social, and email campaigns
- Delivered 3.2x ROAS on Meta campaigns for M-PESA merchant acquisition across Nairobi, Mombasa, and Kisumu
- Managed Google Search campaigns driving 2.1M clicks in 2023 for Safaricom Home Fibre product at a cost-per-lead of KES 290, 18% below target
- Oversaw email marketing to a subscriber base of 420,000; open rate 27%, CTR 5.8% using Mailchimp
- Coordinated with 12 brand ambassador influencers for product launches; managed briefs, approvals, and performance reporting
- Tools: GA4, Google Ads, Meta Business Suite, Mailchimp, Google Search Console, Looker Studio

Digital Marketing Executive — Safaricom PLC, Nairobi
July 2018 – March 2021 (2 years 8 months)
- Executed paid social and SEM campaigns for Safaricom consumer products (Bonga Points, Skiza, Home Fibre)
- Produced weekly performance reports for the Head of Digital Marketing
- Supported SEO strategy that improved organic rankings for 34 target keywords to page 1 in 12 months

EDUCATION
BSc Marketing — Kenyatta University, Nairobi, 2018 (Second Class Upper)

CERTIFICATIONS
- Google Ads Search Certification (2024)
- Google Analytics Certification — GA4 (2023)
- Mailchimp Email Marketing Foundations (2022)

SKILLS
Paid Search | Paid Social | SEM | Email Marketing | SEO | Team Leadership | GA4 | Google Ads | Meta Business Suite | Mailchimp | Looker Studio | Google Search Console | Campaign Reporting

NOTABLE GAPS (for evaluator awareness)
- No TikTok for Business experience (telecoms org did not use TikTok as a paid channel)
- No direct D2C or e-commerce experience; all roles in telecommunications
- Influencer experience limited to 12 brand ambassadors vs. the 120+ creator scale in JD
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f05_yes",
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
