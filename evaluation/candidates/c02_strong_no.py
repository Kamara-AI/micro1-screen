"""
WHY: c02 is the STRONG_NO calibration anchor — the hard-requirement failure case.
This candidate is not bad; they are simply the wrong seniority for the role by a
wide margin. A 2-year junior applying for a Staff Engineer role requiring 8+ years
is a hard knockout, not a nuanced judgment call. Any system that passes this
has a broken pre-filter.

HOW: Junior dev with 2 years experience, no quantified outcomes, skills that partially
overlap the role keywords but are not demonstrated at the required depth. Hard requirement
on years of experience fails immediately at Tier 1.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "STRONG_NO"
GROUND_TRUTH_RATIONALE: str = (
    "Hard requirement failure: role requires 8+ years of system design experience; candidate "
    "has 2 years total. This is not a close call — the gap is not bridgeable by any other "
    "signal. Skills listed match some role keywords (Docker, Python) but none are evidenced "
    "at Staff Engineer depth. No quantified outcomes across any role. All experience at "
    "micro/small companies. This is a STRONG_NO on hard requirements alone, Tier 1 reject."
)

CV_TEXT: str = """
DANIEL MWANGI
Nairobi, Kenya | daniel.mwangi.dev@gmail.com | github.com/dano-mwangi

SUMMARY
Passionate software developer with experience in Python and web development. Eager to grow
and take on new challenges in software engineering. Strong interest in distributed systems
and cloud technologies. Looking for opportunities to contribute to impactful projects.

EXPERIENCE

Junior Software Developer — BrightStack Solutions, Nairobi
June 2023 – Present (1 year 2 months)
- Worked on backend APIs using Python and Django
- Fixed bugs in the customer portal and helped with code reviews
- Assisted the senior team with database migrations
- Participated in daily standups and sprint planning

Software Developer Intern — TechHive Labs, Nairobi
Jan 2023 – May 2023 (5 months)
- Developed a simple CRUD application for internal inventory tracking
- Wrote unit tests for existing endpoints
- Shadowed senior developers during architecture discussions

Freelance Web Developer
2022 – 2023 (approx. 1 year, part-time)
- Built WordPress and basic Flask sites for 4 small local businesses
- Handled client communication and basic deployment on shared hosting

EDUCATION
Diploma in Information Technology — Kenya Institute of Management, Nairobi, 2022
Relevant coursework: Networking Fundamentals, Web Design, Database Administration

SKILLS
Python, Django, Flask, HTML/CSS, JavaScript (basic), MySQL, PostgreSQL (basic),
Docker (basic), Git, REST APIs, Linux command line

CERTIFICATIONS
- AWS Cloud Practitioner (2023)
- Google IT Support Certificate (2022)

PROJECTS
- Personal blog built on Flask, hosted on PythonAnywhere
- CLI task manager in Python (personal project, not published)

INTERESTS
Distributed systems, cloud architecture, open source (no contributions yet)
"""

JOB_DESCRIPTION: str = """
Staff Engineer — Platform Infrastructure
VaultCore Financial, Singapore (Remote-first)

VaultCore provides core banking infrastructure to 40+ neobanks across Southeast Asia and
East Africa. We process $3.2B in transactions monthly across 12 currencies. Our platform
team owns the foundational systems every other team builds on.

THE ROLE
You are a force-multiplier at the Staff level. This is not an individual contributor role
in the traditional sense — you will define the technical direction for our platform
infrastructure, own cross-team architecture decisions, and set the engineering standards
that 60+ engineers work within.

WHAT YOU WILL DO
- Define the 3-year technical roadmap for our core transaction processing platform
- Lead system design reviews for all projects touching payment data consistency
- Own and evolve our internal developer platform (golden paths, platform APIs, observability)
- Partner with VPs of Engineering across product lines on cross-cutting technical decisions
- Identify and retire technical debt that limits organisational velocity

REQUIREMENTS (hard)
- 8+ years of software engineering experience, including 3+ years at senior or above
- Demonstrable experience designing distributed systems at scale (>100K TPS or equivalent)
- Deep expertise in at least one of: Go, Rust, Java (JVM internals level)
- Prior experience in financial services, payments, or regulated infrastructure

WHAT WE ARE LOOKING FOR
- Track record of driving technical decisions that impacted 20+ engineers
- External thought leadership: conference talks, published papers, significant OSS contributions
- Comfort navigating ambiguity at the organisational level, not just the technical level

COMPENSATION
$180,000–$230,000 USD equivalent (location-adjusted) + equity
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c02_strong_no",
    role_seniority="staff",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "8+ years of software engineering experience",
        "3+ years at senior level or above",
        "distributed systems design at scale",
        "financial services or regulated infrastructure experience",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
