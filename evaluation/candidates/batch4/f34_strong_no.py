"""WHY: f34_strong_no tests STRONG_NO verdict — influencer with no formal employment, no degree, and no marketing team management; fails every hard requirement."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "No degree (KCSE only), no formal employment history, no team management, and no experience as a digital marketer — being a content creator and brand ambassador is categorically different from performance marketing management; fails all four hard requirements with zero ambiguity. Confidence: 99%."
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
AMINA NALEDI SHEIKH
Nairobi, Kenya | amina.naledi@email.com | +254 700 574 821
Instagram: @aminanaledi_ke (180K followers) | TikTok: @aminanaledi (90K) | YouTube: AminaNaledi (25K subscribers)

PROFESSIONAL SUMMARY
Full-time content creator and lifestyle influencer with 5 years of building an engaged, loyal audience across Instagram, TikTok, and YouTube. Specialise in beauty, wellness, and personal care content resonating with Kenyan women aged 18–34. Experienced in executing paid brand campaigns, long-term brand ambassador partnerships, and affiliate-linked product promotion. Ready to bring my audience knowledge and content expertise into a professional marketing environment.

WORK EXPERIENCE

Self-Employed Content Creator & Brand Ambassador
Independent — Nairobi, Kenya
January 2020 – Present (4 years 8 months)

- Grown Instagram following from 12,000 to 180,000 organically through consistent beauty and lifestyle content, achieving average engagement rate of 6.8%
- Built TikTok channel to 90,000 followers; videos regularly reach 200,000–500,000 views on trending audio formats
- YouTube channel at 25,000 subscribers; produce weekly long-form skincare tutorials and product review videos averaging 18,000 views per video
- Managed brand ambassador deals with 14 brands including Nivea Kenya, AMARA Beauty, and Dettol Kenya — negotiated deliverables, usage rights, and payment terms directly with brand managers
- Delivered sponsored content campaigns covering product integrations, unboxing hauls, affiliate discount codes, and giveaway activations
- Tracked campaign performance metrics (reach, impressions, story views, link clicks, affiliate conversion rates) and reported results to brand partners
- All campaign budgets (brand fees, production costs) flowed to me as talent compensation — I was the creator, not the campaign manager on the brand side

Cashier
Nakumatt Supermarkets — Nairobi, Kenya
July 2018 – November 2019 (1 year 4 months)

- Processed customer transactions at till, handled cash and M-Pesa payments
- Assisted in store restocking and shelf arrangement during off-peak hours

EDUCATION

Kenya Certificate of Secondary Education (KCSE)
Loreto High School, Msongari — Nairobi, Kenya
Completed: November 2017 | Grade: B+

SKILLS & TOOLS
- Content Creation: Instagram Reels, TikTok, YouTube long-form, short-form video editing (CapCut, InShot)
- Analytics: Instagram Insights, TikTok Creator Analytics, YouTube Studio
- Brand Collaboration: Brief interpretation, usage rights negotiation, affiliate tracking links
- Community Management: DM engagement, comment moderation, brand Q&A sessions
- Languages: English (fluent), Kiswahili (fluent), Somali (conversational)

CERTIFICATIONS
- None (self-taught creator)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f34_strong_no",
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
