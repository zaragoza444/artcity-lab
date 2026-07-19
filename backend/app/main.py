from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

settings = get_settings()

app = FastAPI(
    title="Art City AI Studio",
    description="Art City production OS + AI Core (Model Gateway, Data Lab, registries)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "health": "/health",
        "gateway": "/api/v1/ai",
    }
