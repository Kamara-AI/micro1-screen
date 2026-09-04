"""WHY: f09_ambiguous tests AMBIGUOUS verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate has 5 years total experience with unclear team size during 'team lead' period, "
    "no quantified ad spend figures anywhere in the CV, and a B2B SaaS background with no D2C or consumer marketing evidence; "
    "a phone screen is required to determine whether hard requirements are actually met. Confidence: 71%."
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
JAMES OMONDI ACHIENG
Nairobi, Kenya | james.achieng@gmail.com | +254 701 958 334 | linkedin.com/in/jamesomondi

PROFESSIONAL SUMMARY
Digital marketing professional with 5 years of experience spanning B2B SaaS and online talent platforms. Comfortable with GA4, Meta Ads, and Google Ads. Recently transitioned into a digital marketing team lead position where I manage campaigns and coordinate with the wider marketing team. Passionate about data-driven marketing and looking to grow into a senior management role.

WORK EXPERIENCE

Digital Marketing Team Lead — Ajira Digital, Nairobi
March 2023 – Present
- Lead digital marketing campaigns across Meta and Google Ads to promote Ajira's freelancer certification programme and platform growth
- Manage the team's day-to-day digital campaign execution and provide feedback on campaign performance
- Overseeing significant digital ad budgets for platform acquisition and brand awareness across Kenya and Uganda
- Coordinate with content and design colleagues to ensure campaign assets are delivered on time
- Report on campaign performance to the Head of Marketing weekly
- Tools used: GA4, Meta Ads Manager, Google Ads, Mailchimp, Google Search Console

Digital Marketing Specialist — Andela, Nairobi
January 2021 – February 2023 (2 years 1 month)
- Managed paid social and SEM campaigns for Andela's East Africa talent acquisition brand; primarily targeting software developers for the Andela platform
- Handled Google Ads and Facebook/Instagram campaigns independently as a sole contributor
- Produced monthly performance reports; tracked campaign CTR, CPL, and conversion rates across channels
- Supported SEO content calendar by briefing blog posts optimised for software developer search terms

Junior Digital Marketing Executive — Sendy, Nairobi
August 2019 – December 2020 (1 year 4 months)
- Assisted with digital campaign execution for Sendy Business (B2B logistics product)
- Created and scheduled social media posts across Facebook, Instagram, and Twitter
- Pulled weekly ad performance data from Meta and Google; compiled summary reports

EDUCATION
BSc Information Technology — Multimedia University of Kenya, Nairobi, 2019 (Second Class Lower)

CERTIFICATIONS
- Google Ads Search Certification (2023)
- Google Analytics Certification — GA4 (2022)
- Meta Blueprint: Digital Marketing Associate (2022)

SKILLS
Paid Social | SEM | SEO (basic) | Email Marketing | Campaign Reporting | GA4 | Meta Ads Manager | Google Ads | Mailchimp | Google Search Console

SCREENING NOTES (for evaluator awareness — not shown to AI)
- Hard requirement gaps that require phone screen to resolve:
  1. Team size at Ajira Digital is never stated; "team lead" title is present but whether 3+ direct reports exist is unknown
  2. No ad spend figures (KES or USD) given for any role; "significant budgets" is the only language used
  3. All experience is B2B SaaS / online platform — zero consumer, D2C, or FMCG marketing
  4. BSc IT does not perfectly match the degree requirement; adjacent but not a listed field
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f09_ambiguous",
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
