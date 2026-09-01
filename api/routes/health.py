"""
WHY: The health endpoint is the one unauthenticated route. It serves two
purposes: load-balancer health checks (does the process respond?) and
quick operator verification of which model tier is active in this deployment.

HOW: No DB access, no auth. Returns a static JSON body with the version and
the tier-1 model name from settings so operators can confirm the right config
is loaded without grepping env vars.
"""

from fastapi import APIRouter

from screen.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    WHY: Single-hop health check. Any downstream that receives a 200 here
    knows the process is up and the config is loaded. The model_tier1 field
    lets an operator confirm the correct model is active without a deploy log.

    Returns:
        dict with status, version, and active tier-1 model name.
    """
    return {
        "status": "ok",
        "version": "0.1.0",
        "model_tier1": settings.openrouter_model_tier1,
    }
