"""WHY: f17_no tests NO verdict where total years look sufficient but digital-specific experience is only 2 years, budget is far below threshold, and team management is of agency relationships not digital staff."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Despite 6 total years in marketing, only 2 years involve digital channels; paid digital spend is KES 800K/month (far below KES 5M threshold); no direct management of digital marketing staff; and the role is fundamentally ATL/BTL brand management, not digital performance marketing — fails three hard requirements. Confidence: 93%."
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
GRACE WANJIKU KARIUKI
Nairobi, Kenya | grace.kariuki@email.com | +254 701 567 883
LinkedIn: linkedin.com/in/gracewanjiku-brand

PROFESSIONAL SUMMARY
Brand manager with 6 years of marketing experience in fast-moving consumer goods, specialising in ATL and BTL campaign execution, trade marketing, and brand equity management. Experienced in managing advertising agency relationships and coordinating multi-market activations across East Africa. Growing exposure to digital channels as part of integrated brand campaigns.

WORK EXPERIENCE

Brand Manager — Personal Care Division
Bidco Africa — Nairobi, Kenya
June 2021 – Present (3 years 2 months)

- Own brand strategy and 360° campaign execution for two personal care product lines (hair care and body lotion)
- Manage ATL/BTL marketing budget of KES 28M/year; digital social ads account for approximately KES 800K/month of this allocation
- Manage relationships with three advertising agencies (creative, media, and PR) — no direct management of in-house digital staff
- Coordinate annual brand activations in supermarkets, pharmacies, and open-air events across Nairobi, Mombasa, and Kisumu
- Brief creative agency on Facebook and Instagram ad content; review and approve copy and visuals; do not personally operate Ads Manager
- Track brand health metrics: share of voice, brand awareness scores, retail distribution coverage
- Familiar with Facebook Ads Manager and Google Analytics for reviewing reports prepared by agency

Marketing Executive — Trade & Activations
Procter & Gamble Kenya (Distributor Partner) — Nairobi, Kenya
March 2018 – May 2021 (3 years 3 months)

- Planned and executed in-store promotions and market activations for P&G product lines across 120+ outlets
- Coordinated with field sales teams, merchandisers, and promotional staff for campaign rollouts
- Managed BTL activity budgets, vendor payments, and logistics for nationwide activation events
- Produced post-activation reports on footfall, sampling numbers, and estimated sell-through

EDUCATION

BSc Marketing — Jomo Kenyatta University of Agriculture and Technology (JKUAT), Nairobi
Graduated: 2017 | Second Class Honours

SKILLS & TOOLS
- Brand Management: ATL/BTL campaign planning, brand equity tracking, consumer insight research
- Agency Management: creative briefing, media planning review, PR coordination
- Digital (Limited): Facebook Ads Manager (review/approval level), Google Analytics (reading reports)
- Tools: Nielsen Brandbank, PowerPoint, Excel, SAP (basic)

CERTIFICATIONS
- CIM Certificate in Marketing (2020)
- Nielsen FMCG Marketing Essentials (2019)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f17_no",
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
