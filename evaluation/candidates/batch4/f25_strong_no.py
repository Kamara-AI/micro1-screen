"""WHY: f25_strong_no tests STRONG_NO verdict in digital marketing context."""
from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Fails all four hard requirements: no formal degree (online certificate only), 3 years of experience vs 5+ required, zero team management as a solo freelancer, and negligible ad spend of KES 80,000/month across all clients combined versus the KES 5M threshold. Confidence: 99%."
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
BRENDA ACHIENG OLOO
Nairobi, Kenya | brenda.achieng@gmail.com | +254 798 045 312
Instagram: @brendamarkets | TikTok: @brendaachiengsocials

PROFESSIONAL SUMMARY
Self-taught freelance Social Media Manager and content creator with 3 years of experience helping Kenyan small businesses grow their online presence. Manage organic content strategies and small-scale Meta Ads campaigns for 12 active SME clients. Passionate about community building and authentic storytelling. Fully remote, self-directed workflow.

WORK EXPERIENCE

Freelance Social Media Manager
Self-Employed — Nairobi, Kenya
July 2021 – Present (3 years 1 month)

- Manage Instagram, TikTok, and Facebook organic content for 12 Kenyan SME clients spanning beauty salons, clothing boutiques, a catering business, and a fitness studio
- Create and schedule 4–6 posts per week per client using Canva and Buffer
- Run small Meta Ads campaigns on behalf of select clients — total combined Meta Ads spend across all 12 clients is approximately KES 80,000/month (average KES 6,500 per client per month, primarily boosted posts)
- Grew one client's Instagram following from 1,200 to 8,400 in 14 months through consistent posting and hashtag strategy
- Produce simple monthly performance reports covering follower growth, post reach, and engagement rate
- Handle client onboarding, scope-of-work agreements, and monthly invoicing independently

EDUCATION

Certificate in Digital Marketing — Google (Google Digital Garage, online)
Completed: March 2021

SKILLS & TOOLS
- Social Media: Instagram, TikTok, Facebook, Twitter/X, YouTube (basic)
- Content Creation: Canva, CapCut, Adobe Express
- Scheduling: Buffer, Meta Business Suite
- Ads: Meta Ads (boosted posts, basic Ads Manager — small budgets)
- Other: Google Workspace, WhatsApp Business

NOTABLE CLIENT RESULTS
- Glam by Grace (beauty salon, Westlands): 600% follower growth in 12 months
- Thrift & Chic (fashion boutique, CBD): 3x increase in DM enquiries after TikTok content strategy
- FitSpace Nairobi (fitness studio): launched Instagram Reels series generating 28,000 plays

TESTIMONIALS
"Brenda transformed our Instagram presence — she truly understands our audience." — Grace Wanjiru, Glam by Grace
"Professional, creative, and always on time." — Kevin Maina, Thrift & Chic

REFEREES
Available on request.
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="f25_strong_no",
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
