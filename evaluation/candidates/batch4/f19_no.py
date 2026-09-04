"""WHY: f19_no tests NO verdict where the candidate is in the wrong domain entirely — PR and communications with zero paid digital marketing experience."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "PR and communications is a categorically different function from digital marketing — zero paid media experience, no ROAS/CAC metrics, no digital ad budget ownership, and organic social channel management does not substitute for performance marketing; fails at least three of the four hard requirements. Confidence: 96%."
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
LUCY ADHIAMBO OUMA
Nairobi, Kenya | lucy.ouma@email.com | +254 724 891 076
LinkedIn: linkedin.com/in/lucyadhiambo-pr

PROFESSIONAL SUMMARY
Strategic communications professional with 5 years of experience in corporate PR, media relations, and brand reputation management at one of Kenya's largest media companies. Skilled in crisis communications, executive profiling, stakeholder engagement, and editorial content. Manages digital presence for corporate accounts as part of an integrated communications strategy.

WORK EXPERIENCE

PR & Communications Manager
Nation Media Group — Nairobi, Kenya
February 2021 – Present (3 years 6 months)

- Lead corporate communications strategy for Nation Media Group, managing relationships with over 80 journalists, editors, and broadcast producers across print, radio, and TV
- Draft and distribute press releases, media advisories, speeches, and executive statements
- Manage NMG's corporate Twitter and LinkedIn accounts (organic): schedule posts, respond to stakeholder queries, and escalate crisis situations
- Coordinate all external communications during corporate events including shareholder meetings, editorial conferences, and CSR activations
- Manage a team of 2 PR coordinators responsible for media monitoring, press clipping, and event logistics
- Oversee media monitoring using Meltwater and Cision; produce monthly share-of-voice and sentiment reports for the CEO and board
- No paid digital advertising responsibilities; all social media activity is organic and editorial

Communications Officer
Nation Media Group — Nairobi, Kenya
March 2019 – January 2021 (1 year 11 months)

- Assisted with press release drafting and distribution to NMG's media contact database
- Scheduled and published organic social media content on Twitter, Facebook, and LinkedIn
- Supported logistics for press conferences, media roundtables, and editorial briefings
- Compiled daily media monitoring summaries for the communications director

EDUCATION

BA Communications — United States International University (USIU) Africa, Nairobi
Graduated: 2018 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- PR & Media: Cision, Meltwater, ResponseSource, media pitching, crisis comms playbooks
- Social Media (Organic): Hootsuite, Buffer, Twitter/X, LinkedIn, Facebook
- Content: Microsoft Word, PowerPoint, Google Docs, Canva (basic)
- Monitoring: Brand24 (basic), Google Alerts
- Other: Zoom, Teams, Asana

CERTIFICATIONS
- PRSK (Public Relations Society of Kenya) — Member in Good Standing (2020)
- Coursera: Crisis Communications (Northwestern University, 2021)
- Hootsuite Social Media Marketing Certification (2019)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f19_no",
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
