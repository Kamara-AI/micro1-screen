"""WHY: f15_ambiguous tests AMBIGUOUS verdict where experience and team management exist but paid budget is below threshold and the team managed is content, not performance marketing."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "Six years of experience and formal team management are clear, but the paid media budget (KES 2.5M/month) is below the KES 5M threshold, and the 'content team of 4' does not satisfy the digital marketing team management criterion — a phone screen is needed to determine whether broader budget responsibility exists. Confidence: 58%."
)

JOB_DESCRIPTION: str = """
Senior Digital Marketing Manager — Kweli Commerce Ltd
Nairobi, Kenya | Remote-first (quarterly in-перformance (quarterly in-person)

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
ERIC KAMAU NJENGA
Nairobi, Kenya | eric.njenga@email.com | +254 711 894 230
LinkedIn: linkedin.com/in/erickamaunjenga

PROFESSIONAL SUMMARY
Content-led digital marketer with 6 years of experience in financial services and banking. Strong track record in organic growth, editorial content strategy, and brand-led SEO. People manager with experience leading content teams. Complementary paid media exposure supporting broader digital campaigns.

WORK EXPERIENCE

Content & Digital Marketing Manager
KCB Group — Nairobi, Kenya
April 2020 – Present (4 years 4 months)

- Lead all digital content and organic marketing activity for KCB's retail banking digital channels
- Manage a content team of 4: 2 content writers, 1 graphic designer, and 1 social media coordinator
- Oversee SEO strategy; grew KCB.co.ke organic traffic by 85% over 3 years through on-page optimisation, technical fixes, and a structured content calendar
- Own email marketing programme for retail customers: 280,000-subscriber list, average open rate 29%, CTR 2.1%
- Support paid media team on campaign briefs and creative direction; personally manage KES 2.5M/month in Meta Ads for product launches and seasonal promotions
- Develop brand content strategy aligned with KCB's corporate communications and compliance team guidelines
- Produce quarterly digital performance reports for the CMO and Group Marketing Director

Digital Marketing Officer
KCB Group — Nairobi, Kenya
January 2018 – March 2020 (2 years 3 months)

- Executed social media strategy across Facebook, Twitter, Instagram, and LinkedIn
- Created and published organic content; moderated community interactions
- Assisted with Google Ads and Meta Ads campaign setup under senior manager's supervision
- Coordinated with agencies on PR amplification and influencer gifting initiatives

EDUCATION

BSc Marketing — Kenyatta University, Nairobi
Graduated: 2017 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- SEO: SEMrush, Ahrefs, Google Search Console, Screaming Frog
- Paid Media: Meta Ads Manager (intermediate), Google Ads (basic)
- Email: Mailchimp, Salesforce Marketing Cloud (basic)
- Analytics: GA4, Google Data Studio, Looker Studio
- Content: WordPress, Canva, Adobe Express

CERTIFICATIONS
- Google Analytics 4 Certification (2023)
- HubSpot Content Marketing Certification (2022)
- SEMrush SEO Fundamentals (2021)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f15_ambiguous",
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
