from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.cinema import router as cinema_router
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.publishing import router as publishing_router
from app.api.studio import router as studio_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Art City AI Studio",
    description="Art City production & publishing — cinema packages, masters, delivery checklist",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(studio_router)
app.include_router(cinema_router)
app.include_router(publishing_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Art City AI Studio",
        "docs": "/docs",
        "health": "/health",
    }
