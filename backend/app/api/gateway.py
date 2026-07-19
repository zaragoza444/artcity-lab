from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.schemas import GenerationJobOut
from app.api.studio import _enrich_job
from app.core.db import get_db
from app.core.deps import CurrentUser, client_ip
from app.models import GenerationJob, Project, RegisteredModel
from app.services.audit import write_audit
from app.services.gateway import cancel_job, enqueue_generation, retry_job
from app.services.providers import list_providers

router = APIRouter(prefix="/api/v1/ai", tags=["model-gateway"])


class GenerateRequest(BaseModel):
    project_id: str
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None
    character_key: Optional[str] = None
    character_name: Optional[str] = None
    duration_seconds: float = Field(default=4.0, ge=0.5, le=60.0)
    dialogue_lines: Optional[list[str]] = None
    prefer_external: bool = False
    params: Optional[dict[str, Any]] = None


class ProviderOut(BaseModel):
    name: str
    healthy: bool


class ModelRegistryOut(BaseModel):
    id: str
    name: str
    version: str
    model_type: str
    modality: str
    status: str
    character_key: Optional[str] = None
    commercial_use: bool
    checksum: Optional[str] = None

    model_config = {"from_attributes": True}


def _require_project(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _generate(modality: str, payload: GenerateRequest, user: CurrentUser, request: Request, db: Session) -> GenerationJobOut:
    _require_project(db, payload.project_id)
    job = enqueue_generation(
        db,
        project_id=payload.project_id,
        modality=modality,
        prompt=payload.prompt,
        model=payload.model,
        character_key=payload.character_key,
        character_name=payload.character_name,
        duration_seconds=payload.duration_seconds,
        dialogue_lines=payload.dialogue_lines,
        prefer_external=payload.prefer_external,
        requested_by=user.id,
        params=payload.params,
    )
    write_audit(
        db,
        action="ai_generate",
        resource_type="generation_job",
        resource_id=job.id,
        user_id=user.id,
        detail={"modality": modality, "provider": job.provider, "model": job.model},
        ip_address=client_ip(request),
    )
    db.commit()
    return _enrich_job(job)


@router.post("/images/generate", response_model=GenerationJobOut, status_code=201)
def generate_image(payload: GenerateRequest, user: CurrentUser, request: Request, db: Session = Depends(get_db)):
    return _generate("image", payload, user, request, db)


@router.post("/videos/generate", response_model=GenerationJobOut, status_code=201)
def generate_video(payload: GenerateRequest, user: CurrentUser, request: Request, db: Session = Depends(get_db)):
    return _generate("video", payload, user, request, db)


@router.post("/voices/generate", response_model=GenerationJobOut, status_code=201)
def generate_voice(payload: GenerateRequest, user: CurrentUser, request: Request, db: Session = Depends(get_db)):
    return _generate("voice", payload, user, request, db)


@router.post("/audio/generate", response_model=GenerationJobOut, status_code=201)
def generate_audio(payload: GenerateRequest, user: CurrentUser, request: Request, db: Session = Depends(get_db)):
    return _generate("audio", payload, user, request, db)


@router.post("/music/generate", response_model=GenerationJobOut, status_code=201)
def generate_music(payload: GenerateRequest, user: CurrentUser, request: Request, db: Session = Depends(get_db)):
    return _generate("music", payload, user, request, db)


@router.get("/jobs/{job_id}", response_model=GenerationJobOut)
def get_job(job_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _enrich_job(job)


@router.post("/jobs/{job_id}/cancel", response_model=GenerationJobOut)
def cancel(job_id: str, user: CurrentUser, request: Request, db: Session = Depends(get_db)):
    try:
        job = cancel_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_audit(db, action="ai_cancel", resource_type="generation_job", resource_id=job_id, user_id=user.id, ip_address=client_ip(request))
    db.commit()
    return _enrich_job(job)


@router.post("/jobs/{job_id}/retry", response_model=GenerationJobOut, status_code=201)
def retry(job_id: str, user: CurrentUser, request: Request, db: Session = Depends(get_db)):
    try:
        job = retry_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_audit(db, action="ai_retry", resource_type="generation_job", resource_id=job.id, user_id=user.id, ip_address=client_ip(request))
    db.commit()
    return _enrich_job(job)


@router.get("/models", response_model=list[ModelRegistryOut])
def list_models(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(RegisteredModel).order_by(RegisteredModel.created_at.desc()).all()


@router.get("/models/{model_id}", response_model=ModelRegistryOut)
def get_model(model_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    model = db.get(RegisteredModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/providers", response_model=list[ProviderOut])
def providers(user: CurrentUser) -> list[ProviderOut]:
    return [ProviderOut(**p) for p in list_providers()]
