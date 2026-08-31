"""WHY: f14_ambiguous tests AMBIGUOUS verdict where a senior title exists but company size makes budget and team thresholds implausible — and no numbers are provided anywhere."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "Five years total experience and a 'Head of Digital' title are present, but the 12-person startup context makes KES 5M+/month spend highly implausible, team size under the threshold of 3 direct reports is likely, and zero quantitative metrics anywhere on the CV prevent a confident pass or fail — a phone screen is required. Confidence: 55%."
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
DIANA MUTHONI GITHINJI
Nairobi, Kenya | diana.githinji@email.com | +254 700 128 976
LinkedIn: linkedin.com/in/dianamuthoni

PROFESSIONAL SUMMARY
Creative and analytical digital marketer with 5 years of experience building brand presence and driving online sales for consumer fashion brands. Grew from social media management into a cross-functional leadership role. Passionate about data-informed marketing, community building, and the Kenyan fashion ecosystem.

WORK EXPERIENCE

Head of Digital
Vazi Nation (Fashion Startup) — Nairobi, Kenya
May 2022 – Present (2 years 3 months)

- Promoted to Head of Digital following consistent performance as Digital Marketing Specialist
- Oversee all digital marketing channels including social media (Instagram, TikTok, Facebook), email, and paid advertising
- Manage the digital marketing budget and make decisions on channel allocation
- Lead the digital team in planning and executing seasonal campaigns aligned with fashion drops
- Report directly to the CEO on digital channel performance and growth initiatives
- Coordinate with external creatives, photographers, and social media collaborators

Digital Marketing Specialist
Vazi Nation (Fashion Startup) — Nairobi, Kenya
March 2021 – April 2022 (1 year 2 months)

- Executed organic and paid social media campaigns on Meta and TikTok
- Managed the brand's email newsletter using Mailchimp; grew subscriber list organically
- Created content calendars, wrote captions, and briefed photographers for campaign shoots
- Set up and monitored Google Analytics (Universal Analytics) for website traffic reporting

Social Media Manager
Kijiji Looks — Nairobi, Kenya
August 2019 – February 2021 (1 year 7 months)

- Managed Instagram and Facebook pages for a boutique streetwear brand
- Grew combined social media following from 4,200 to 18,000 organically over 18 months
- No paid advertising responsibilities in this role

EDUCATION

BA Communications — Daystar University, Nairobi
Graduated: 2019 | Second Class Honours

SKILLS & TOOLS
- Social Media: Meta Business Suite, TikTok, Instagram, Facebook
- Email: Mailchimp
- Analytics: Google Analytics (Universal Analytics)
- Design: Canva, Adobe Lightroom (basic)
- Other: Google Workspace, Notion

CERTIFICATIONS
- Meta Blueprint — Social Media Marketing (2022)
- Canva for Business Certificate (2021)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f14_ambiguous",
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
