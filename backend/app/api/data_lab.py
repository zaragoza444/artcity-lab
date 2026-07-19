from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_roles
from app.core.enums import DATASET_UPLOAD_ROLES, AnnotationStatus, DatasetStatus
from app.models import User, AnnotationTask, Dataset, IngestionRun
from app.services.speech import detect_language_dialect
from app.services.storage import get_storage

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
    status: Optional[str] = None
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
    run = IngestionRun(source_type="upload", status="processing", operator_id=user.id, report={})
    db.add(run)
    db.flush()

    if dataset_id:
        dataset = db.get(Dataset, dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
    else:
        dataset = Dataset(
            name=dataset_name or f"Ingest {datetime.now(timezone.utc).date()}",
            category="archive",
            media_type="mixed",
            owner="Art City",
            status=DatasetStatus.INGESTING.value,
            created_by=user.id,
        )
        db.add(dataset)
        db.flush()

    storage = get_storage()
    imported = 0
    failed = 0
    duplicates = 0
    unknown_rights = 0
    total_bytes = 0
    text_samples: list[str] = []
    dialect_votes: dict[str, int] = {}
    seen: set[str] = set()
    start = datetime.now(timezone.utc)

    for f in files:
        try:
            data = await f.read()
            digest = hashlib.sha256(data).hexdigest()
            if digest in seen:
                duplicates += 1
                continue
            seen.add(digest)
            key = f"datasets/{dataset.id}/raw/{digest[:16]}_{f.filename or uuid4().hex}"
            storage.upload_bytes(key, data, f.content_type or "application/octet-stream")
            imported += 1
            total_bytes += len(data)
            unknown_rights += 1
            name = (f.filename or "").lower()
            ctype = (f.content_type or "").lower()
            if "text" in ctype or name.endswith((".txt", ".md", ".srt", ".vtt", ".csv", ".json")):
                try:
                    sample = data[:4000].decode("utf-8", errors="ignore")
                    if sample.strip():
                        text_samples.append(sample)
                        detected = detect_language_dialect(sample)
                        dialect_votes[detected["dialect"]] = dialect_votes.get(detected["dialect"], 0) + 1
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            failed += 1

    detected_dialect = dialect
    detected_language = language or "ku"
    detection_confidence = None
    if dialect_votes:
        detected_dialect = max(dialect_votes, key=dialect_votes.get)
        detection_confidence = round(
            dialect_votes[detected_dialect] / max(sum(dialect_votes.values()), 1), 3
        )
    elif text_samples:
        detected = detect_language_dialect("\n".join(text_samples[:3]))
        detected_dialect = detected["dialect"]
        detected_language = detected["language"]
        detection_confidence = detected["confidence"]

    if detected_language and not dataset.language:
        dataset.language = detected_language
    if detected_dialect and not dataset.dialect:
        dataset.dialect = detected_dialect

    dataset.record_count = (dataset.record_count or 0) + imported
    dataset.size_bytes = (dataset.size_bytes or 0) + total_bytes
    dataset.status = DatasetStatus.NEEDS_REVIEW.value
    dataset.storage_path = f"datasets/{dataset.id}/raw/"
    dataset.checksum = hashlib.sha256(",".join(sorted(seen)).encode()).hexdigest() if seen else None

    run.dataset_id = dataset.id
    run.status = "completed"
    run.finished_at = datetime.now(timezone.utc)
    run.report = {
        "imported": imported,
        "duplicates": duplicates,
        "failed": failed,
        "unknown_rights": unknown_rights,
        "needs_review": imported,
        "total_bytes": total_bytes,
        "duration_seconds": (run.finished_at - start).total_seconds(),
        "operator": user.email,
        "language": detected_language,
        "dialect": detected_dialect,
        "dialect_votes": dialect_votes,
        "detection_confidence": detection_confidence,
        "text_files_scanned": len(text_samples),
    }
    db.commit()
    db.refresh(run)
    return run


@router.get("/api/data-lab/ingestions", response_model=list[IngestionOut])
def list_ingestions(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(100).all()


@router.get("/api/data-lab/annotations", response_model=list[AnnotationOut])
def list_annotations(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(AnnotationTask).order_by(AnnotationTask.created_at.desc()).limit(200).all()


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
def update_annotation(task_id: str, payload: AnnotationUpdate, user: CurrentUser, db: Session = Depends(get_db)):
    task = db.get(AnnotationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Annotation not found")
    history = list(task.revision_history or [])
    history.append({"at": datetime.now(timezone.utc).isoformat(), "by": user.email, "before": task.labels})
    task.revision_history = history
    if payload.labels is not None:
        task.labels = payload.labels
    if payload.status is not None:
        task.status = payload.status
    if payload.comment:
        comments = list(task.comments or [])
        comments.append({"by": user.email, "text": payload.comment, "at": datetime.now(timezone.utc).isoformat()})
        task.comments = comments
    db.commit()
    db.refresh(task)
    return task
