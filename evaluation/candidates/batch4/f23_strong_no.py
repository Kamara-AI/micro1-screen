"""WHY: f23_strong_no tests STRONG_NO verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Fresh graduate with 1 year of combined intern and junior-level experience; fails all four hard requirements — experience years, management, ad spend, and meaningful role seniority — with no path to a senior competency claim. Confidence: 98%."
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
MERCY WANJIKU KARIUKI
Nairobi, Kenya | mercy.kariuki@email.com | +254 790 312 567
LinkedIn: linkedin.com/in/mercywanjiku

PROFESSIONAL SUMMARY
Enthusiastic and motivated Junior Digital Marketing Executive with 1 year of hands-on experience gained through an internship at Safaricom PLC and a junior agency role. Eager to grow my career in performance marketing, content creation, and social media management. Quick learner with a strong foundation in digital marketing fundamentals.

WORK EXPERIENCE

Junior Digital Marketing Executive
Pixel Agency Kenya — Nairobi, Kenya
February 2025 – Present (6 months)

- Assist with scheduling and publishing organic social media content for 5 SME clients across Instagram, Facebook, and TikTok
- Draft weekly content calendars and caption copy for client approval
- Pull basic engagement metrics from Meta Business Suite and compile into monthly client reports
- Support the senior executive with campaign set-up tasks in Google Ads (no independent budget ownership)
- Coordinate with the design team for creative asset delivery

Digital Marketing Intern
Safaricom PLC — Nairobi, Kenya
August 2024 – January 2025 (6 months)

- Rotated through the Social Media, Digital Campaigns, and CRM teams under close supervision
- Assisted with community management across Safaricom's Twitter/X and Facebook pages (responding to comments, flagging escalations)
- Helped prepare campaign briefing decks and competitive landscape slides for internal stakeholders
- Observed and assisted in setting up basic Meta Ads boosted posts (no independent spend authority)
- Completed internal Safaricom Digital Academy modules in Google Analytics and SEO fundamentals

EDUCATION

BSc Marketing — University of Nairobi
Graduated: November 2024 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- Social Media: Instagram, TikTok, Facebook, Twitter/X
- Basic Exposure: Meta Business Suite, Google Ads (supervised), Google Analytics 4 (intro level)
- Content: Canva, CapCut, Google Workspace
- Other: Microsoft Office Suite

CERTIFICATIONS
- Google Digital Marketing & E-commerce Certificate (Coursera, 2024)
- HubSpot Social Media Marketing Certification (2024)

REFEREES
Available on request.
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f23_strong_no",
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
