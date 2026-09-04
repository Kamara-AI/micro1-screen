"""WHY: f16_no tests NO verdict where years of experience is just under threshold, management is absent, and budget is below minimum."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "Fails three of four hard requirements: 4.5 years experience (vs 5+ required), no people-management experience as an individual contributor throughout, and KES 3M/month ad spend (vs KES 5M+ required) — good technical profile but does not clear the gate criteria. Confidence: 92%."
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
FELIX OMONDI ONYANGO
Nairobi, Kenya | felix.onyango@email.com | +254 728 443 112
LinkedIn: linkedin.com/in/felixonyango-pm

PROFESSIONAL SUMMARY
Data-driven performance marketing specialist with 4.5 years of experience in app growth and mobile user acquisition. Expert in Meta, Google UAC, and mobile measurement platforms. Consistently delivered below-target CPIs and above-benchmark ROAS for high-volume app install campaigns in the East African market.

WORK EXPERIENCE

Senior Performance Marketing Specialist
Bolt Kenya (Taxify) — Nairobi, Kenya
March 2022 – Present (2 years 5 months)

- Manage KES 3M/month in paid user acquisition campaigns across Meta Ads and Google UAC targeting Android and iOS users in Kenya and Uganda
- Run continuous A/B testing on ad creatives, audiences, and bidding strategies; improved CPI by 22% over 12 months
- Sole owner of campaign performance; collaborate with regional marketing leads in Tallinn on strategy alignment
- Build weekly and monthly performance dashboards in GA4 and Looker Studio; present findings to the Kenya Country Manager
- Coordinate with the creative team on ad asset briefs; no direct management of creative or marketing staff
- Integrated Adjust MMP for granular attribution across all Bolt Kenya paid channels

Performance Marketing Specialist
Bolt Kenya (Taxify) — Nairobi, Kenya
February 2020 – February 2022 (2 years)

- Executed app install campaigns on Meta and Google under the direction of the Regional Marketing Manager
- Managed campaign budgets up to KES 1.2M/month across Nairobi and Mombasa geo targets
- Built custom audiences from CRM data exports; improved retargeting CTR by 35%
- Reported on weekly acquisition metrics: installs, CPI, ROAS, day-7 and day-30 retention

EDUCATION

BSc Computer Science — University of Nairobi
Graduated: 2020 | Second Class Honours (Upper Division)

SKILLS & TOOLS
- Paid Media: Meta Business Suite, Google Ads (UAC, Search, Display), YouTube Ads
- App Attribution: Adjust, AppsFlyer, Firebase
- Analytics: GA4, Looker Studio, BigQuery (basic SQL)
- Automation: Google Ads Scripts (basic), Zapier
- Other: Excel (advanced), Notion, Slack

CERTIFICATIONS
- Google Ads Mobile Certification (2024)
- Meta Blueprint — Media Planning Professional (2023)
- Adjust Certified Measurement Specialist (2022)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f16_no",
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
