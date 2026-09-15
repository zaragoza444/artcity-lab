"""AC Graphic Motion REST API — /api/v1/graphic-motion."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.schemas_agm import PreviewIn, QuoteIn, RenderIn, SceneCreateIn, SceneOut, ValidateIn
from app.core.db import SessionLocal, get_db
from app.core.deps import CurrentUser
from app.core.ids import load_project
from app.models_agm import AgmJob, AgmScene
from app.services import agm_acx, agm_render, agm_scene
from app.services.agm_validate import validate_graph

router = APIRouter(prefix="/api/v1/graphic-motion", tags=["graphic-motion"])


def _scene_response(scene: AgmScene, rev=None) -> dict[str, Any]:
    return agm_scene.scene_out(scene, rev)


@router.get("/features")
def features(user: CurrentUser) -> dict[str, bool]:
    return {"graphic_motion": True, "preview": True, "render": True, "acx": True}


@router.post("/acx/quote")
def acx_quote(payload: QuoteIn, user: CurrentUser) -> dict[str, Any]:
    return agm_acx.quote_render(
        job_kind=payload.job_kind,
        duration_ms=payload.duration_ms,
        profile=payload.profile,
    )


@router.get("/projects/{project_id}/scenes", response_model=list[SceneOut])
def list_project_scenes(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    load_project(db, project_id)
    rows = (
        db.query(AgmScene)
        .filter(AgmScene.project_id == project_id, AgmScene.soft_deleted.is_(False))
        .order_by(AgmScene.created_at.desc())
        .all()
    )
    return [_scene_response(s) for s in rows]


@router.post("/scenes", status_code=status.HTTP_201_CREATED, response_model=SceneOut)
def create_scene(
    payload: SceneCreateIn,
    user: CurrentUser,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    scene, rev = agm_scene.create_scene(
        db,
        project_id=payload.project_id,
        name=payload.name,
        user_id=getattr(user, "id", None),
        graph=payload.graph,
        locale=payload.locale,
        direction=payload.direction,
        idempotency_key=idempotency_key,
    )
    return _scene_response(scene, rev)


@router.get("/scenes/{scene_id}", response_model=SceneOut)
def get_scene(scene_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    scene = agm_scene.get_scene(db, scene_id)
    rev = None
    if scene.head_revision_id:
        rev = agm_scene.get_revision(db, scene_id, scene.head_revision_id)
    return _scene_response(scene, rev)


@router.patch("/scenes/{scene_id}", response_model=SceneOut)
async def patch_scene(
    scene_id: str,
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
    if_match: Optional[str] = Header(default=None, alias="If-Match"),
) -> dict:
    if not if_match:
        raise HTTPException(status_code=400, detail="If-Match header required")
    raw = await request.json()
    if not isinstance(raw, list):
        raise HTTPException(status_code=400, detail="JSON Patch array required")
    scene, rev = agm_scene.patch_scene(
        db,
        scene_id=scene_id,
        operations=raw,
        if_match=if_match,
        user_id=getattr(user, "id", None),
    )
    return _scene_response(scene, rev)


@router.delete("/scenes/{scene_id}", response_model=SceneOut)
def delete_scene(scene_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    scene = agm_scene.soft_delete_scene(db, scene_id)
    return _scene_response(scene)


@router.get("/scenes/{scene_id}/revisions")
def list_revisions(scene_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    return [agm_scene.revision_out(r) for r in agm_scene.list_revisions(db, scene_id)]


@router.get("/scenes/{scene_id}/revisions/{revision_id}")
def get_revision(scene_id: str, revision_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    return agm_scene.revision_out(agm_scene.get_revision(db, scene_id, revision_id))


@router.post("/validate")
def validate_unsaved(payload: ValidateIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    if not payload.graph:
        raise HTTPException(status_code=400, detail="graph required")
    return validate_graph(payload.graph, db=db, profile=payload.profile, strict_assets=False)


@router.post("/scenes/{scene_id}/validate")
def validate_scene(
    scene_id: str,
    payload: ValidateIn,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    scene = agm_scene.get_scene(db, scene_id)
    if payload.graph:
        graph = payload.graph
    else:
        rid = payload.revision_id or scene.head_revision_id
        if not rid:
            raise HTTPException(status_code=400, detail="no revision")
        rev = agm_scene.get_revision(db, scene_id, rid)
        graph = rev.graph_json or {}
    return validate_graph(graph, db=db, profile=payload.profile, strict_assets=True)


@router.post("/scenes/{scene_id}/preview", status_code=status.HTTP_202_ACCEPTED)
def preview_scene(
    scene_id: str,
    payload: PreviewIn,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    scene = agm_scene.get_scene(db, scene_id)
    job = agm_render.queue_preview(
        db,
        scene=scene,
        user_id=getattr(user, "id", None),
        body=payload.model_dump(),
    )
    return agm_render.job_out(job)


@router.post("/scenes/{scene_id}/render", status_code=status.HTTP_202_ACCEPTED)
def render_scene(
    scene_id: str,
    payload: RenderIn,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    scene = agm_scene.get_scene(db, scene_id)
    job = agm_render.queue_render(
        db,
        scene=scene,
        user_id=getattr(user, "id", None),
        body=payload.model_dump(),
    )
    return agm_render.job_out(job)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    job = db.get(AgmJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return agm_render.job_out(job)


@router.delete("/jobs/{job_id}")
def cancel_job(job_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    return agm_render.job_out(agm_render.request_cancel(db, job_id))


@router.post("/jobs/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_job(job_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    return agm_render.job_out(agm_render.retry_job(db, job_id, getattr(user, "id", None)))


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str, user: CurrentUser) -> StreamingResponse:
    """SSE progress stream for AGM jobs."""

    async def gen():
        last_status = None
        for _ in range(120):
            db = SessionLocal()
            try:
                job = db.get(AgmJob, job_id)
                if not job:
                    yield f"event: error\ndata: {json.dumps({'code': 'not_found'})}\n\n"
                    return
                payload = {
                    "job_id": job.id,
                    "status": job.status,
                    "progress": job.progress,
                    "error_code": job.error_code,
                    "outputs": job.outputs_json or [],
                }
                if job.status != last_status or True:
                    yield f"event: progress\ndata: {json.dumps(payload, default=str)}\n\n"
                    last_status = job.status
                if job.status in {"completed", "failed", "cancelled"}:
                    yield f"event: done\ndata: {json.dumps(payload, default=str)}\n\n"
                    return
            finally:
                db.close()
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/parity/still")
def parity_still(payload: dict[str, Any], user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    revision_id = payload.get("revision_id")
    if not revision_id:
        raise HTTPException(status_code=400, detail="revision_id required")
    return agm_render.preview_parity_still(db, revision_id=revision_id, at_ms=int(payload.get("at_ms") or 0))
