"""
Modly FastAPI backend.
Runs locally within the Electron app to provide AI inference endpoints.
"""
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from routers import generation, model, optimize, status, settings, extensions, export, workflow_runs


def _cors_origins() -> list[str]:
    raw = os.environ.get("MODLY_CORS_ORIGINS")
    if raw is None:
        return ["*"]
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


def _is_health_path(path: str) -> bool:
    return path in {"/health", "/api/health"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize the registry (instantiates all adapters)
    from services.generator_registry import generator_registry
    generator_registry.initialize()
    yield
    # Shutdown: unload all models
    generator_registry.unload_all()


class _StatusFilter(logging.Filter):
    def filter(self, record):
        return "/generate/status/" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(_StatusFilter())


app = FastAPI(
    title="Modly API",
    version="0.3.5",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def optional_bearer_auth(request: Request, call_next):
    """Wan2GP-style guard: MODLY_API_TOKEN protects every non-health route."""
    token = os.environ.get("MODLY_API_TOKEN") or ""
    if (
        not token
        or request.method == "OPTIONS"
        or _is_health_path(request.url.path)
    ):
        return await call_next(request)

    auth = request.headers.get("Authorization", "")
    if not secrets.compare_digest(auth, f"Bearer {token}"):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    return await call_next(request)


app.include_router(status.router)
app.include_router(settings.router)
app.include_router(model.router,      prefix="/model")
app.include_router(generation.router, prefix="/generate")
app.include_router(optimize.router,    prefix="/optimize")
app.include_router(extensions.router, prefix="/extensions")
app.include_router(export.router,          prefix="/export")
app.include_router(workflow_runs.router,   prefix="/workflow-runs")

app.include_router(status.router,          prefix="/api", include_in_schema=False)
app.include_router(settings.router,        prefix="/api", include_in_schema=False)
app.include_router(model.router,           prefix="/api/model", include_in_schema=False)
app.include_router(generation.router,      prefix="/api/generate", include_in_schema=False)
app.include_router(optimize.router,        prefix="/api/optimize", include_in_schema=False)
app.include_router(extensions.router,      prefix="/api/extensions", include_in_schema=False)
app.include_router(export.router,          prefix="/api/export", include_in_schema=False)
app.include_router(workflow_runs.router,   prefix="/api/workflow-runs", include_in_schema=False)


def _workspace_path(full_path: str) -> Path:
    import services.generator_registry as reg
    workspace_root = reg.WORKSPACE_DIR.resolve()
    file_path = (workspace_root / full_path).resolve()
    try:
        file_path.relative_to(workspace_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    return file_path


# Serve generated files from workspace — dynamic so path changes take effect immediately
@app.get("/workspace/{full_path:path}")
@app.get("/api/workspace/{full_path:path}", include_in_schema=False)
async def serve_workspace_file(full_path: str):
    file_path = _workspace_path(full_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path))
