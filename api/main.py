"""
WHY: The FastAPI application entry point. All middleware, router registration,
and app-level configuration lives here and nowhere else. Route logic lives
in api/routes/; auth logic lives in api/auth.py; schemas in api/schemas.py.

HOW: Routers are included with the /api/v1 prefix for all domain routes.
The health endpoint is prefix-free so load balancers can reach it without
knowing the API version.

CORS: allow_origins=["*"] is intentional for v0.1 — SCREEN is a backend API,
not a browser app. Callers are server-side integrations. Restrict origins in
production if a browser client is ever added.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import feedback, health, runs, screen

app = FastAPI(
    title="SCREEN API",
    description="Structured Candidate Reasoning and Evaluation Engine",
    version="0.1.0",
)

# WHY: CORS wildcard is acceptable for a server-to-server API. If a browser
# client is added in a future version, restrict allow_origins to explicit domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check — no prefix, no auth. Reachable by load balancers and uptime monitors.
app.include_router(health.router)

# Domain routes — all under /api/v1 and protected by authenticate_request
app.include_router(screen.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
