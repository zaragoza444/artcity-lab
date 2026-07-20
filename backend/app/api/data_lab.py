from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_roles
from app.core.enums import DATASET_UPLOAD_ROLES, AnnotationStatus
from app.models import AnnotationTask, Dataset, IngestionRun, User
from app.services import data_lab as data_lab_service

router = APIRouter(tags=["data-lab"])


class IngestionOut(BaseModel):
    id: str
    dataset_id: Optional[str]
    source_type: str
    status: str
    report: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnnotationCreate(BaseModel):
    dataset_id: str
    media_type: str = "text"
    payload: dict
    labels: Optional[dict] = None


class AnnotationOut(BaseModel):
    id: str
    dataset_id: str
    media_type: str
    payload: dict
    labels: Optional[dict]
    status: str
    comments: Optional[list]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnnotationUpdate(BaseModel):
    labels: Optional[dict] = None
    status: Optional[str] = Field(
        default=None,
        pattern="^(pending|in_review|approved|rejected|conflict)$",
    )
    comment: Optional[str] = None


@router.post("/api/data-lab/ingest", response_model=IngestionOut, status_code=201)
async def ingest_files(
    user: User = Depends(require_roles(*DATASET_UPLOAD_ROLES)),
    dataset_id: Optional[str] = Form(None),
    dataset_name: Optional[str] = Form(None),
    language: Optional[str] = Form("ku"),
    dialect: Optional[str] = Form(None),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    return await data_lab_service.ingest_uploads(
        db,
        user=user,
        files=files,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        language=language,
        dialect=dialect,
    )


@router.get("/api/data-lab/ingestions", response_model=list[IngestionOut])
def list_ingestions(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(100).all()


@router.get("/api/data-lab/ingestions/{run_id}", response_model=IngestionOut)
def get_ingestion(run_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    return data_lab_service.get_ingestion(db, run_id)


@router.get("/api/data-lab/datasets/{dataset_id}")
def get_dataset(dataset_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    return data_lab_service.get_dataset_detail(db, dataset_id)


@router.get("/api/data-lab/datasets/{dataset_id}/files")
def list_files(dataset_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    return data_lab_service.list_dataset_files(db, dataset_id)


@router.get("/api/data-lab/datasets/{dataset_id}/manifest")
def dataset_manifest(dataset_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    return data_lab_service.build_training_manifest(db, dataset_id)


@router.get("/api/data-lab/datasets/{dataset_id}/export")
def export_dataset(
    dataset_id: str,
    user: CurrentUser,
    format: str = Query(default="jsonl", pattern="^(jsonl|csv)$"),
    persist: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Response:
    body, media, filename = data_lab_service.export_dataset(
        db, dataset_id, fmt=format, persist=persist
    )
    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/media/datasets/{dataset_id}/files/{file_id}")
def dataset_file_media(
    dataset_id: str,
    file_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    data, media, filename = data_lab_service.get_dataset_file_bytes(db, dataset_id, file_id)
    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/api/data-lab/annotations", response_model=list[AnnotationOut])
def list_annotations(
    user: CurrentUser,
    db: Session = Depends(get_db),
    dataset_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    media_type: Optional[str] = Query(default=None),
):
    q = db.query(AnnotationTask)
    if dataset_id:
        q = q.filter(AnnotationTask.dataset_id == dataset_id)
    if status:
        q = q.filter(AnnotationTask.status == status)
    if media_type:
        q = q.filter(AnnotationTask.media_type == media_type)
    return q.order_by(AnnotationTask.created_at.desc()).limit(200).all()


@router.post("/api/data-lab/annotations", response_model=AnnotationOut, status_code=201)
def create_annotation(payload: AnnotationCreate, user: CurrentUser, db: Session = Depends(get_db)):
    if not db.get(Dataset, payload.dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found")
    task = AnnotationTask(
        dataset_id=payload.dataset_id,
        media_type=payload.media_type,
        payload=payload.payload,
        labels=payload.labels or {},
        status=AnnotationStatus.PENDING.value,
        assignee_id=user.id,
        comments=[],
        revision_history=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/api/data-lab/annotations/{task_id}", response_model=AnnotationOut)
def update_annotation(
    task_id: str, payload: AnnotationUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    return data_lab_service.update_annotation_task(
        db,
        task_id=task_id,
        user=user,
        labels=payload.labels,
        status_value=payload.status,
        comment=payload.comment,
    )
