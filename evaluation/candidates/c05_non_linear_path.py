"""
WHY: c05 tests the non-linear path detector — one of SCREEN's most important
differentiating features. An ATS parsing this CV would see "Primary School Teacher"
and immediately disqualify. A thoughtful recruiter reads the full arc: deliberate
career pivot, completed bootcamp, shipped 3 real products, and is applying to a role
in ed-tech where the teaching background is actually a domain advantage.

HOW: Career path is teacher → bootcamp → junior dev → mid SWE at health tech startup.
The non-linear path is coherent and the learning velocity is exceptional — this is
exactly the profile that SCREEN should surface as a YES while an ATS kills it.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "YES"
GROUND_TRUTH_RATIONALE: str = (
    "Non-linear path that an ATS would kill but a thoughtful recruiter would advance. "
    "Teaching background is a domain advantage for an ed-tech SWE role. Learning velocity "
    "is exceptional: moved from bootcamp to mid-level SWE in under 3 years, shipped 3 "
    "portfolio products with real users, and the health tech startup role shows she can "
    "deliver in a regulated, user-facing product environment. Technical skills are appropriate "
    "for a mid-level SWE role. Domain knowledge (pedagogy, curriculum design) is rare in "
    "engineering teams building learning products and represents a genuine non-obvious fit signal. "
    "Confidence: 72%."
)

CV_TEXT: str = """
GRACE MUTHONI KARIUKI
Nairobi, Kenya | grace.muthoni.dev@gmail.com | github.com/grace-mdev | linkedin.com/in/grace-muthoni-k

SUMMARY
Software engineer and former primary school teacher with 3 years in professional software
development. Transitioned into tech through Moringa School (Nairobi) after 4 years in
the classroom. My teaching background gives me an unusual ability to design for learners:
I think about how people build mental models, not just how software works. Currently
building patient-facing features at a health tech startup. 3 shipped portfolio products
with real users.

EXPERIENCE

Software Engineer (Mid-Level) — AfyaDigital, Nairobi
Mar 2023 – Present (1 year 5 months)
- Own the patient appointment booking flow (React Native + Node.js backend); used by
  12,000 monthly active patients across 3 counties
- Reduced appointment no-show rate from 34% to 21% by building an SMS reminder feature
  integrated with Africa's Talking API
- Built an admin dashboard for clinic coordinators (React + Recharts); cut weekly reporting
  time from 4 hours to 20 minutes for clinic staff
- Participates in bi-weekly design reviews; proposed and shipped the "plain language"
  consent flow which reduced patient abandonment at the consent step by 28%

Junior Software Developer — Kazi Tech, Nairobi
Sep 2021 – Feb 2023 (1 year 6 months)
- Built 3 features for a job-matching web app (Django + React): skill tagging, employer
  shortlisting, and applicant status notifications
- Maintained the PostgreSQL schema and wrote migrations for 4 schema iterations
- Wrote unit tests for core API endpoints using pytest; raised test coverage from 41% to 68%
- First employee to introduce PR templates and a code review checklist

Primary School Teacher — St. Francis of Assisi Primary School, Nyeri
2017 – 2021 (4 years)
- Taught Science and Mathematics to Grades 4–7 (ages 10–13)
- Developed differentiated learning materials for a mixed-ability class of 38 students
- Piloted a peer-teaching programme that improved end-of-year Science scores by 18%
  across the class cohort
- Served as school ICT coordinator in final year; trained 12 teachers on digital lesson tools

EDUCATION
Full-Stack Software Development Bootcamp — Moringa School, Nairobi, 2021
Languages and frameworks covered: JavaScript, React, Python, Django, SQL, Git

Bachelor of Education (Science) — Kenyatta University, Nairobi, 2016
Major: Biology and Chemistry

PORTFOLIO PROJECTS
- MathBridge (mathbridge.co.ke — live): Adaptive maths practice tool for primary school
  learners; 340 registered students, built with React + Django
- AfyaReminder (github.com/grace-mdev/afya-reminder): Open-source SMS appointment reminder
  library for Africa's Talking; 60 GitHub stars
- Shule Planner: Lesson planning web app for Kenyan primary teachers (150 active users)

SKILLS
JavaScript, React, React Native, Node.js, Python, Django, PostgreSQL, MySQL, Git,
Africa's Talking API, REST APIs, pytest, basic AWS (S3, EC2), Figma (basic)
"""

JOB_DESCRIPTION: str = """
Software Engineer (Mid-Level) — Learning Experience
Elimu.io (Seed, $2.4M raised), Nairobi (Hybrid)

Elimu.io builds adaptive learning software for primary and secondary schools across
East Africa. Our platform is used by 85,000 learners in Kenya, Uganda, and Rwanda.
We are a 9-person team (5 engineers) closing our Seed round and preparing to scale.

THE ROLE
You will build the learner-facing features that students interact with daily. This means
React Native mobile screens, backend APIs in Node.js, and the occasional data pipeline
that feeds our adaptive recommendation engine. You will have a direct line to teachers
and school coordinators as user research partners.

WHAT YOU WILL DO
- Build and own learner-facing features end-to-end (mobile + API)
- Collaborate with our curriculum team to translate pedagogical requirements into
  engineering specifications
- Participate in bi-weekly user research sessions with teachers and school admins
- Review and improve code quality for 1 junior engineer

REQUIREMENTS
- 2+ years professional software development experience
- React or React Native proficiency
- Experience with a backend framework (Node.js, Django, or similar)
- Comfortable working in a small team with high ownership expectations

NICE TO HAVE
- Background in education, teaching, or edtech domain
- Experience building for low-bandwidth mobile environments (Africa context)
- Portfolio projects with real users

COMPENSATION
KES 180,000–240,000/month + equity options
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c05_non_linear_path",
    role_seniority="mid",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "2+ years professional software development",
        "React or React Native proficiency",
        "backend framework experience",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
