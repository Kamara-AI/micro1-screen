"""WHY: f21_no tests NO verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Manages a KES 4.5M/month influencer budget — below the KES 5M threshold — but more critically, her entire career is influencer/creator economy management with zero paid social, SEM, or SEO competency; core performance marketing channels are entirely absent. Confidence: 91%."
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
ZAWADI AKINYI OTIENO
Nairobi, Kenya | zawadi.otieno@email.com | +254 722 198 034
LinkedIn: linkedin.com/in/zawadiakinyi

PROFESSIONAL SUMMARY
Seasoned Influencer Marketing Manager with 5 years of experience building and scaling creator partnership programmes for blue-chip brands across East Africa. Deep expertise in influencer sourcing, contract negotiation, campaign seeding, and creator relationship management. Passionate about authentic brand storytelling through human voices.

WORK EXPERIENCE

Influencer Marketing Manager
Ogilvy Africa — Nairobi, Kenya
February 2021 – Present (3 years 6 months)

- Lead Ogilvy Africa's influencer marketing practice for 8 brand clients including FMCG, beauty, and telecoms verticals
- Manage a monthly influencer budget of KES 4.5M across all clients, covering creator fees, product seeding, gifting, and campaign production
- Supervise 2 Influencer Coordinators responsible for day-to-day creator communications and content scheduling
- Built a proprietary creator shortlisting framework adopted agency-wide, reducing vetting time by 40%
- Delivered an average Earned Media Value (EMV) of 3.2x on influencer spend across Q3 and Q4 2023
- Maintain active relationships with 180+ Kenyan and East African content creators across Instagram, TikTok, and YouTube
- Oversee monthly creator reporting decks covering reach, engagement rate, story views, and swipe-up conversions

Influencer & Partnerships Executive
Dentsu Kenya — Nairobi, Kenya
March 2019 – January 2021 (1 year 11 months)

- Executed influencer seeding campaigns for 4 client brands, managing a combined creator roster of 60+ individuals
- Drafted and negotiated creator contracts in collaboration with the legal and finance teams
- Produced post-campaign EMV and sentiment analysis reports for client presentations
- Coordinated product dispatch, briefing documents, and content approval workflows across creator partnerships

EDUCATION

BA Marketing — United States International University Africa (USIU-Africa), Nairobi
Graduated: 2019 | Second Class Honours

SKILLS & TOOLS
- Influencer Platforms: AspireIQ, Upfluence, Grin, Modash
- Reporting: EMV tracking, Engagement Rate benchmarking, Story View-through Rate
- Project Management: Asana, Trello, Notion
- Communication: Slack, Microsoft Teams, Google Workspace
- Content Review: Instagram Creator Studio, TikTok Creator Marketplace

CERTIFICATIONS
- Influencer Marketing Association (IMA) — Certified Influencer Marketing Professional (2022)
- Google Digital Marketing Fundamentals (2020)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f21_no",
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
