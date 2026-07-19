from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import (
    AssetOut,
    GenerationJobOut,
    GenerationSubmit,
    ReviewCreate,
    ReviewOut,
    StudioSummary,
)
from app.core.db import get_db
from app.core.deps import CurrentUser
from app.models import Asset, CostRecord, GenerationJob, Project, Review
from app.services.gateway import enqueue_generation
from app.services.storage import get_storage
from app.services.studio import add_review

router = APIRouter(tags=["studio"])


def _enrich_job(job: GenerationJob) -> GenerationJobOut:
    out = GenerationJobOut.model_validate(job)
    if job.result_uri:
        out.media_url = f"/api/media/{job.project_id}/{job.id}/primary"
    # Audio bed for video proxies uses convention in storage path sibling assets
    if job.modality == "video":
        out.audio_url = f"/api/media/{job.project_id}/{job.id}/audio"
    return out


def _enrich_asset(asset: Asset) -> AssetOut:
    out = AssetOut.model_validate(asset)
    if asset.storage_path:
        out.media_url = f"/api/assets/file/{asset.id}"
    return out


@router.get("/api/projects/{project_id}/studio/summary", response_model=StudioSummary)
def studio_summary(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> StudioSummary:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    jobs = db.query(GenerationJob).filter(GenerationJob.project_id == project_id).all()
    totals: dict[str, int] = {}
    for j in jobs:
        totals[j.modality] = totals.get(j.modality, 0) + 1

    reviewed_ids = {
        r.generation_job_id
        for r in db.query(Review)
        .join(GenerationJob, Review.generation_job_id == GenerationJob.id)
        .filter(GenerationJob.project_id == project_id)
        .all()
    }
    approved = (
        db.query(Review)
        .join(GenerationJob, Review.generation_job_id == GenerationJob.id)
        .filter(GenerationJob.project_id == project_id, Review.decision == "approve")
        .count()
    )
    pending = len([j for j in jobs if j.id not in reviewed_ids and j.status == "succeeded"])
    spent = (
        db.query(func.coalesce(func.sum(CostRecord.amount), 0.0))
        .filter(CostRecord.project_id == project_id)
        .scalar()
    )

    return StudioSummary(
        project_id=project_id,
        totals=totals,
        approved=approved,
        pending_review=pending,
        spent=float(spent or 0),
    )


@router.post(
    "/api/projects/{project_id}/studio/generate",
    response_model=GenerationJobOut,
    status_code=status.HTTP_201_CREATED,
)
def studio_generate(
    project_id: str, payload: GenerationSubmit, user: CurrentUser, db: Session = Depends(get_db)
) -> GenerationJobOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    character_key = None
    if payload.character_name:
        key = payload.character_name.strip().lower()
        if "kardokh" in key:
            character_key = "kardokh"
        elif "kurdiya" in key:
            character_key = "kurdiya"
    job = enqueue_generation(
        db,
        project_id=project_id,
        modality=payload.modality,
        prompt=payload.prompt,
        model=payload.model,
        character_key=character_key,
        character_name=payload.character_name,
        duration_seconds=payload.duration_seconds,
        dialogue_lines=payload.dialogue_lines,
        prefer_external=payload.provider == "external-fallback",
        requested_by=user.id,
    )
    return _enrich_job(job)


@router.get("/api/projects/{project_id}/assets", response_model=list[AssetOut])
def list_assets(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[AssetOut]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    assets = (
        db.query(Asset)
        .filter(Asset.project_id == project_id, Asset.soft_deleted.is_(False))
        .order_by(Asset.created_at.desc())
        .all()
    )
    return [_enrich_asset(a) for a in assets]


@router.post(
    "/api/projects/{project_id}/generations/{job_id}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    project_id: str,
    job_id: str,
    payload: ReviewCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> Review:
    job = db.get(GenerationJob, job_id)
    if not job or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return add_review(
        db,
        job=job,
        decision=payload.decision,
        notes=payload.notes,
        quality_score=payload.quality_score,
    )


@router.get("/api/projects/{project_id}/generations/{job_id}/reviews", response_model=list[ReviewOut])
def list_reviews(project_id: str, job_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[Review]:
    job = db.get(GenerationJob, job_id)
    if not job or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return db.query(Review).filter(Review.generation_job_id == job_id).order_by(Review.created_at.desc()).all()


@router.get("/api/media/{project_id}/{job_id}/{kind}")
def get_job_media(project_id: str, job_id: str, kind: str, db: Session = Depends(get_db)) -> Response:
    job = db.get(GenerationJob, job_id)
    if not job or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Job not found")

    if kind == "primary":
        if not job.result_uri:
            raise HTTPException(status_code=404, detail="No media")
        key = job.result_uri
    elif kind == "audio":
        candidates = (
            db.query(Asset)
            .filter(Asset.project_id == project_id, Asset.asset_type == "audio")
            .order_by(Asset.created_at.desc())
            .all()
        )
        asset = next(
            (a for a in candidates if (a.metadata_json or {}).get("linked_job") == job_id),
            None,
        )
        if not asset or not asset.storage_path:
            raise HTTPException(status_code=404, detail="No audio bed")
        key = asset.storage_path
    else:
        raise HTTPException(status_code=404, detail="Unknown media kind")

    try:
        data, content_type = get_storage().get_object(key)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Media missing in storage") from exc
    return Response(content=data, media_type=content_type)


@router.get("/api/assets/file/{asset_id}")
def get_asset_file(asset_id: str, db: Session = Depends(get_db)) -> Response:
    asset = db.get(Asset, asset_id)
    if not asset or asset.soft_deleted or not asset.storage_path:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        data, content_type = get_storage().get_object(asset.storage_path)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Asset missing in storage") from exc
    return Response(content=data, media_type=content_type)
