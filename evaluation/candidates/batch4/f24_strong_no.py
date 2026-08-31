"""WHY: f24_strong_no tests STRONG_NO verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Eight years of senior marketing experience but entirely in traditional above-the-line channels (TV, radio, OOH, events); candidate explicitly states digital is agency-handled, and there is zero evidence of paid digital platform competency — a fundamental mismatch for a performance digital role. Confidence: 97%."
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
HARRISON ONYANGO ODHIAMBO
Nairobi, Kenya | harrison.odhiambo@email.com | +254 733 881 120
LinkedIn: linkedin.com/in/harrisonodhiambo

PROFESSIONAL SUMMARY
Seasoned Brand Manager with 8 years of experience in FMCG marketing across East Africa, specialising in above-the-line brand campaigns, sponsorship activation, and consumer promotions. Proven ability to manage large marketing budgets and agency relationships. Strong track record delivering brand health improvements and market share growth in competitive FMCG categories. Digital activation is managed in partnership with our retained digital agency team.

WORK EXPERIENCE

Brand Manager — Mainstream Spirits & Premium Lager
East African Breweries Limited (EABL) — Nairobi, Kenya
May 2020 – Present (4 years 3 months)

- Manage a total marketing budget of KES 15M/month covering TV production and airtime, radio, outdoor/OOH billboards, events and activations, and in-store point-of-sale materials
- Lead a cross-functional brand team of 4 (2 Brand Executives, 1 Events Coordinator, 1 Trade Marketing Executive)
- Brief and manage 3 retained agencies: JWT Nairobi (creative), Mindshare Kenya (media buying), and MediaVantage (OOH and activation)
- Delivered two award-winning TVC campaigns recognised at the Marketing Society of Kenya Awards (2022, 2023)
- Oversee TV and radio media buying (NTV, Citizen, K24, Classic 105, Radio Maisha) through agency; negotiate rate cards and value additions directly with broadcasters
- Spearhead brand sponsorship of major sporting events (Magical Kenya Open, Safari Rally) covering KES 3.2M annually
- Note: digital marketing activations (social media, online video, paid digital) are planned and executed exclusively by our retained digital agency — I provide brand briefs and approve creative; I do not operate digital platforms directly
- Conduct quarterly brand health tracking surveys and present findings to the Board Marketing Committee

Brand Executive
Unilever East Africa — Nairobi, Kenya
January 2018 – April 2020 (2 years 4 months)

- Supported brand managers on Sunlight, Omo, and Vaseline campaigns across Kenya and Uganda
- Coordinated radio and print media bookings through Mindshare East Africa
- Managed in-store activation logistics for MT (modern trade) and GT (general trade) channels
- Produced post-campaign performance reports for TV and radio campaigns using Nielsen audience data

Marketing Graduate Trainee
Nation Media Group — Nairobi, Kenya
June 2016 – December 2017 (1 year 7 months)

- Rotated through advertising sales, brand partnerships, and events teams
- Assisted with advertiser proposal decks, rate card management, and post-campaign reports

EDUCATION

BSc Marketing — Egerton University, Njoro
Graduated: 2016 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- Media: TV and radio media planning, OOH site selection, Nielsen audience reporting
- Brand: Brand health tracking (Kantar), consumer research, focus group facilitation
- Agency Management: Creative briefing, agency performance reviews, rate card negotiation
- Other: Microsoft PowerPoint, Excel, Word; Keynote

CERTIFICATIONS
- CIM (Chartered Institute of Marketing) — Diploma in Professional Marketing (2021)
- Marketing Society of Kenya — Senior Member (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f24_strong_no",
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
