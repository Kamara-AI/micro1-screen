"""WHY: f42_strong_yes tests STRONG_YES verdict with large-budget e-commerce and international experience."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate far exceeds all hard requirements: 9 years digital marketing, 4+ years management, "
    "KES 10M/month budget, 5 direct reports regionally, MBA Marketing from INSEAD, and best-in-class "
    "metrics (5.2x Google Shopping ROAS, 28% CAC reduction) in large-scale e-commerce. Confidence: 98%."
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
DAVID OTIENO OCHIENG
Nairobi, Kenya | david.ochieng@outlook.com | +254 722 478 203
LinkedIn: linkedin.com/in/davidochiengke

PROFESSIONAL SUMMARY
Senior digital marketing leader with 9 years of experience driving e-commerce revenue for major retail and FMCG brands across East and Central Africa. Expert in high-budget performance marketing across Google Shopping, Meta, and programmatic channels. Proven track record of building and leading regional marketing teams, reducing CAC at scale, and delivering measurable business growth. MBA from INSEAD with a deep grounding in marketing strategy and consumer behaviour.

WORK EXPERIENCE

Digital Marketing Director — E-Commerce
Carrefour Kenya (Majid Al Futtaim Retail) — Nairobi, Kenya
July 2020 – Present

Carrefour Kenya is the country's largest hypermarket chain with a rapidly scaling e-commerce division, operating carrefourkeny.com and app-based ordering across Nairobi, Mombasa, and Kisumu.

- Own KES 10M/month digital advertising budget: Google Shopping (40%), Meta Ads (30%), programmatic display via DV360 (20%), TikTok (10%)
- Lead a regional digital marketing team of 5 direct reports in Nairobi, with dotted-line oversight of 3 additional specialists in Carrefour Uganda (Kampala)
- Google Shopping ROAS: 5.2x (up from 3.1x in Year 1); Meta ROAS: 4.1x on Performance+ campaigns
- Reduced blended customer acquisition cost by 28% over 2 years through Google PMax restructure and Meta Advantage+ audience testing
- Grew e-commerce monthly active customers from 42,000 to 185,000 over 3.5 years
- Launched Salesforce Marketing Cloud for email/CRM: email revenue attributed at 18% of total e-commerce GMV
- Introduced Klaviyo for loyalty segment re-engagement; cart abandonment recovery rate improved from 8% to 27%
- Built programmatic brand safety framework using DV360 + IAS; reduced wasted impressions by 41%
- Managed agency relationships for creative, localisation (Swahili/English), and influencer activations

Head of Digital Marketing
Naivas Supermarkets — Nairobi, Kenya
August 2017 – June 2020

Naivas is Kenya's largest homegrown supermarket chain with 90+ outlets and a growing digital footprint.

- Grew digital marketing function from 1-person operation to team of 4: 2 paid media, 1 SEO/content, 1 CRM
- Managed KES 4.5M/month paid digital budget (Meta and Google Ads)
- Launched Naivas online shopping pilot in partnership with Glovo; drove 28,000 first orders in 6 months
- Grew organic search traffic 220% in 24 months via structured SEO programme (Ahrefs, Screaming Frog)
- Introduced GA4 and Data Studio dashboards replacing manual Excel reporting; saved 12 analyst-hours/week

Digital Marketing Analyst
Safaricom PLC — Nairobi, Kenya
September 2015 – July 2017

- Supported performance marketing campaigns across M-Pesa, Safaricom Home Fibre, and handset promotions
- Managed Google Ads campaigns: combined spend ~USD 25,000/month across Search and Display
- Built automated weekly reporting in Google Data Studio; distributed to 3 business units
- Assisted SEO team: keyword research, on-page audits, backlink analysis using SEMrush

EDUCATION

Master of Business Administration — Marketing & Strategy
INSEAD — Paris, France (Fontainebleau/Singapore campuses)
Graduated: June 2015

Bachelor of Business Administration — Marketing
United States International University – Africa (USIU), Nairobi
Graduated: May 2013 | Second Class Upper

CERTIFICATIONS
- Google Ads Certified (all tracks including Performance Max) — 2024
- Meta Blueprint Certified Media Buying Professional — 2023
- DV360 Programmatic Certified — Google — 2022
- Salesforce Marketing Cloud Email Specialist — 2021

SKILLS & TOOLS
- Paid: Google Ads (Shopping, PMax, Display, Search), Meta Ads (Performance+, Advantage+), DV360, TikTok for Business
- Analytics: GA4, Google Tag Manager, Google Merchant Center, Looker Studio
- CRM/Email: Salesforce Marketing Cloud, Klaviyo, HubSpot
- SEO: Ahrefs, SEMrush, Screaming Frog
- Data: SQL (intermediate), Excel (advanced), Python (basic data manipulation)
- Leadership: team building, cross-border team management, agency management, media planning and forecasting

LANGUAGES
English (native), Swahili (fluent), French (conversational)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f42_strong_yes",
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
