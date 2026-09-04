"""WHY: f13_ambiguous tests AMBIGUOUS verdict where digital experience timeline, budget ownership, and team management are all unverifiable from CV alone."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "Strong education and 7 total years, but only 4 years are in digital marketing (post-agency transition), budget figures are client-aggregate and not personally owned, and 'works with junior staff' does not confirm 3+ direct reports — a phone screen is required to verify all three gate criteria. Confidence: 60%."
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
CAROLINE AKINYI ODERO
Nairobi, Kenya | caroline.odero@email.com | +254 733 209 445
LinkedIn: linkedin.com/in/carolineakinyi

PROFESSIONAL SUMMARY
Versatile marketing professional with 7 years of experience spanning traditional media, brand communications, and digital marketing. Strong foundation in integrated marketing communications with a proven ability to lead client engagements and deliver cross-channel campaign results. MBA-qualified with deep understanding of the Kenyan consumer market.

WORK EXPERIENCE

Senior Digital Marketing Strategist
Pulse Digital Agency — Nairobi, Kenya
February 2020 – Present (4 years 6 months)

- Lead digital marketing strategy across a portfolio of 8–12 FMCG, retail, and lifestyle client accounts
- Oversee client campaigns spanning Meta Ads, Google Ads, SEO, and email marketing; combined client digital ad spend exceeds several million shillings monthly
- Proficient in all major digital marketing platforms including paid social, search, programmatic display, and marketing automation
- Work closely with junior staff on campaign execution, creative briefing, and performance reporting
- Present monthly performance decks to senior client stakeholders and CMOs
- Contributed to agency winning two PRSK Awards for Digital Campaign Excellence (2022, 2023)

Marketing Executive — Print & Broadcast
Nation Media Group — Nairobi, Kenya
January 2017 – January 2020 (3 years)

- Developed and managed advertising campaigns for Nation FM and Daily Nation print editions
- Coordinated with clients on traditional media placements — radio spots, full-page and half-page print inserts
- Supported the brand team on corporate event activations and sponsorship management
- Produced post-campaign reports on reach, GRP, and print readership metrics
- Assisted digital team on occasional social media content (organic posts, no paid media)

EDUCATION

MBA — Marketing Specialisation
United States International University (USIU) Africa — Nairobi
Graduated: 2017 | Distinction

SKILLS & TOOLS
- Digital Platforms: Proficient in all major digital marketing platforms
- Analytics: Google Analytics, Facebook Insights, basic reporting dashboards
- Presentation: PowerPoint, Google Slides, Canva
- Project Management: Trello, Asana
- Languages: English (fluent), Kiswahili (fluent)

CERTIFICATIONS
- Google Digital Garage — Fundamentals of Digital Marketing (2020)
- HubSpot Inbound Marketing Certification (2021)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f13_ambiguous",
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
