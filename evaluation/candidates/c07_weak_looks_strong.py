"""
WHY: c07 is the "keyword-stuffed impressive-looking CV" trap. This is the hardest
case for naive systems — the titles are impressive, the companies are recognisable,
the skills list is long. But a careful reading reveals: no quantification anywhere,
passive maintainer language throughout ('managed', 'oversaw', 'ensured', 'supported'),
no team sizes, no outcomes. An ATS would rank this candidate top 5%. SCREEN should
see through the surface signals and score NO.

HOW: The silence flags are the key: for a Director-level candidate, the complete
absence of quantification, team sizes, and outcome evidence is a high-severity silence
flag pattern. The builder/maintainer verdict should be "maintainer" with high confidence.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "NO"
GROUND_TRUTH_RATIONALE: str = (
    "CV is keyword-rich but evidence-empty. Impressive titles (Director, Head of Engineering) "
    "and recognisable companies, but every bullet uses passive maintainer language: 'managed', "
    "'oversaw', 'ensured', 'supported'. Zero quantified outcomes across 7 years and 4 roles. "
    "No team sizes ever stated (critical silence flag for leadership roles). No architectural "
    "decisions described. No mention of what was built, launched, or shipped. For a Principal "
    "Engineer role, this is a NO: the candidate cannot demonstrate the builder track record "
    "or the measurable impact the role requires. Confidence: 38%."
)

CV_TEXT: str = """
VICTOR OMONDI OTIENO
Nairobi, Kenya | victor.omondi.tech@gmail.com | linkedin.com/in/victor-omondi-otieno

PROFESSIONAL SUMMARY
Experienced technology leader with 7+ years driving digital transformation across enterprise
and startup environments. Proven track record of managing cross-functional engineering teams,
overseeing complex technical projects, and ensuring delivery of high-quality software products.
Passionate about engineering excellence, team culture, and technology strategy.

EXPERIENCE

Director of Engineering — Safaricom PLC, Nairobi
Jan 2022 – Present
- Managed the engineering function for the M-PESA Super App division
- Oversaw delivery of multiple product features across mobile and backend teams
- Ensured alignment between engineering roadmap and business objectives
- Supported the CTO in strategic technology planning and vendor management
- Managed relationships with external technology partners and vendors

Head of Engineering — Cellulant Corporation, Nairobi
Apr 2019 – Dec 2021
- Led engineering teams responsible for payment processing infrastructure
- Oversaw the migration of legacy systems to cloud infrastructure
- Ensured compliance with PCI-DSS and relevant regulatory requirements
- Managed the performance review process for engineering staff
- Supported recruitment efforts for the engineering department

Senior Software Engineer — Craft Silicon, Nairobi
Aug 2017 – Mar 2019
- Worked on core banking software for financial institutions
- Supported maintenance and enhancement of existing product modules
- Participated in client requirements gathering and documentation
- Assisted in testing and QA processes before major releases

Software Developer — Ushahidi, Nairobi
2016 – 2017
- Contributed to open source platform development
- Managed tasks assigned by senior developers
- Ensured timely completion of assigned development tickets

EDUCATION
BSc Computer Science — Jomo Kenyatta University of Agriculture and Technology, 2016

TECHNICAL SKILLS
Java, Python, JavaScript, Node.js, React, AWS, Azure, Docker, Kubernetes, Agile/Scrum,
JIRA, Confluence, Salesforce, Tableau, MySQL, PostgreSQL, MongoDB, Redis, Kafka, Terraform,
GraphQL, REST APIs, Microservices, CI/CD, Jenkins, GitHub Actions

CERTIFICATIONS
- AWS Solutions Architect Associate
- PMP (Project Management Professional)
- Certified ScrumMaster (CSM)

INTERESTS
Technology leadership, digital transformation, team building, engineering culture
"""

JOB_DESCRIPTION: str = """
Principal Engineer — Platform
Wasoko (Series B, $125M raised), Nairobi (Hybrid)

Wasoko is Africa's largest B2B e-commerce platform. We connect 200,000+ informal retailers
to FMCG suppliers across 7 countries. Our engineering team of 45 works on the systems that
power $1.4B in annual GMV. We are preparing for our Series C and need a Principal Engineer
to lead our platform re-architecture.

THE ROLE
This is a deeply technical individual contributor role. You will design the next generation
of our order management, fulfilment, and logistics platform — systems that need to scale
10x over the next 24 months. You will influence the entire engineering organisation through
technical standards, design reviews, and architectural guidance.

WHAT YOU WILL DO
- Lead the technical design of our next-generation OMS and logistics orchestration layer
- Own the architecture decisions for systems that 40+ engineers build on top of
- Drive measurable improvements in platform reliability, throughput, and developer experience
- Represent technical depth in the hiring loop: design the bar for senior and staff ICs

REQUIREMENTS
- 8+ years software engineering, including 3+ years at senior or principal level
- Demonstrable experience designing systems at 100K+ transactions/day scale
- Track record of shipping significant platform changes with measurable outcomes
- Deep expertise in one or more: Go, Java, Python

WHAT WE ARE LOOKING FOR
- Someone who can point to specific systems they designed and explain the trade-offs they made
- Quantified evidence of impact — we do not hire on titles
- Builder mindset: you have zero-to-one history, not just maintenance history

COMPENSATION
KES 500,000–700,000/month + equity
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c07_weak_looks_strong",
    role_seniority="staff",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "8+ years software engineering",
        "3+ years at senior or principal level",
        "systems design at scale — demonstrable",
        "quantified evidence of impact required",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
