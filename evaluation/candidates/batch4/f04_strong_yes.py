"""WHY: f04_strong_yes tests STRONG_YES verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_YES"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate dramatically exceeds all hard requirements with 10 years experience, KES 12M/month spend, "
    "a team of 8, an MBA, D2C e-commerce pedigree at Kilimall and Masoko, and independently verifiable national award recognition. Confidence: 99%."
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
DAVID MURIITHI KARIUKI
Nairobi, Kenya | david.kariuki@dmkconsulting.co.ke | +254 722 017 745 | linkedin.com/in/davidmuriithikariuki

PROFESSIONAL SUMMARY
Award-winning digital marketing executive and D2C e-commerce specialist with 10 years of experience across Kenya's top e-commerce brands. Former Marketing Director at Kilimall; currently an independent consultant advising Kenyan brands on growth, paid media, and CRM strategy. Named in the "Top 40 Under 40 in Marketing" 2023 by Marketing Africa magazine and winner of IAB Kenya's "Best Digital Campaign" 2022. Deep expertise in scaling performance marketing operations and influencer programmes for East African consumer audiences.

WORK EXPERIENCE

Independent Digital Marketing Consultant — DMK Consulting, Nairobi
January 2024 – Present
- Advising 3 Kenyan consumer brands on paid media strategy, influencer programme design, and CRM stack selection
- Retained consultant for Masoko (Safaricom e-commerce platform): led restructure of KES 4M/month Meta and Google campaigns, improving ROAS from 2.1x to 3.6x in 3 months

Marketing Director (Digital) — Kilimall Kenya, Nairobi
June 2019 – December 2023 (4 years 6 months)
- Owned and scaled digital advertising budget from KES 4M to KES 12M/month across Meta, Google, TikTok, and programmatic display
- Led marketing team of 8: 3 paid media specialists, 2 SEO/content specialists, 1 email/CRM analyst, 1 influencer programme manager, 1 data analyst
- Managed influencer and affiliate programme with 200+ active Kenyan creators; contributed 29% of total monthly revenue
- Delivered "Best Digital Campaign Kenya 2022" — IAB Kenya — for Kilimall's 7th Anniversary Sale campaign (3-week Meta + TikTok campaign, ROAS 6.2x)
- Introduced HubSpot CRM stack; segmented email list from a single blast to 12 behavioural journeys; email revenue grew 210% in 18 months
- Grew Kilimall's organic search traffic by 88% in 2 years via in-house SEO programme
- Tools: GA4, Meta Business Suite, Google Ads, TikTok Ads Manager, DV360, HubSpot, Mailchimp, SEMrush, Ahrefs, Looker Studio

Digital Marketing Manager — Masoko (Safaricom), Nairobi
August 2016 – May 2019 (2 years 9 months)
- Managed KES 3.5M/month paid social and SEM budget for Safaricom's e-commerce platform launch
- Supervised team of 3; introduced Meta dynamic product ads that reduced cart abandonment rate by 31%
- Led SEO and content strategy for Masoko.com from zero to 280,000 monthly organic sessions in 18 months

Digital Marketing Associate — Saatchi & Saatchi, Nairobi
September 2014 – July 2016 (1 year 10 months)
- Executed paid social and search campaigns for FMCG clients including Procter & Gamble East Africa
- Produced campaign analytics reports presented to C-suite stakeholders monthly

EDUCATION
MBA (Marketing) — University of Edinburgh Business School, Edinburgh, UK, 2013 (Distinction)
BA Economics — University of Nairobi, 2011

AWARDS & RECOGNITION
- IAB Kenya "Best Digital Campaign" 2022
- Marketing Africa "Top 40 Under 40 in Marketing" 2023
- Shortlisted: PRSK Digital Excellence Award 2021

CERTIFICATIONS
- Google Ads Search & Shopping Certification (2024)
- Meta Blueprint: Advanced Media Buying (2023)
- HubSpot Marketing Hub Certified (2023)

SKILLS
Digital Strategy | Performance Marketing | SEO/SEM | Email/CRM | Influencer & Affiliate Management | Team Leadership | GA4 | Meta Business Suite | Google Ads | TikTok Ads Manager | DV360 | HubSpot | Mailchimp | SEMrush | Ahrefs | Looker Studio
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f04_strong_yes",
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
