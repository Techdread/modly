import os

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Health check — used by Electron to know the API is ready."""
    return {
        "status": "ok",
        "service": "modly",
        "version": "0.3.5",
        "api_prefix": "/api",
        "auth": bool(os.environ.get("MODLY_API_TOKEN")),
    }
