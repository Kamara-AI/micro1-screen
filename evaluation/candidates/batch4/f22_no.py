"""WHY: f22_no tests NO verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Ad spend of KES 2.2M/month is less than half the KES 5M threshold, and team size of 2 direct reports falls short of the 3-minimum; both hard gates fail simultaneously despite solid digital tooling and 6 years of experience. Confidence: 93%."
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
BONIFACE KIPCHOGE MUTAI
Nairobi, Kenya | boniface.mutai@email.com | +254 711 457 229
LinkedIn: linkedin.com/in/bonifacemutai

PROFESSIONAL SUMMARY
Digital Marketing Manager with 6 years of experience in the travel and tourism sector, specialising in performance campaigns targeting international leisure travellers and corporate clients. Proficient in Meta Ads, Google Ads, and TripAdvisor Ads for destination marketing. Strong analytical background with a focus on CPA optimisation for booking conversions.

WORK EXPERIENCE

Digital Marketing Manager
Safari Link Aviation — Nairobi, Kenya
April 2021 – Present (3 years 4 months)

- Manage Safari Link's digital advertising budget of KES 2.2M/month across Meta Ads, Google Ads (Search and Display), and TripAdvisor Sponsored Placements
- Lead a team of 2 digital marketers responsible for paid media execution and content scheduling
- Drive flight booking conversions for domestic routes (Wilson–Maasai Mara, Wilson–Amboseli, Wilson–Lamu) and charter packages
- Optimise Google Search campaigns targeting high-intent travellers searching for bush flights and safari packages
- Manage seasonal campaign cycles aligned with peak tourism seasons (Jan–Feb dry season, July–Oct Great Migration)
- Reduced cost per booking by 22% year-on-year through audience exclusions and bidding strategy refinements in Google Ads
- Coordinate with travel trade partners (Abercrombie & Kent, &Beyond) on co-branded digital placements
- Produce monthly GA4 dashboards for the Board covering CAC, revenue-per-booking, and channel attribution

Senior Digital Marketing Executive
TUI East Africa (formerly Thomson Travel) — Nairobi, Kenya
January 2019 – March 2021 (2 years 3 months)

- Executed digital campaigns for packaged holidays targeting UK and European travellers visiting Kenya and Tanzania
- Managed Google Display and Meta retargeting campaigns with a combined monthly budget of KES 900,000
- Built landing page A/B tests in Google Optimize, improving holiday booking form completion rate by 17%
- Coordinated email marketing to a database of 28,000 past travellers using Mailchimp

Digital Marketing Executive
Serena Hotels — Nairobi, Kenya
August 2018 – December 2018 (5 months)

- Supported the digital team with social media scheduling, paid post boosting, and weekly analytics reporting
- Assisted with TripAdvisor Business Advantage account management for 3 Kenyan Serena properties

EDUCATION

BCom Tourism Management — Moi University, Eldoret
Graduated: 2018 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- Paid Media: Meta Ads Manager, Google Ads (Search, Display, Shopping), TripAdvisor Ads
- Analytics: GA4, Google Data Studio, Google Optimize
- Email: Mailchimp
- Other: Microsoft Excel, Canva, HubSpot CRM (basic)

CERTIFICATIONS
- Google Ads Search Certification (2023)
- Meta Blueprint — Digital Marketing Associate (2022)
- Google Analytics Individual Qualification (2021)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f22_no",
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
