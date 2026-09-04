"""WHY: f32_no tests NO verdict in digital marketing context — email-only specialist with no paid media experience and below-threshold team size."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Five years of digital experience is email marketing only — no paid social, no SEM, no SEO — which does not satisfy the 'digital marketing' breadth requirement; additionally, the candidate manages one direct report (below the three-person threshold) and has no paid advertising budget whatsoever. Confidence: 93%."
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
WANJIKU GRACE KAMAU
Nairobi, Kenya | wanjiku.kamau@email.com | +254 720 467 293
LinkedIn: linkedin.com/in/wanjikugracekamau

PROFESSIONAL SUMMARY
Dedicated Email Marketing Specialist with 5 years of experience designing and executing lifecycle email programmes for large B2C organisations. Deep expertise in segmentation strategy, automated drip sequences, A/B testing frameworks, and CRM data hygiene. Passionate about delivering personalised, data-led communications that improve policyholder retention and cross-sell conversion.

WORK EXPERIENCE

Senior Email Marketing Specialist
Britam Insurance — Nairobi, Kenya
March 2020 – Present (4 years 5 months)

- Own end-to-end design and execution of all lifecycle email communications to Britam's existing policyholder database of 320,000+ contacts
- Build and manage automated drip sequences for policy renewal reminders, cross-sell campaigns (health to life, motor to travel), and lapse re-engagement flows
- Supervise 1 Email Marketing Coordinator responsible for HTML template QA, contact list uploads, and campaign scheduling
- Manage the Salesforce Marketing Cloud subscription (annual platform cost: KES 1.4M); no paid media advertising budget within my remit
- Achieved average email open rate of 34% across retention campaigns in 2023, against an industry benchmark of 21%
- Reduced policy lapse rate by 8 percentage points through a 6-touch automated renewal email sequence launched in Q1 2022
- Maintain contact database hygiene through monthly list cleaning, bounce management, and unsubscribe compliance (GDPR-aligned)
- Produce weekly email performance dashboards for the Head of Retention covering open rate, click-to-open rate, conversion to renewal, and unsubscribe rate

Email Marketing Executive
Old Mutual Kenya — Nairobi, Kenya
February 2019 – February 2020 (1 year)

- Executed monthly email newsletters and promotional campaigns for Old Mutual Kenya's retail wealth and investment products
- Managed Mailchimp account covering 45,000 subscribers; handled list segmentation and basic A/B subject line tests
- Collaborated with the content team to draft email copy aligned with Old Mutual's brand voice guidelines
- Reported on open rate and click-through rate performance to the marketing manager on a fortnightly basis

EDUCATION

Bachelor of Arts — Communications
United States International University Africa (USIU-Africa) — Nairobi, Kenya
Graduated: December 2018 | Second Class Honours

SKILLS & TOOLS
- Email Platforms: Salesforce Marketing Cloud (advanced), Mailchimp, HubSpot Email
- CRM: Salesforce CRM (basic data pulls), Microsoft Dynamics (read access)
- Analytics: Email open rate, click-to-open rate, conversion rate, bounce and unsubscribe tracking
- Design: Litmus (email rendering QA), Canva (basic HTML template edits)
- Languages: English (fluent), Kiswahili (fluent)

CERTIFICATIONS
- Salesforce Marketing Cloud Email Specialist Certification (2022)
- HubSpot Email Marketing Certification (2021)
- Google Digital Marketing Fundamentals (2019)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f32_no",
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
