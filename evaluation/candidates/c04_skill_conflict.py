"""
WHY: c04 tests the unverifiable high-stakes claim detector. The candidate
claims expert-level proficiency in Kubernetes, Terraform, and ML pipelines —
skills that are gatekeeping requirements for the role. But a careful reading
of every job entry reveals pure CRUD web development: no infrastructure work,
no ML, no evidence of any of the claimed skills in practice.

HOW: The skills list is keyword-perfect for the role. The role descriptions
are generic web dev. This is the "skills section as lies" pattern that a naive
keyword-match ATS would rank highly and an experienced recruiter would
immediately flag. SCREEN should detect the gap and escalate.
"""

from screen.schemas.input import ScreeningInput

GROUND_TRUTH_VERDICT: str = "ESCALATE"
GROUND_TRUTH_RATIONALE: str = (
    "Candidate claims 'Expert: Kubernetes, Terraform, ML pipelines (Kubeflow, MLflow)' in skills "
    "section, but none of the 5 role descriptions contain any evidence of infrastructure work, "
    "orchestration, or machine learning. All roles are web application development (Django, "
    "React, MySQL). The skills-experience gap is the highest-stakes pattern SCREEN must catch: "
    "these are role-critical skills and the claim is entirely unverifiable from the CV content. "
    "Escalation category: unverifiable_high_stakes_claim."
)

CV_TEXT: str = """
FELIX OCHIENG
felix.ochieng@outlook.com | Nairobi, Kenya | github.com/felix-oc

SUMMARY
Full-stack developer with 5 years of experience building web applications and data platforms.
Expertise in cloud infrastructure, MLOps, and containerised deployments. Comfortable across
the full stack from database design to production Kubernetes clusters. Eager to work on
ML-driven products and data-intensive systems.

TECHNICAL SKILLS
Expert: Python, Kubernetes, Terraform, ML pipelines (Kubeflow, MLflow), Docker Swarm
Proficient: Django, React, PostgreSQL, MySQL, Redis, Celery
Familiar: AWS (EC2, S3), GCP, Airflow, Spark

EXPERIENCE

Full Stack Developer — Retail Orbit, Nairobi
Oct 2022 – Present (1 year 10 months)
- Built and maintained the product catalogue API using Django REST Framework
- Developed the React-based admin dashboard for warehouse staff
- Wrote SQL queries for inventory reporting (MySQL)
- Fixed frontend bugs reported by QA team
- Participated in weekly sprint ceremonies

Full Stack Developer — BizConnect Africa, Nairobi
Mar 2021 – Sep 2022 (1 year 7 months)
- Created a customer-facing web portal for SME loan applications (Django + React)
- Integrated M-Pesa payment flow via Daraja API
- Managed the MySQL database schema for loan application records
- Maintained the company's internal CRM application

Junior Developer — Soko Digital, Nairobi
Jul 2019 – Feb 2021 (1 year 8 months)
- Assisted senior developers in building e-commerce features
- Wrote HTML/CSS templates for the marketing website
- Implemented basic form validation in JavaScript
- Helped migrate data from spreadsheets to the MySQL database

Junior Web Developer (Internship) — CloudWeb Studios, Nairobi
Jan 2019 – Jun 2019 (6 months)
- Built WordPress themes for client websites
- Learned version control with Git

Freelance Developer
2018 (part-time)
- Built a basic Flask portfolio site for a local photographer

EDUCATION
BSc Information Technology — Strathmore University, Nairobi, 2018

CERTIFICATIONS
- HashiCorp Terraform Associate (claimed, no badge link provided)
- Google Professional Data Engineer (claimed, no badge link provided)
"""

JOB_DESCRIPTION: str = """
ML Platform Engineer — MLOps Infrastructure
Xona AI, Remote (Africa-based candidates strongly encouraged)

Xona AI builds computer vision products for retail and logistics. Our ML platform team
owns the infrastructure that data scientists and ML engineers deploy models on. We run
50+ models in production across 3 cloud providers.

THE ROLE
You will build and maintain the ML infrastructure layer: training orchestration, model
serving, experiment tracking, and the internal developer platform that ML engineers
use every day. This is an infrastructure-first role — you must be comfortable at the
intersection of DevOps and ML.

WHAT YOU WILL DO
- Own and evolve our Kubernetes-based model training and serving infrastructure
- Build and maintain Kubeflow pipelines for training orchestration across GPU clusters
- Manage Terraform modules for our multi-cloud footprint (AWS + GCP)
- Integrate MLflow for experiment tracking and model registry
- Build internal tooling to improve data scientist and MLE productivity

REQUIREMENTS (hard)
- Production Kubernetes experience (cluster management, not just kubectl apply)
- Terraform at IaC production level (modules, state management, multi-environment)
- Hands-on experience with an ML pipeline orchestrator (Kubeflow, Airflow, or Metaflow)
- 3+ years infrastructure or MLOps engineering experience

NICE TO HAVE
- Python automation scripting
- Experience with GPU scheduling (NVIDIA device plugin, etc.)

COMPENSATION
$60,000–$85,000 USD equivalent (remote, Africa-based)
"""

CANDIDATE_INPUT = ScreeningInput(
    candidate_id="c04_skill_conflict",
    role_seniority="mid",
    role_type="engineering",
    batch_id="eval_batch_001",
    hard_requirements=[
        "production Kubernetes experience",
        "Terraform at IaC production level",
        "ML pipeline orchestrator experience",
        "3+ years infrastructure or MLOps engineering",
    ],
    cv_text=CV_TEXT,
    job_description=JOB_DESCRIPTION,
)
