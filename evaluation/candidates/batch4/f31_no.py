"""WHY: f31_no tests NO verdict in digital marketing context — trade/BTL marketing background with zero digital spend ownership."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Five years of marketing experience at Twiga Foods is trade and BTL marketing exclusively — in-store displays, distributor promotions, and field activations — with zero paid digital advertising budget ownership; the role type, not the years of experience, is the disqualifier. Confidence: 95%."
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
KIPCHOGE BRIAN MUTAI
Nairobi, Kenya | kipchoge.mutai@email.com | +254 711 342 087
LinkedIn: linkedin.com/in/kipchogemutai

PROFESSIONAL SUMMARY
Results-driven Trade Marketing professional with 5 years of experience driving retail execution, BTL activations, and distributor engagement across Kenya's FMCG sector. Proven track record building brand presence at the point of sale and managing large field teams in fast-paced, high-distribution environments. Passionate about translating brand strategy into shelf-level impact.

WORK EXPERIENCE

Trade Marketing Manager
Twiga Foods Ltd — Nairobi, Kenya
August 2019 – Present (5 years)

- Develop and implement trade marketing calendars covering 8 product categories across modern trade, wholesale, and informal retail channels (dukas, kiosks)
- Manage in-store display standards across 1,200+ Twiga-serviced retail outlets in Nairobi, Mombasa, and Central Kenya regions
- Lead a field team of 12 merchandisers and 3 area supervisors responsible for outlet coverage, planogram compliance, and stock availability reporting
- Coordinate quarterly distributor promotions — rebate schemes, push incentives, co-funded activations — with a BTL activation budget of KES 3.8M/quarter
- Negotiate and execute POSM (Point-of-Sale Material) placements: gondola ends, branded coolers, shelf talkers, and floor displays
- Run sell-through analytics using Twiga's internal distributor data portal; produce monthly trade performance dashboards for the commercial director
- Collaborate with the brand team on above-the-line campaign localisation for below-the-line adaptation at the outlet level
- Achieved 97% planogram compliance across top 200 accounts in Q2 2023, up from 71% in Q1 2022

Trade Marketing Executive
Unga Group Ltd — Nairobi, Kenya
June 2018 – July 2019 (1 year 1 month)

- Supported the trade marketing team in executing BTL activations for Jogoo and Bakwell brands across urban and peri-urban markets
- Managed product sampling campaigns at 40+ market events and retail activations per quarter
- Tracked merchandiser daily route plans and field productivity via paper-based reporting systems
- Assisted in building the first digital route-to-market tracker using Google Sheets, reducing supervisor reporting time by 25%

EDUCATION

Bachelor of Arts — Marketing
Egerton University — Njoro, Kenya
Graduated: June 2019 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- Trade Execution: Planogram design, POSM briefing and procurement, outlet segmentation
- Field Management: Salesforce automation, route planning, field force productivity tracking
- Reporting: Excel, Google Sheets, Twiga internal distributor dashboards
- BTL Activations: Sampling events, in-store promotions, roadshows, distributor conferences
- Languages: English (fluent), Kiswahili (fluent), Kalenjin (conversational)

CERTIFICATIONS
- CIM Kenya — Introduction to Trade Marketing (2021)
- Shopper Marketing Fundamentals — Nielsen Academy Online (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f31_no",
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
