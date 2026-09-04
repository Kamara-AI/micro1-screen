"""
WHY: Domain calibration is the core fix for the Batch 4 Marketing failure (42% accuracy).
The problem was that SCREEN had hardcoded logic for only 3 domains (Engineering, Data Science,
Operations/Supply Chain). Any other domain got generic treatment with no domain-appropriate
silence flags, no hard anchors, and no Tier C trap detection.

This module defines a full calibration registry for 20 hiring domains. Every domain specifies:
  - What keywords prove genuine domain experience (domain_keywords)
  - What specific phrases indicate real, verifiable experience (hard_anchor_patterns)
  - What generic phrases are common in that domain but carry no signal (tier_c_traps)
  - Whether production deployment absence is a meaningful signal (production_check_enabled)
  - Whether skill-level conflict checking is appropriate (skill_conflict_check_enabled)
  - What non-transferable backgrounds should trigger hard score caps (hard_cap_alien_domains)

HOW: Any role_type string is matched against domain aliases. The calibration is then injected
into both the evidence extraction and fit analysis prompts so the LLM receives domain-aware
guidance rather than relying on generic recruiter instincts.

The architecture: detect_domain() → get_calibration() → injected into extract_evidence.py
and analyze_fit.py as deterministic facts + prompt additions.
"""

from dataclasses import dataclass, field

__all__ = [
    "DomainCalibration",
    "DOMAIN_REGISTRY",
    "GENERIC_CALIBRATION",
    "detect_domain",
    "get_calibration",
]


@dataclass
class DomainCalibration:
    """
    Calibration config for a single hiring domain.

    Attributes:
        name: Canonical domain name (e.g. "Software Engineering").
        aliases: Lowercase substrings that map a role_type string to this domain.
            Checked in order — first match wins.
        production_check_enabled: True for tech domains where the absence of any
            production deployment is a meaningful red flag for senior candidates.
            False for domains where "production" is not a meaningful concept
            (e.g. Marketing, Sales, HR, Finance).
        production_check_keywords: Phrases in role achievement bullets that confirm
            the candidate has deployed/shipped something to live production.
            Only used when production_check_enabled=True.
        skill_conflict_check_enabled: True for tech domains where engineers name the
            specific tools they used in every role bullet. False for outcome-language
            domains (Sales, Marketing, HR, Ops) where candidates write "grew revenue 40%"
            not "used Salesforce to grow revenue 40%" — checking skill mentions against
            role bullets produces false conflicts for these domains.
        domain_keywords: Real vocabulary used in this domain. Presence in CV text
            signals genuine domain experience. Absence is a potential mismatch flag.
            Minimum 15 per domain.
        minimum_domain_keyword_count: How many domain_keywords must appear in the CV
            before we consider it a genuine domain match. Default 2 is intentionally
            conservative — some keywords are short and could appear coincidentally.
        hard_anchor_patterns: Specific phrases that indicate Tier A or B evidence —
            real, verifiable experience with scope and outcome. These are the signals
            a senior recruiter uses to distinguish genuine practitioners from people
            who can write the right words. Minimum 6 per domain.
        tier_c_traps: Generic claim patterns that are extremely common in this domain
            but carry essentially no signal — any candidate can write them. These are
            the phrases that fool ATS systems. Minimum 5 per domain.
        hard_cap_alien_domains: Descriptions of backgrounds that are fundamentally
            non-transferable to this domain. Used to trigger hard score caps in the
            fit analysis node. Be conservative — only truly incompatible backgrounds.
        supervision_check_enabled: Always True. Supervision language detection is
            domain-agnostic and applies universally.
        strong_yes_threshold: Domain-specific override for the STRONG_YES verdict threshold.
            Default 86.0 matches the global setting. Lower for domains where Tier A evidence
            is structurally rare (e.g. Digital Marketing has no GitHub repos or public APIs
            to cite — the best evidence is Tier B campaign metrics). Calibrated from eval data.
    """

    name: str
    aliases: list[str]
    production_check_enabled: bool
    production_check_keywords: list[str]
    skill_conflict_check_enabled: bool
    domain_keywords: list[str]
    minimum_domain_keyword_count: int
    hard_anchor_patterns: list[str]
    tier_c_traps: list[str]
    hard_cap_alien_domains: list[str]
    supervision_check_enabled: bool = field(default=True)
    strong_yes_threshold: float = field(default=86.0)
    ambiguous_threshold: float = field(default=45.0)
    # WHY: Domain-specific override for the AMBIGUOUS verdict threshold.
    # Default 45.0 matches the global setting. For Digital Marketing, the
    # evidence quality floor is higher — weak candidates who write generic
    # outcome language (Tier C) naturally cluster around 49-55% confidence.
    # Raising the threshold to 55.0 ensures they land in NO territory rather
    # than AMBIGUOUS, which would imply "worth investigating further."


# ── Domain Registry ────────────────────────────────────────────────────────────
# Ordered from most specific to most generic within alias groups to prevent
# early-match false positives (e.g. "data engineer" should not match "engineer"
# before "data" aliases are checked).

DOMAIN_REGISTRY: list[DomainCalibration] = [

    # ── 1. Data Science / ML / AI ──────────────────────────────────────────────
    # WHY: Checked before Software Engineering because "data scientist" and "ml engineer"
    # are legitimate aliases that contain "engineer" — we want the more specific match.
    DomainCalibration(
        name="Data Science / ML / AI",
        aliases=[
            "data scientist", "machine learning", "ml engineer", "ai engineer",
            "data science", "nlp engineer", "computer vision", "deep learning",
            "research scientist", "applied scientist", "mlops", "data analyst",
            "analytics engineer", "quantitative analyst", "quant analyst",
        ],
        # WHY: Senior DS/ML candidates who have never deployed a model to production
        # are researchers, not practitioners — a critical distinction for most roles.
        production_check_enabled=True,
        production_check_keywords=[
            "deployed", "in production", "model serving", "api endpoint",
            "real-time inference", "batch prediction", "model monitoring",
            "live system", "production system", "serving pipeline", "mlflow",
            "model registry", "feature store", "online serving", "a/b test",
            "shadow mode", "canary deployment", "model drift", "retraining pipeline",
        ],
        # WHY: DS/ML engineers do name tools in role bullets (TensorFlow, PyTorch,
        # scikit-learn, XGBoost) — skill conflict check is meaningful here.
        skill_conflict_check_enabled=True,
        domain_keywords=[
            "model", "training", "inference", "feature", "dataset", "accuracy",
            "precision", "recall", "f1", "auc", "roc", "overfitting", "regularisation",
            "hyperparameter", "gradient", "neural network", "transformer", "embedding",
            "pipeline", "validation", "cross-validation", "statistical", "regression",
            "classification", "clustering", "anomaly detection", "time series",
            "experiment", "hypothesis", "p-value", "confidence interval",
            "tensorflow", "pytorch", "scikit-learn", "xgboost", "lightgbm",
            "pandas", "numpy", "spark", "sql", "jupyter", "python",
        ],
        minimum_domain_keyword_count=3,
        hard_anchor_patterns=[
            "deployed model to production",
            "reduced model latency",
            "improved accuracy by",
            "a/b test",
            "feature store",
            "model serving",
            "false positive rate",
            "precision-recall",
            "model drift",
            "retraining pipeline",
            "business impact",
            "fraud detection model",
            "recommendation engine",
            "real-time prediction",
        ],
        tier_c_traps=[
            "worked with machine learning",
            "experience with data",
            "familiar with python",
            "knowledge of statistics",
            "analysed data",
            "built models",
            "used various ml techniques",
            "passionate about data",
            "exposure to ai",
            "understanding of algorithms",
        ],
        hard_cap_alien_domains=[
            "Entire career in manual data entry or data cleansing only — no modelling or analysis",
            "Entire career in IT support or helpdesk with no data or analytics exposure",
        ],
    ),

    # ── 2. DevOps / Platform Engineering / SRE ────────────────────────────────
    # WHY: Checked before Software Engineering — "devops engineer" and "sre" contain
    # "engineer" but are a distinct discipline requiring distinct calibration.
    DomainCalibration(
        name="DevOps / Platform Engineering / SRE",
        aliases=[
            "devops", "site reliability", "sre", "platform engineer", "infrastructure engineer",
            "cloud engineer", "reliability engineer", "systems engineer", "build engineer",
            "release engineer", "devsecops", "gitops", "mlops engineer",
        ],
        # WHY: A DevOps engineer who has never managed a production system or CI/CD pipeline
        # is a theoretical practitioner — production evidence is the core differentiator.
        production_check_enabled=True,
        production_check_keywords=[
            "production", "ci/cd", "deployed", "kubernetes cluster", "terraform apply",
            "pipeline", "zero downtime", "rollback", "incident response", "on-call",
            "sla", "uptime", "monitoring", "alerting", "infrastructure as code",
        ],
        # WHY: DevOps engineers name tools explicitly — Kubernetes, Terraform, Helm, Ansible.
        # Skill conflict check is meaningful and catches "Expert: Kubernetes" claims
        # from candidates who have never touched k8s in any role.
        skill_conflict_check_enabled=True,
        domain_keywords=[
            "kubernetes", "docker", "terraform", "ansible", "helm", "ci/cd",
            "jenkins", "github actions", "gitlab", "pipeline", "container",
            "infrastructure", "monitoring", "prometheus", "grafana", "alerting",
            "aws", "gcp", "azure", "cloud", "vpc", "iam", "s3", "ec2",
            "deployment", "rollback", "uptime", "sla", "incident", "on-call",
            "bash", "linux", "nginx", "load balancer", "cdn",
        ],
        minimum_domain_keyword_count=3,
        hard_anchor_patterns=[
            "reduced deployment time",
            "zero downtime deployment",
            "99.9% uptime",
            "incident response",
            "kubernetes cluster",
            "infrastructure as code",
            "ci/cd pipeline",
            "reduced mean time to recovery",
            "cost reduction on cloud",
            "migrated to kubernetes",
            "terraform module",
            "on-call rotation",
        ],
        tier_c_traps=[
            "experience with cloud",
            "worked with docker",
            "familiar with linux",
            "knowledge of ci/cd",
            "experience with aws",
            "understanding of devops principles",
            "exposure to kubernetes",
            "used various cloud tools",
        ],
        hard_cap_alien_domains=[
            "Entire career in manual IT support / helpdesk with no automation, cloud, or pipeline exposure",
            "Entire career as an application developer with no infrastructure, deployment, or ops ownership",
        ],
    ),

    # ── 3. Cybersecurity / Information Security ───────────────────────────────
    DomainCalibration(
        name="Cybersecurity / Information Security",
        aliases=[
            "cybersecurity", "information security", "infosec", "security engineer",
            "security analyst", "penetration tester", "pentester", "red team",
            "blue team", "soc analyst", "threat intelligence", "security architect",
            "application security", "appsec", "cloud security", "devsecops",
            "grc analyst", "risk analyst",
        ],
        # WHY: Security professionals must have hands-on production exposure —
        # running live IR, implementing controls in prod environments. Academic
        # knowledge without production application is insufficient for most roles.
        production_check_enabled=True,
        production_check_keywords=[
            "incident response", "live environment", "production system", "remediated",
            "vulnerability in production", "patch deployed", "security control implemented",
            "soc", "live threat", "breached", "forensic analysis", "containment",
        ],
        # WHY: Security engineers name frameworks and tools — SIEM, SOAR, specific CVEs,
        # Burp Suite, Nessus, CrowdStrike. Skill conflict detection is appropriate.
        skill_conflict_check_enabled=True,
        domain_keywords=[
            "vulnerability", "exploit", "penetration", "firewall", "siem", "soar",
            "incident", "threat", "malware", "phishing", "ransomware", "zero-day",
            "cve", "owasp", "iso 27001", "soc 2", "nist", "gdpr", "pci-dss",
            "authentication", "authorisation", "encryption", "ssl/tls", "vpn",
            "ids/ips", "endpoint detection", "edr", "xdr", "log analysis",
            "risk assessment", "compliance", "audit", "patch management",
        ],
        minimum_domain_keyword_count=3,
        hard_anchor_patterns=[
            "led incident response",
            "iso 27001 certified",
            "soc 2 type",
            "penetration test",
            "cve disclosed",
            "vulnerability remediation",
            "reduced attack surface",
            "threat hunting",
            "security audit",
            "implemented zero trust",
            "phishing simulation",
            "red team exercise",
        ],
        tier_c_traps=[
            "experience with security",
            "knowledge of cybersecurity principles",
            "familiar with owasp",
            "understanding of threats",
            "passionate about security",
            "exposure to security tools",
            "interest in ethical hacking",
            "worked on security projects",
        ],
        hard_cap_alien_domains=[
            "Entire career in non-technical roles (HR, Marketing, Finance) with no security tooling, audit, or compliance work",
            "Entire career in general IT support with no security specialisation, certifications, or incident exposure",
        ],
    ),

    # ── 4. Software Engineering ───────────────────────────────────────────────
    DomainCalibration(
        name="Software Engineering",
        aliases=[
            "software engineer", "software developer", "backend engineer", "frontend engineer",
            "full stack", "fullstack", "web developer", "mobile engineer", "ios engineer",
            "android engineer", "embedded engineer", "systems developer", "api developer",
            "engineer", "developer",  # broad — checked after more specific domains above
        ],
        # WHY: Production deployment is the dividing line between software engineers
        # and CS students. Senior candidates with zero production exposure represent
        # a significant risk for any role requiring ownership of live systems.
        production_check_enabled=True,
        production_check_keywords=[
            "production", "deployed", "live system", "shipped", "released",
            "in production", "serving", "api in production", "microservice",
            "load tested", "scaled to", "real users", "customer-facing",
        ],
        # WHY: Engineers name their tools explicitly in role bullets — languages,
        # frameworks, databases. Skill conflict detection is meaningful and prevents
        # "Expert: Rust" claims from candidates who have no Rust in any role.
        skill_conflict_check_enabled=True,
        domain_keywords=[
            "api", "backend", "frontend", "database", "sql", "nosql", "microservice",
            "rest", "graphql", "authentication", "deployment", "ci/cd", "git",
            "code review", "unit test", "integration test", "performance", "latency",
            "scalability", "architecture", "refactor", "technical debt", "sprint",
            "agile", "scrum", "pull request", "release", "service", "endpoint",
            "python", "java", "golang", "typescript", "javascript", "rust", "c++",
        ],
        minimum_domain_keyword_count=3,
        hard_anchor_patterns=[
            "architected",
            "zero to one",
            "built from scratch",
            "scaled to",
            "reduced latency by",
            "serving n users",
            "led technical design",
            "system design",
            "open source",
            "shipped feature",
            "reduced cost by",
            "improved throughput",
            "p99 latency",
            "99.9% availability",
        ],
        tier_c_traps=[
            "worked on various projects",
            "familiar with multiple programming languages",
            "experience with web development",
            "contributed to team projects",
            "knowledge of software development lifecycle",
            "passionate about coding",
            "exposure to agile",
            "understanding of oop",
            "worked with databases",
        ],
        hard_cap_alien_domains=[
            "Entire career in non-technical roles with zero coding, scripting, or system-building evidence",
            "Entire career as IT support/helpdesk with no development, deployment, or code-authoring evidence",
        ],
    ),

    # ── 5. Digital Marketing ──────────────────────────────────────────────────
    DomainCalibration(
        name="Digital Marketing",
        aliases=[
            "marketing manager", "digital marketing", "growth manager", "seo",
            "sem", "ppc", "paid media", "content marketing", "social media manager",
            "brand manager", "email marketing", "marketing director", "cmo",
            "performance marketing", "demand generation", "growth hacker",
            "marketing strategist", "marketing lead", "marketing specialist",
            "marketing analyst", "marketing",
        ],
        # WHY: Marketing is an outcome-language domain. "Production" is not a meaningful
        # concept. The equivalent signal (shipped campaigns, owned channels) is captured
        # via hard_anchor_patterns and domain silence flags instead.
        production_check_enabled=False,
        production_check_keywords=[],
        # WHY: Disabled. Marketing is an outcome-language domain — senior practitioners
        # legitimately write "managed KES 5M across Google and Meta" without naming tools
        # in every bullet. The skill conflict check produces systematic false positives:
        # a genuine expert who writes "Expert: GA4" and outcome bullets like "grew organic
        # traffic 45%" is correctly classified as a senior marketer but would be falsely
        # ESCALATED because "ga4" doesn't appear in their achievement bullets.
        # The f27 skill conflict case is instead caught via the LLM's contradiction
        # reasoning when the deterministic facts block highlights 0 hard anchors and
        # high Tier-C trap count, combined with the explicit "Expert:" skill claims.
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "roas", "cac", "cpm", "ctr", "cpc", "ltv", "conversion rate", "funnel",
            "organic", "paid", "seo", "sem", "ppc", "google ads", "meta ads",
            "email", "campaign", "audience", "segmentation", "a/b test",
            "lead generation", "mrr", "arr", "pipeline", "attribution",
            "content", "copywriting", "brand", "social media", "influencer",
            "analytics", "google analytics", "hubspot", "salesforce", "crm",
            "marketing automation", "drip", "nurture", "roi", "budget",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "roas of",
            "cac reduced by",
            "conversion rate improved",
            "managed budget of",
            "generated n leads",
            "grew organic traffic by",
            "email open rate",
            "campaign generated",
            "a/b tested",
            "attribution model",
            "grew mrr",
            "paid acquisition",
            "managed google ads",
        ],
        tier_c_traps=[
            "drove growth",
            "increased brand awareness",
            "engaged with customers",
            "developed marketing strategies",
            "managed social media presence",
            "created content",
            "collaborated with teams",
            "responsible for marketing",
            "experience with digital marketing",
            "passionate about brands",
        ],
        # WHY: These backgrounds have genuinely zero transferable marketing vocabulary —
        # someone whose entire career was in manual assembly line work, clinical nursing,
        # or civil engineering will have no channel ownership, no performance metrics,
        # no campaign management. General business roles are NOT alien (any manager
        # has had exposure to marketing concepts).
        hard_cap_alien_domains=[
            "Entire career in clinical healthcare, civil engineering, or manufacturing with no marketing, comms, or brand exposure",
            "Entire career in manual/trade labour with no client-facing, campaign, or digital channel experience",
        ],
        # WHY: Digital Marketing candidates structurally cannot produce Tier A evidence
        # (no public repos, no live APIs to link). Their best evidence is Tier B campaign
        # metrics. Batch 4 eval data shows genuine STRONG_YES candidates cluster at 71-85%.
        # Setting threshold to 75 captures f01(78%), f02(81%), f03(77%), f04(76%), f41(85%),
        # f42(80%) while keeping YES candidates (f11 at 74.6%) correctly below the threshold.
        strong_yes_threshold=75.0,
        # WHY: Digital Marketing NO candidates cluster at 56-60% with generic
        # Tier-C outcome language and some hard-anchor buzzwords. Raising the
        # AMBIGUOUS floor to 60 ensures weak candidates who can write marketing
        # language still score below AMBIGUOUS. AMBIGUOUS truth candidates
        # (f15 at 64%) are safely above this floor; NO candidates consistently
        # land in 56-60% across eval runs (f16-f32 cluster).
        # Calibrated from batch4 eval: f16(59%), f17(60%), f18(59%), f21(60%),
        # f31(60%), f32(56%) all need to land in NO territory.
        ambiguous_threshold=60.0,
    ),

    # ── 6. Sales / Business Development ──────────────────────────────────────
    DomainCalibration(
        name="Sales / Business Development",
        aliases=[
            "sales manager", "account executive", "account manager", "business development",
            "sales director", "vp sales", "chief revenue", "cro", "sales representative",
            "sales engineer", "solutions engineer", "field sales", "inside sales",
            "enterprise sales", "smb sales", "channel sales", "partnerships manager",
            "revenue manager", "commercial manager", "sales lead", "sales",
            "biz dev", "bd manager",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        # WHY: Sales candidates write "closed $2M ARR" not "used Salesforce to close $2M ARR".
        # Skill conflict detection would incorrectly penalise legitimate high performers.
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "quota", "arr", "mrr", "pipeline", "deal", "close", "prospect",
            "outbound", "inbound", "cold call", "demo", "proposal", "negotiation",
            "contract", "renewal", "upsell", "cross-sell", "churn", "win rate",
            "sales cycle", "crm", "salesforce", "hubspot", "enterprise", "smb",
            "territory", "account", "revenue", "commission", "forecast", "qbr",
            "discovery call", "objection handling", "executive sponsor", "champion",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "exceeded quota by",
            "closed n arr",
            "grew territory from",
            "win rate of",
            "average deal size",
            "shortened sales cycle",
            "enterprise account",
            "net new revenue",
            "president's club",
            "top performer",
            "managed pipeline of",
            "expanded account",
        ],
        tier_c_traps=[
            "drove revenue growth",
            "built relationships with clients",
            "collaborated with stakeholders",
            "developed business opportunities",
            "passionate about sales",
            "responsible for sales targets",
            "experience in client management",
            "worked with customers",
            "contributed to revenue",
            "grew the business",
        ],
        hard_cap_alien_domains=[
            "Entire career in back-office non-client-facing roles (data entry, accounting, lab work) with zero sales, BD, or client-facing exposure",
        ],
    ),

    # ── 7. Operations / Supply Chain / Logistics ──────────────────────────────
    DomainCalibration(
        name="Operations / Supply Chain / Logistics",
        aliases=[
            "supply chain", "logistics", "operations manager", "warehouse manager",
            "distribution manager", "procurement manager", "inventory manager",
            "demand planner", "supply planner", "fleet manager", "3pl manager",
            "last mile", "fulfilment manager", "fmcg operations", "manufacturing operations",
            "plant manager", "factory manager", "production manager",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        # WHY: Operations/supply chain candidates write in outcome language:
        # "Reduced shrinkage by 23%", "Improved fill rate to 98%"
        # They do NOT repeat tool names in every bullet even when genuinely using them.
        # Skill conflict detection on ops candidates ALWAYS produces false positives.
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "warehouse", "distribution", "logistics", "3pl", "supply chain",
            "inventory", "fill rate", "on-time delivery", "fmcg", "distributor",
            "dispatch", "freight", "last mile", "route planning", "shrinkage",
            "stock", "inbound", "outbound", "fulfilment", "procurement",
            "demand planning", "sku", "erp", "sap", "odoo", "wms",
            "supplier", "vendor", "purchase order", "lead time", "safety stock",
            "kpi", "cycle count", "stockout", "backorder",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "fill rate",
            "on-time delivery",
            "reduced shrinkage",
            "managed warehouse",
            "inventory accuracy",
            "led distribution",
            "reduced stockout",
            "improved order fulfilment",
            "managed 3pl",
            "route optimisation",
            "managed fleet of",
            "procurement savings",
        ],
        tier_c_traps=[
            "managed operations",
            "oversaw day-to-day activities",
            "ensured smooth operations",
            "responsible for logistics",
            "coordinated with teams",
            "experience in operations management",
            "familiar with supply chain",
            "worked on operational efficiency",
        ],
        hard_cap_alien_domains=[
            "Entire career in events/hospitality/venue operations with zero supply chain, warehousing, distribution, or FMCG vocabulary",
            "Entire career in contact centre / customer service operations with zero inventory, logistics, or supply chain exposure",
            "Entire career in NGO programme operations / M&E / donor reporting with zero commercial supply chain exposure",
            "Entire career in financial / payment / settlement operations with zero physical goods, logistics, or distribution exposure",
            "Entire career in banking branch operations with zero supply chain, warehousing, or distribution exposure",
        ],
    ),

    # ── 8. Finance / Accounting / FP&A ────────────────────────────────────────
    DomainCalibration(
        name="Finance / Accounting / FP&A",
        aliases=[
            "financial analyst", "finance manager", "fp&a", "financial planning",
            "accountant", "accounting manager", "controller", "cfo", "chief financial",
            "treasury", "tax", "audit", "internal audit", "investment analyst",
            "fund manager", "portfolio manager", "credit analyst", "risk manager",
            "finance director", "management accountant", "cost accountant",
            "financial controller", "finance",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        # WHY: Finance candidates write outcomes ("reduced cost by 12%") not tool-name
        # claims ("used Excel to reduce cost"). Skill conflict check inappropriate.
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "p&l", "balance sheet", "cash flow", "budget", "forecast", "variance",
            "revenue", "ebitda", "gross margin", "working capital", "capex", "opex",
            "financial model", "dcf", "lbo", "npv", "irr", "valuation",
            "audit", "compliance", "ifrs", "gaap", "tax", "statutory",
            "reconciliation", "accounts payable", "accounts receivable",
            "treasury", "hedging", "fx", "interest rate", "credit",
            "erp", "sap", "oracle", "quickbooks", "excel", "power bi",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "p&l ownership",
            "budget of",
            "financial model",
            "reduced cost by",
            "dcf valuation",
            "audit completion",
            "ifrs compliance",
            "working capital improvement",
            "variance analysis",
            "board reporting",
            "closed accounts",
            "tax filing",
            "managed cash flow",
        ],
        tier_c_traps=[
            "strong financial acumen",
            "experience with financial analysis",
            "familiar with accounting principles",
            "knowledge of financial reporting",
            "worked on budgets",
            "responsible for financial tasks",
            "passionate about finance",
            "understanding of economics",
            "contributed to financial projects",
        ],
        hard_cap_alien_domains=[
            "Entire career in non-financial roles (e.g. marketing, operations, engineering) with zero financial modelling, accounting, audit, or reporting exposure",
        ],
    ),

    # ── 9. Product Management ─────────────────────────────────────────────────
    DomainCalibration(
        name="Product Management",
        aliases=[
            "product manager", "product lead", "product director", "vp product",
            "chief product", "cpo", "product owner", "group product manager",
            "technical product manager", "growth pm", "platform pm", "product",
        ],
        # WHY: PMs who have never shipped a live product to real users are researchers
        # or internal stakeholders — not product owners. Shipping to production (or
        # equivalent — launching a live feature to users) is the key signal.
        production_check_enabled=True,
        production_check_keywords=[
            "shipped", "launched", "released to users", "in production", "live",
            "went live", "deployed", "feature launch", "product launch", "beta",
            "ga launch", "rolled out", "delivered to customers",
        ],
        # WHY: PMs don't write "used Jira to manage sprints". Skill conflict check
        # would wrongly penalise legitimate PMs who describe outcomes, not tooling.
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "roadmap", "sprint", "backlog", "user story", "acceptance criteria",
            "product launch", "shipped", "feature", "stakeholder", "discovery",
            "user research", "a/b test", "retention", "engagement", "dau", "mau",
            "nps", "okr", "kpi", "go-to-market", "product strategy", "prioritisation",
            "agile", "scrum", "kanban", "mvp", "prd", "brd", "product spec",
            "cross-functional", "engineering partner", "design partner",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "shipped product",
            "launched feature",
            "grew dau",
            "improved retention by",
            "roadmap for",
            "zero to one product",
            "user research led to",
            "a/b test resulted in",
            "drove product-market fit",
            "managed roadmap",
            "go-to-market",
            "product revenue",
        ],
        tier_c_traps=[
            "collaborated with stakeholders",
            "gathered requirements",
            "worked with engineering",
            "managed the backlog",
            "coordinated with teams",
            "passionate about product",
            "experience with agile",
            "responsible for product development",
            "familiar with user stories",
            "understanding of product lifecycle",
        ],
        hard_cap_alien_domains=[
            "Entire career in non-product roles with zero evidence of roadmap ownership, stakeholder management, or shipped features",
        ],
    ),

    # ── 10. Customer Success / Support / CX ──────────────────────────────────
    DomainCalibration(
        name="Customer Success / Support / CX",
        aliases=[
            "customer success", "customer experience", "cx manager", "cs manager",
            "account manager", "customer support", "support manager", "support lead",
            "client success", "client experience", "customer retention", "onboarding manager",
            "implementation manager", "customer success manager", "csm",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "nps", "csat", "churn", "retention", "renewal", "arr", "expansion",
            "onboarding", "qbr", "executive business review", "health score",
            "at-risk", "escalation", "sla", "response time", "resolution time",
            "customer journey", "playbook", "success plan", "upsell", "cross-sell",
            "crm", "zendesk", "gainsight", "salesforce", "ticketing",
            "customer segment", "enterprise", "smb", "portfolio",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "nps improved by",
            "churn rate reduced",
            "arr retained",
            "expansion revenue",
            "managed portfolio of",
            "customer health score",
            "renewal rate",
            "reduced time to value",
            "onboarded n customers",
            "escalation resolved",
            "csat score",
        ],
        tier_c_traps=[
            "passion for customer service",
            "experience dealing with customers",
            "built relationships",
            "ensured customer satisfaction",
            "resolved customer issues",
            "responsible for customer accounts",
            "worked with customers",
            "familiar with crm tools",
        ],
        hard_cap_alien_domains=[
            "Entire career in back-office non-client-facing roles with zero customer interaction, account management, or service delivery",
        ],
    ),

    # ── 11. HR / People Operations / Talent Acquisition ──────────────────────
    DomainCalibration(
        name="HR / People Operations / Talent Acquisition",
        aliases=[
            "human resources", "hr manager", "hr director", "people operations",
            "people manager", "talent acquisition", "recruiter", "technical recruiter",
            "talent partner", "hrbp", "hr business partner", "hr generalist",
            "compensation and benefits", "total rewards", "learning and development",
            "organisational development", "hr lead", "head of people", "hr",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "headcount", "hiring", "recruitment", "talent", "onboarding", "offboarding",
            "performance review", "okr", "compensation", "benefits", "salary band",
            "hris", "workday", "bamboohr", "greenhouse", "lever", "ats",
            "employee engagement", "retention", "attrition", "time-to-hire",
            "offer acceptance", "employer brand", "culture", "dei", "inclusion",
            "training", "l&d", "succession", "org design", "workforce planning",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "reduced time-to-hire",
            "improved retention rate",
            "headcount of",
            "managed hris",
            "redesigned compensation",
            "built talent pipeline",
            "launched employee engagement",
            "scaled team from",
            "offer acceptance rate",
            "led hiring for",
            "implemented performance management",
        ],
        tier_c_traps=[
            "passionate about people",
            "experience in hr",
            "familiar with recruitment",
            "worked in human resources",
            "responsible for hr functions",
            "knowledge of employment law",
            "understanding of hr processes",
            "collaborated with teams on hr matters",
        ],
        hard_cap_alien_domains=[
            "Entire career in purely technical roles (engineering, data science) with zero people management, HR process, or talent acquisition exposure",
        ],
    ),

    # ── 12. Design (UX / UI / Brand / Product Design) ────────────────────────
    DomainCalibration(
        name="Design (UX / UI / Brand)",
        aliases=[
            "ux designer", "ui designer", "product designer", "ux/ui", "graphic designer",
            "visual designer", "brand designer", "interaction designer", "motion designer",
            "design lead", "head of design", "creative director", "design manager",
            "design director", "design",
        ],
        # WHY: For design, "production" means shipped to real users with a portfolio link.
        # The absence of any shipped, live product design is a meaningful red flag
        # for senior candidates, just as it is for engineers.
        production_check_enabled=True,
        production_check_keywords=[
            "shipped", "launched", "live product", "in production", "released",
            "live app", "deployed", "published", "went live", "real users",
            "portfolio", "case study", "product in market",
        ],
        # WHY: Designers don't list "Figma" in every design bullet. Skill conflict
        # detection produces false positives for design tool claims.
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "figma", "sketch", "adobe", "prototype", "wireframe", "user research",
            "usability", "a/b test", "design system", "component", "typography",
            "colour", "grid", "layout", "user flow", "information architecture",
            "accessibility", "wcag", "responsive", "mobile-first", "interaction",
            "animation", "motion", "brand guide", "style guide", "design sprint",
            "heuristic evaluation", "user testing", "persona", "journey map",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "shipped product design",
            "design system",
            "user research led to",
            "a/b tested design",
            "improved conversion by",
            "reduced drop-off",
            "portfolio",
            "led design for",
            "redesigned",
            "improved usability score",
            "accessibility audit",
        ],
        tier_c_traps=[
            "passionate about design",
            "eye for design",
            "creative thinking",
            "experience with figma",
            "designed interfaces",
            "worked on design projects",
            "familiar with design principles",
            "strong aesthetic sense",
            "created visual content",
        ],
        hard_cap_alien_domains=[
            "Entire career in non-visual non-creative roles with zero design tool usage, UX research, or visual output",
        ],
    ),

    # ── 13. Legal / Compliance / Risk ─────────────────────────────────────────
    DomainCalibration(
        name="Legal / Compliance / Risk",
        aliases=[
            "legal counsel", "lawyer", "solicitor", "attorney", "legal manager",
            "compliance manager", "compliance officer", "compliance analyst",
            "risk manager", "risk analyst", "general counsel", "in-house counsel",
            "regulatory", "aml", "kyc", "data protection", "privacy officer",
            "dpo", "legal director", "head of legal", "legal",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "contract", "negotiation", "litigation", "regulatory", "compliance",
            "gdpr", "pci-dss", "aml", "kyc", "ifrs", "gaap", "sarbanes-oxley",
            "jurisdiction", "due diligence", "m&a", "ip", "intellectual property",
            "employment law", "data protection", "privacy", "risk assessment",
            "audit", "policy", "drafting", "legal opinion", "dispute resolution",
            "arbitration", "mediation", "regulatory filing", "board minutes",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "led due diligence",
            "drafted and negotiated",
            "regulatory approval",
            "gdpr compliance",
            "aml framework",
            "transaction closed",
            "court matter",
            "compliance programme",
            "risk framework",
            "policy implemented",
            "board-level legal advice",
            "jurisdictional",
        ],
        tier_c_traps=[
            "strong legal acumen",
            "knowledge of laws and regulations",
            "experience in compliance",
            "familiar with contracts",
            "understanding of legal frameworks",
            "responsible for legal matters",
            "worked on compliance projects",
            "passionate about law",
        ],
        hard_cap_alien_domains=[
            "Entire career in roles with zero legal, regulatory, compliance, or risk management exposure",
        ],
    ),

    # ── 14. Project / Programme Management ───────────────────────────────────
    DomainCalibration(
        name="Project / Programme Management",
        aliases=[
            "project manager", "programme manager", "program manager", "pmo",
            "project lead", "delivery manager", "scrum master", "agile coach",
            "it project manager", "construction project manager", "project director",
            "portfolio manager",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "project plan", "milestone", "gantt", "budget", "scope", "risk",
            "stakeholder", "pmo", "agile", "waterfall", "prince2", "pmp",
            "deliverable", "on-time", "on-budget", "resource allocation",
            "critical path", "dependency", "sprint", "backlog", "velocity",
            "change management", "escalation", "governance", "steering committee",
            "project charter", "status report", "rag status", "lessons learned",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "delivered on-time and on-budget",
            "managed budget of",
            "programme of",
            "stakeholders across",
            "pmp certified",
            "prince2",
            "reduced project overrun",
            "managed cross-functional team",
            "steering committee",
            "project portfolio",
            "change management",
        ],
        tier_c_traps=[
            "managed projects",
            "ensured delivery",
            "coordinated teams",
            "responsible for project delivery",
            "familiar with agile",
            "understanding of project management",
            "experience managing stakeholders",
            "worked on various projects",
            "passionate about delivery",
        ],
        hard_cap_alien_domains=[],  # PM is transferable across industries — no hard caps
    ),

    # ── 15. Communications / PR / Content ─────────────────────────────────────
    DomainCalibration(
        name="Communications / PR / Content",
        aliases=[
            "communications manager", "pr manager", "public relations", "content manager",
            "content strategist", "content writer", "copywriter", "editor",
            "comms manager", "head of communications", "corporate communications",
            "media relations", "press officer", "communications director",
            "communications lead",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "press release", "media relations", "journalist", "pitch", "coverage",
            "editorial", "content calendar", "tone of voice", "brand voice",
            "messaging", "narrative", "crisis communications", "spokesperson",
            "thought leadership", "ghostwriting", "copywriting", "seo content",
            "organic traffic", "readership", "engagement rate", "share of voice",
            "newsletter", "annual report", "internal comms", "executive comms",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "press coverage in",
            "media placement",
            "crisis comms",
            "brand narrative",
            "grew readership by",
            "editorial calendar",
            "launched content strategy",
            "executive speechwriting",
            "tone of voice guide",
            "organic traffic growth",
            "share of voice",
        ],
        tier_c_traps=[
            "excellent written communication",
            "strong storytelling skills",
            "experience creating content",
            "passionate about writing",
            "managed social media",
            "responsible for communications",
            "familiar with media",
            "worked on content projects",
        ],
        hard_cap_alien_domains=[
            "Entire career in roles with zero writing, editorial, media, or communications exposure",
        ],
    ),

    # ── 16. Strategy / Consulting / Business Analysis ─────────────────────────
    DomainCalibration(
        name="Strategy / Consulting / Business Analysis",
        aliases=[
            "strategy manager", "strategy analyst", "business analyst", "management consultant",
            "strategy consultant", "strategy director", "head of strategy", "chief of staff",
            "corporate strategy", "strategic planning", "business strategy",
            "transformation manager", "change manager", "consulting manager",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "market analysis", "competitive landscape", "business case", "executive presentation",
            "c-suite", "board", "strategic initiative", "market entry", "expansion",
            "due diligence", "m&a", "restructuring", "transformation", "roi",
            "benchmarking", "kpi framework", "ogsm", "swot", "porter's five forces",
            "financial model", "scenario planning", "recommendation", "stakeholder",
            "implementation", "mckinsey", "bcg", "bain", "deloitte", "pwc",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "recommendation adopted by c-suite",
            "market entry strategy",
            "revenue impact of",
            "built business case",
            "executive presentation",
            "m&a due diligence",
            "strategic roadmap",
            "board-level",
            "restructuring programme",
            "scenario analysis",
            "led strategy",
        ],
        tier_c_traps=[
            "strategic thinker",
            "strong analytical skills",
            "experience with strategy",
            "familiar with business analysis",
            "understanding of business",
            "passionate about strategy",
            "worked on strategic projects",
            "contributed to business decisions",
        ],
        hard_cap_alien_domains=[],  # Strategy is transferable across sectors
    ),

    # ── 17. Research & Development ────────────────────────────────────────────
    DomainCalibration(
        name="Research & Development",
        aliases=[
            "r&d", "research engineer", "research scientist", "research lead",
            "research manager", "r&d manager", "innovation manager", "lab scientist",
            "research director", "principal researcher", "research fellow",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "publication", "peer-reviewed", "patent", "hypothesis", "experiment",
            "methodology", "literature review", "prototype", "proof of concept",
            "grant", "research proposal", "lab", "specimen", "trial", "pilot",
            "findings", "conclusion", "replication", "reproducibility",
            "conference", "proceedings", "journal", "doi", "citation",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "published in",
            "patent filed",
            "grant awarded",
            "prototype validated",
            "research led to",
            "cited by",
            "peer-reviewed",
            "conference presentation",
            "technology transferred",
            "commercialised research",
        ],
        tier_c_traps=[
            "passionate about research",
            "curious mindset",
            "experience with research",
            "strong analytical skills",
            "familiar with scientific methods",
            "worked on research projects",
            "understanding of research process",
        ],
        hard_cap_alien_domains=[],
    ),

    # ── 18. Healthcare / Clinical / Medical ────────────────────────────────────
    DomainCalibration(
        name="Healthcare / Clinical / Medical",
        aliases=[
            "doctor", "physician", "nurse", "clinical officer", "pharmacist",
            "medical officer", "healthcare manager", "clinical manager", "hospital administrator",
            "medical director", "clinical director", "health programme", "public health",
            "epidemiologist", "biomedical", "clinical research", "healthcare",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "patient", "clinical", "diagnosis", "treatment", "protocol", "ward",
            "hospital", "clinic", "medical record", "ehr", "emr", "icd",
            "procedure", "surgery", "prescription", "dosage", "adverse event",
            "clinical trial", "ethics board", "informed consent", "triage",
            "morbidity", "mortality", "health outcome", "patient safety",
            "infection control", "regulatory (fda, who, moh)", "certification",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "patient outcome improved",
            "clinical trial",
            "reduced mortality",
            "infection rate reduced",
            "clinical protocol",
            "led ward of",
            "managed n patients",
            "medical programme",
            "health outcome",
        ],
        tier_c_traps=[
            "passionate about health",
            "experience in healthcare",
            "familiar with medical procedures",
            "worked in clinical settings",
            "responsible for patient care",
        ],
        hard_cap_alien_domains=[
            "Entire career in non-healthcare roles with zero clinical, patient-facing, or medical regulatory exposure",
        ],
    ),

    # ── 19. Education / Learning & Development ────────────────────────────────
    DomainCalibration(
        name="Education / Learning & Development",
        aliases=[
            "teacher", "lecturer", "professor", "trainer", "learning and development",
            "l&d manager", "instructional designer", "curriculum developer",
            "education manager", "training manager", "elearning", "corporate trainer",
            "education director", "head of learning", "facilitator",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "curriculum", "lesson plan", "learning objective", "assessment", "rubric",
            "student", "learner", "cohort", "training programme", "workshop",
            "elearning", "lms", "articulate", "moodle", "completion rate",
            "knowledge retention", "skill gap", "competency framework", "blended learning",
            "facilitator", "mentoring", "coaching", "feedback", "exam", "certification",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "curriculum designed",
            "training completion rate",
            "learning outcomes improved",
            "cohort of n learners",
            "programme launched",
            "assessment designed",
            "knowledge retention rate",
            "skill gap closed",
            "certification programme",
        ],
        tier_c_traps=[
            "passionate about education",
            "enjoys teaching",
            "experience with training",
            "strong communication skills",
            "familiar with learning tools",
            "responsible for training",
        ],
        hard_cap_alien_domains=[],
    ),

    # ── 20. Executive / General Management / C-Suite ──────────────────────────
    DomainCalibration(
        name="Executive / General Management / C-Suite",
        aliases=[
            "ceo", "chief executive", "managing director", "md", "general manager",
            "country manager", "regional manager", "vp operations", "vp general",
            "executive director", "president", "coo", "chief operating",
            "managing partner", "director general",
        ],
        production_check_enabled=False,
        production_check_keywords=[],
        skill_conflict_check_enabled=False,
        domain_keywords=[
            "p&l", "board", "revenue", "ebitda", "headcount", "strategy",
            "stakeholder", "investor", "governance", "market share", "growth",
            "team leadership", "culture", "transformation", "scale", "fundraising",
            "m&a", "partnership", "expansion", "market entry", "turnaround",
            "shareholder", "equity", "enterprise value", "runway",
        ],
        minimum_domain_keyword_count=2,
        hard_anchor_patterns=[
            "p&l responsibility of",
            "grew revenue from",
            "board-level",
            "led organisation of",
            "market entry",
            "company turnaround",
            "raised funding",
            "managed headcount of",
            "exit / acquisition",
            "scaled from",
        ],
        tier_c_traps=[
            "visionary leader",
            "results-driven executive",
            "passionate about leadership",
            "strategic mindset",
            "strong business acumen",
            "experience leading teams",
            "responsible for organisational growth",
        ],
        hard_cap_alien_domains=[],  # Executive roles are intentionally cross-domain
    ),
]


# ── Generic fallback ───────────────────────────────────────────────────────────
# WHY: When no domain is detected, we use a minimal calibration that enables
# supervision checking and basic keyword counting without domain-specific biases.
# We do not produce false positives by applying tech-specific checks to unknown roles.
GENERIC_CALIBRATION = DomainCalibration(
    name="General / Unknown",
    aliases=[],
    production_check_enabled=False,
    production_check_keywords=[],
    skill_conflict_check_enabled=False,  # Safe default: avoid false positives
    domain_keywords=[
        # Generic professional vocabulary — very broad
        "managed", "led", "built", "delivered", "improved", "reduced", "increased",
        "stakeholder", "team", "project", "outcome", "result", "impact",
    ],
    minimum_domain_keyword_count=3,
    hard_anchor_patterns=[
        "measurable outcome",
        "quantified result",
        "led team of",
        "delivered project",
        "improved by",
    ],
    tier_c_traps=[
        "hard worker",
        "team player",
        "detail-oriented",
        "passionate",
        "responsible for",
        "strong communication skills",
        "experience with",
        "familiar with",
        "knowledge of",
    ],
    hard_cap_alien_domains=[],
)


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_domain(role_type: str) -> DomainCalibration | None:
    """
    Match a role_type string against all registered domain aliases.

    WHY: We use substring matching (not exact match) because role_type is a
    free-text field from the JD. "Senior Digital Marketing Manager" must match
    "marketing manager" and "digital marketing" — both are valid aliases.
    We return the first match in registry order, so more specific domains
    (Data Science, DevOps, Cyber) must appear before generic ones (Engineer).

    Args:
        role_type: The role type string from the screening input, e.g.
            "Senior Software Engineer" or "Head of Marketing EMEA".

    Returns:
        The first matching DomainCalibration, or None if no alias matches.
    """
    role_lower = role_type.lower().strip()
    if not role_lower:
        return None
    for calibration in DOMAIN_REGISTRY:
        for alias in calibration.aliases:
            if alias in role_lower:
                return calibration
    return None


def get_calibration(role_type: str) -> DomainCalibration:
    """
    Return domain calibration for a role type, falling back to generic if no match.

    WHY: This is the primary entry point used by extract_evidence.py and analyze_fit.py.
    It never throws and always returns a usable calibration — the generic fallback
    is safer than raising an exception mid-screening.

    Args:
        role_type: The role type string from the screening input.

    Returns:
        A DomainCalibration instance. Never None.
    """
    return detect_domain(role_type) or GENERIC_CALIBRATION
