"""WHY: f03_strong_yes tests STRONG_YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate meets all hard requirements with 7 years experience, KES 6.5M/month spend, "
    "a team of 5, a relevant degree, and major brand-scale outcomes including leading Equity Eazzy app to 3.2M users. Confidence: 95%."
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
CYNTHIA AKINYI MWANGI
Nairobi, Kenya | cynthia.mwangi@gmail.com | +254 711 302 558 | linkedin.com/in/cynthiaakinyi

PROFESSIONAL SUMMARY
Senior digital marketing professional with 7 years of experience in performance marketing, programmatic advertising, and CRM across financial services and agency environments in Kenya. Led digital acquisition campaigns that grew Equity Bank's flagship mobile product to 3.2M active users. Skilled in managing large integrated teams and enterprise-grade martech stacks.

WORK EXPERIENCE

Digital Marketing Manager — Equity Bank Kenya, Nairobi
March 2020 – Present
- Manage KES 6.5M/month digital advertising budget across Google Ads, Meta Ads, and programmatic display (DV360)
- Lead a team of 5: 3 paid media specialists, 1 SEO analyst, 1 CRM specialist (Salesforce Marketing Cloud)
- Spearheaded digital acquisition strategy for Equity Eazzy App; app grew from 1.1M to 3.2M active users under my campaigns
- Achieved 28% year-on-year reduction in CAC through audience segmentation and programmatic bid strategy optimisation
- Launched and managed Salesforce Marketing Cloud journeys; reduced churn among app users by 17% in 12 months
- Tools: GA4, DV360, Campaign Manager 360, Salesforce Marketing Cloud, Ahrefs, Looker Studio, Google Search Console

Digital Strategist — Ogilvy Africa (WPP), Nairobi
January 2017 – February 2020 (3 years 1 month)
- Led digital strategy for 6 major accounts including KCB Group, Britam, and Unilever East Africa
- Planned and executed integrated digital campaigns across paid, earned, and owned channels; managed budgets up to KES 4M/month per client
- Mentored 2 junior digital executives; co-led the agency's Google Ads Centre of Excellence training programme
- Delivered a 42% improvement in organic traffic for Unilever's East Africa brand portfolio through SEO audit and content strategy refresh

Junior Digital Executive — Scanad Kenya, Nairobi
June 2015 – December 2016 (1 year 7 months)
- Supported paid social and SEM campaign execution for FMCG and telco clients
- Produced weekly performance dashboards distributed to 3 client accounts

EDUCATION
BA Communications (Media and Advertising) — United States International University – Africa (USIU-A), Nairobi, 2017 (Second Class Upper)

CERTIFICATIONS
- Google Ads Search Certification (2024)
- Display & Video 360 Certification — Google Marketing Platform (2023)
- Salesforce Marketing Cloud Email Specialist (2022)

SKILLS
Programmatic Advertising | Paid Social | SEM | SEO | CRM/Email Automation | Team Leadership | DV360 | Campaign Manager 360 | Google Ads | Meta Ads Manager | Salesforce Marketing Cloud | GA4 | Ahrefs | Looker Studio
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f03_strong_yes",
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
