from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.auth import router as auth_router
from app.api.cinema import router as cinema_router
from app.api.data_lab import router as data_lab_router
from app.api.evaluations import router as evaluations_router
from app.api.gateway import router as gateway_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.projects import router as projects_router
from app.api.publishing import router as publishing_router
from app.api.registries import router as registries_router
from app.api.speech import router as speech_router
from app.api.studio import router as studio_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers

settings = get_settings()

API_DESCRIPTION = """
Art City AI Studio — private production OS + AI Core.

**Auth:** `POST /api/auth/login` then `Authorization: Bearer <access_token>`.

**Docs:** Full human-readable reference in repository `docs/API.md`.

**Live:** https://backend-production-9533.up.railway.app
"""

tags_metadata = [
    {"name": "auth", "description": "Login, refresh, users, RBAC"},
    {"name": "model-gateway", "description": "Art City Model Gateway — sole AI generation entry"},
    {"name": "speech", "description": "Kurdish ASR — Sorani / Badini / Kurmanji + subtitles"},
    {"name": "projects", "description": "Projects, characters, scripts, generations"},
    {"name": "studio", "description": "Studio generate, assets, reviews, media"},
    {"name": "cinema", "description": "Full advertising campaign packages + QC + ZIP"},
    {"name": "publishing", "description": "Masters packaging and channel release"},
    {"name": "data-lab", "description": "Dataset ingest and annotation workspace"},
    {"name": "registries", "description": "Datasets, rights, model registry, training"},
    {"name": "knowledge", "description": "Kurdish knowledge base"},
    {"name": "evaluations", "description": "Model evaluation and human approval"},
]

app = FastAPI(
    title="Art City AI Studio",
    description=API_DESCRIPTION,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={"name": "Art City Group", "email": "admin@artcity.ai"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(gateway_router)
app.include_router(registries_router)
app.include_router(data_lab_router)
app.include_router(knowledge_router)
app.include_router(evaluations_router)
app.include_router(speech_router)
app.include_router(projects_router)
app.include_router(studio_router)
app.include_router(cinema_router)
app.include_router(publishing_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Art City AI Studio",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health",
        "gateway": "/api/v1/ai",
        "api_guide": "docs/API.md",
    }


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
    )
    schema["components"] = schema.get("components") or {}
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "1) POST /api/auth/login  2) Authorize with access_token  3) Fill required body fields before Execute",
        }
    }
    # Do not force Bearer globally — login/health/root stay open in Swagger.
    # Protected routes already declare HTTPBearer via dependencies.
    schema["security"] = []
    public_prefixes = ("/", "/health", "/docs", "/redoc", "/openapi.json", "/api/auth/login", "/api/auth/refresh")
    for path, methods in schema.get("paths", {}).items():
        is_public = path in public_prefixes or path.startswith("/health")
        for method, op in methods.items():
            if method in ("get", "post", "put", "patch", "delete"):
                if is_public or path == "/api/auth/login" or path == "/api/auth/refresh":
                    op["security"] = []
                else:
                    op["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]
