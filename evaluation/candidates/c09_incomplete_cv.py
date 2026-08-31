"""
WHY: c09 tests AMBIGUOUS routing — the case where the CV provides insufficient
evidence to make a confident verdict either way. The candidate is not obviously
bad or obviously good; they are genuinely unknown. This is the case that
distinguishes a thoughtful system from one that forces a binary decision.

HOW: No dates on any role, skills listed but never connected to outcomes, company
names given but no descriptions of what was done, no education context, no
achievements. The data is technically present but analytically empty. The correct
output is AMBIGUOUS with a low confidence score and a recommendation for a
phone screen, not a pass/fail verdict.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "AMBIGUOUS"
GROUND_TRUTH_RATIONALE: str = (
    "Insufficient evidence to make a verdict. CV contains role titles and company names but "
    "no dates (so tenure and trajectory are unknown), no achievement descriptions in any role, "
    "skills listed but never evidenced in role context, and no education dates or context. "
    "Cannot assess: years of experience, career trajectory, depth of any skill, or whether "
    "stated skills were used in professional contexts. The right call is AMBIGUOUS — recommend "
    "a 20-minute phone screen to fill the evidence gaps before making a pass/fail decision. "
    "Confidence: 49%."
)

CV_TEXT: str = """
MICHAEL KIPKEMEI
Eldoret, Kenya | mkipkemei@gmail.com

WORK HISTORY

Software Developer — TechGroup Africa
Responsibilities: Software development and maintenance of company systems.

Full Stack Developer — Innovate Solutions Ltd
Responsibilities: Web development projects, client communication, technical support.

Junior Developer — DataBridge Systems
Responsibilities: Assisted with development tasks and system maintenance.

IT Support / Developer — KenyaLink Technology Services
Responsibilities: Provided technical support and developed internal tools.

TECHNICAL SKILLS
Python, JavaScript, PHP, Laravel, Django, React, Vue.js, MySQL, PostgreSQL,
MongoDB, Docker, AWS, Linux, Git, REST APIs, WordPress

EDUCATION
Diploma in Computer Science
Bachelor of Science in Information Technology

ADDITIONAL INFORMATION
Available to start immediately. Willing to relocate. Have worked on various
projects across different industries. Strong team player and quick learner.
References available on request.
"""

JOB_DESCRIPTION: str = """
Mid-Level Software Engineer — Full Stack
BuildFast Africa, Nairobi (Remote-friendly)

BuildFast is a 15-person software agency building digital products for East African
SMEs. We work on 4–6 client projects simultaneously across fintech, health, and
logistics verticals.

THE ROLE
You will work as a mid-level full-stack engineer on 2–3 concurrent client projects.
You need to be independently productive — we are not a mentorship environment. You
will own features from spec to deployment with minimal supervision.

WHAT YOU WILL DO
- Build and ship features across Django/Python backends and React frontends
- Participate in client calls to clarify requirements
- Review junior developer code
- Manage your own time across concurrent projects

REQUIREMENTS
- 3+ years professional software development experience
- Django and React proficiency
- Experience working directly with clients or end users
- Comfortable managing your own work without daily oversight

COMPENSATION
KES 120,000–180,000/month depending on experience
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c09_incomplete_cv",
    role_seniority="mid",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "3+ years professional software development",
        "Django and React proficiency",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
