"""Art City Data Lab — ingest, inventory, annotation helpers, export."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.enums import AnnotationStatus, DatasetStatus, RightsStatus
from app.models import AnnotationTask, Dataset, DatasetFile, IngestionRun, RightsRecord, User
from app.services.speech import detect_language_dialect, wav_duration_seconds
from app.services.storage import get_storage

TEXT_EXTENSIONS = {".txt", ".md", ".srt", ".vtt", ".csv", ".json", ".jsonl"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt"}


def sniff_media_type(filename: str, content_type: str | None) -> str:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    ext = ""
    if "." in name:
        ext = "." + name.rsplit(".", 1)[-1]
    if ext in SUBTITLE_EXTENSIONS or "subrip" in ctype or "vtt" in ctype:
        return "subtitle"
    if ext in TEXT_EXTENSIONS or ctype.startswith("text/") or "json" in ctype:
        return "text"
    if ext in AUDIO_EXTENSIONS or ctype.startswith("audio/"):
        return "speech" if ext in {".wav", ".mp3", ".m4a", ".flac"} else "audio"
    if ext in IMAGE_EXTENSIONS or ctype.startswith("image/"):
        return "image"
    if ext in VIDEO_EXTENSIONS or ctype.startswith("video/"):
        return "video"
    if "music" in name:
        return "music"
    return "other"


def dataset_rights_status(db: Session, dataset_id: str) -> str:
    rights = (
        db.query(RightsRecord)
        .filter(RightsRecord.dataset_id == dataset_id)
        .order_by(RightsRecord.created_at.desc())
        .first()
    )
    if not rights:
        return RightsStatus.UNKNOWN.value
    return rights.legal_status or RightsStatus.UNKNOWN.value


def _existing_checksums(db: Session, dataset_id: str) -> set[str]:
    rows = (
        db.query(DatasetFile.checksum)
        .filter(DatasetFile.dataset_id == dataset_id, DatasetFile.soft_deleted.is_(False))
        .all()
    )
    return {r[0] for r in rows if r[0]}


async def ingest_uploads(
    db: Session,
    *,
    user: User,
    files: list[UploadFile],
    dataset_id: str | None = None,
    dataset_name: str | None = None,
    language: str | None = "ku",
    dialect: str | None = None,
) -> IngestionRun:
    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required")

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
            language=language or "ku",
            dialect=dialect,
        )
        db.add(dataset)
        db.flush()

    storage = get_storage()
    rights_status = dataset_rights_status(db, dataset.id)
    known = _existing_checksums(db, dataset.id)
    batch_seen: set[str] = set()

    imported = 0
    failed = 0
    duplicates = 0
    unknown_rights = 0
    total_bytes = 0
    text_samples: list[str] = []
    dialect_votes: dict[str, int] = {}
    file_ids: list[str] = []
    media_counts: dict[str, int] = {}
    start = datetime.now(timezone.utc)

    for f in files:
        try:
            data = await f.read()
            if not data:
                failed += 1
                continue
            digest = hashlib.sha256(data).hexdigest()
            if digest in batch_seen or digest in known:
                duplicates += 1
                continue
            batch_seen.add(digest)
            known.add(digest)

            filename = (f.filename or f"file-{uuid4().hex[:8]}").replace("/", "_").replace("\\", "_")
            content_type = f.content_type or "application/octet-stream"
            media_type = sniff_media_type(filename, content_type)
            key = f"datasets/{dataset.id}/raw/{digest[:16]}_{filename}"
            storage.upload_bytes(key, data, content_type)

            file_lang = language or dataset.language
            file_dialect = dialect or dataset.dialect
            duration = wav_duration_seconds(data) if media_type in {"speech", "audio"} else None
            sample_text: str | None = None

            if media_type in {"text", "subtitle"}:
                try:
                    sample_text = data[:8000].decode("utf-8", errors="ignore")
                    if sample_text.strip():
                        text_samples.append(sample_text)
                        detected = detect_language_dialect(sample_text)
                        file_lang = detected.get("language") or file_lang
                        file_dialect = detected.get("dialect") or file_dialect
                        dialect_votes[detected["dialect"]] = dialect_votes.get(detected["dialect"], 0) + 1
                except Exception:  # noqa: BLE001
                    pass

            df = DatasetFile(
                id=str(uuid4()),
                dataset_id=dataset.id,
                ingestion_run_id=run.id,
                filename=filename,
                storage_key=key,
                checksum=digest,
                content_type=content_type,
                media_type=media_type,
                size_bytes=len(data),
                language=file_lang,
                dialect=file_dialect,
                rights_status=rights_status,
                duration_seconds=duration,
                metadata_json={
                    "original_filename": f.filename,
                    "operator_id": user.id,
                },
            )
            db.add(df)
            db.flush()
            file_ids.append(df.id)
            imported += 1
            total_bytes += len(data)
            media_counts[media_type] = media_counts.get(media_type, 0) + 1
            if rights_status == RightsStatus.UNKNOWN.value:
                unknown_rights += 1

            if media_type in {"text", "subtitle"} and sample_text and sample_text.strip():
                db.add(
                    AnnotationTask(
                        dataset_id=dataset.id,
                        media_type=media_type,
                        payload={
                            "text": sample_text[:4000],
                            "language": file_lang or "ku",
                            "file_id": df.id,
                            "storage_key": key,
                            "filename": filename,
                        },
                        labels={
                            "dialect": file_dialect,
                            "source": "ingest",
                            "file_id": df.id,
                        },
                        status=AnnotationStatus.PENDING.value,
                        assignee_id=user.id,
                        comments=[{"note": "Auto-created from Data Lab ingest"}],
                        revision_history=[],
                    )
                )
            elif media_type == "speech":
                db.add(
                    AnnotationTask(
                        dataset_id=dataset.id,
                        media_type="speech",
                        payload={
                            "text": "",
                            "language": file_lang or "ku",
                            "file_id": df.id,
                            "storage_key": key,
                            "filename": filename,
                            "duration_seconds": duration,
                        },
                        labels={
                            "dialect": file_dialect or dialect or "sorani",
                            "source": "ingest",
                            "file_id": df.id,
                            "needs_transcript": True,
                        },
                        status=AnnotationStatus.PENDING.value,
                        assignee_id=user.id,
                        comments=[{"note": "Speech file ingested — transcript pending"}],
                        revision_history=[],
                    )
                )
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
    dataset.checksum = hashlib.sha256(",".join(sorted(batch_seen | known)).encode()).hexdigest() if imported else dataset.checksum

    finished = datetime.now(timezone.utc)
    run.dataset_id = dataset.id
    run.status = "completed"
    run.finished_at = finished
    run.report = {
        "imported": imported,
        "duplicates": duplicates,
        "failed": failed,
        "unknown_rights": unknown_rights,
        "needs_review": imported,
        "total_bytes": total_bytes,
        "duration_seconds": (finished - start).total_seconds(),
        "operator": user.email,
        "language": detected_language,
        "dialect": detected_dialect,
        "dialect_votes": dialect_votes,
        "detection_confidence": detection_confidence,
        "text_files_scanned": len(text_samples),
        "media_counts": media_counts,
        "file_ids": file_ids,
        "dataset_id": dataset.id,
        "rights_status": rights_status,
    }
    db.commit()
    db.refresh(run)
    return run


def get_dataset_detail(db: Session, dataset_id: str) -> dict[str, Any]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    file_count = (
        db.query(DatasetFile)
        .filter(DatasetFile.dataset_id == dataset_id, DatasetFile.soft_deleted.is_(False))
        .count()
    )
    approved = (
        db.query(AnnotationTask)
        .filter(
            AnnotationTask.dataset_id == dataset_id,
            AnnotationTask.status == AnnotationStatus.APPROVED.value,
        )
        .count()
    )
    pending = (
        db.query(AnnotationTask)
        .filter(
            AnnotationTask.dataset_id == dataset_id,
            AnnotationTask.status.in_(
                [AnnotationStatus.PENDING.value, AnnotationStatus.IN_REVIEW.value]
            ),
        )
        .count()
    )
    rights = (
        db.query(RightsRecord)
        .filter(RightsRecord.dataset_id == dataset_id)
        .order_by(RightsRecord.created_at.desc())
        .first()
    )
    latest = (
        db.query(IngestionRun)
        .filter(IngestionRun.dataset_id == dataset_id)
        .order_by(IngestionRun.created_at.desc())
        .first()
    )
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "category": dataset.category,
        "media_type": dataset.media_type,
        "language": dataset.language,
        "dialect": dataset.dialect,
        "owner": dataset.owner,
        "status": dataset.status,
        "version": dataset.version,
        "record_count": dataset.record_count,
        "size_bytes": dataset.size_bytes,
        "checksum": dataset.checksum,
        "storage_path": dataset.storage_path,
        "ai_training_permission": dataset.ai_training_permission,
        "commercial_use": dataset.commercial_use,
        "voice_cloning_permission": dataset.voice_cloning_permission,
        "intended_model_use": dataset.intended_model_use,
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
        "file_count": file_count,
        "approved_annotations": approved,
        "pending_annotations": pending,
        "rights": (
            {
                "id": rights.id,
                "copyright_owner": rights.copyright_owner,
                "legal_status": rights.legal_status,
                "ai_training": rights.ai_training,
                "commercial_use": rights.commercial_use,
            }
            if rights
            else None
        ),
        "latest_ingestion": (
            {
                "id": latest.id,
                "status": latest.status,
                "report": latest.report,
                "created_at": latest.created_at.isoformat() if latest.created_at else None,
            }
            if latest
            else None
        ),
    }


def list_dataset_files(db: Session, dataset_id: str, limit: int = 200) -> list[dict[str, Any]]:
    if not db.get(Dataset, dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found")
    rows = (
        db.query(DatasetFile)
        .filter(DatasetFile.dataset_id == dataset_id, DatasetFile.soft_deleted.is_(False))
        .order_by(DatasetFile.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": f.id,
            "dataset_id": f.dataset_id,
            "ingestion_run_id": f.ingestion_run_id,
            "filename": f.filename,
            "storage_key": f.storage_key,
            "checksum": f.checksum,
            "content_type": f.content_type,
            "media_type": f.media_type,
            "size_bytes": f.size_bytes,
            "language": f.language,
            "dialect": f.dialect,
            "rights_status": f.rights_status,
            "duration_seconds": f.duration_seconds,
            "media_url": f"/api/media/datasets/{f.dataset_id}/files/{f.id}",
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in rows
    ]


def get_ingestion(db: Session, run_id: str) -> IngestionRun:
    run = db.get(IngestionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return run


def get_dataset_file_bytes(db: Session, dataset_id: str, file_id: str) -> tuple[bytes, str, str]:
    df = db.get(DatasetFile, file_id)
    if not df or df.dataset_id != dataset_id or df.soft_deleted:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    try:
        data, content_type = get_storage().get_object(df.storage_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail="File missing in storage") from exc
    return data, content_type or df.content_type or "application/octet-stream", df.filename


def build_training_manifest(db: Session, dataset_id: str) -> dict[str, Any]:
    detail = get_dataset_detail(db, dataset_id)
    files = list_dataset_files(db, dataset_id, limit=5000)
    approved = (
        db.query(AnnotationTask)
        .filter(
            AnnotationTask.dataset_id == dataset_id,
            AnnotationTask.status == AnnotationStatus.APPROVED.value,
        )
        .all()
    )
    return {
        "product": "Art City Data Lab",
        "kind": "training_manifest",
        "dataset": {
            "id": detail["id"],
            "name": detail["name"],
            "version": detail["version"],
            "status": detail["status"],
            "language": detail["language"],
            "dialect": detail["dialect"],
            "media_type": detail["media_type"],
            "checksum": detail["checksum"],
            "ai_training_permission": detail["ai_training_permission"],
        },
        "rights": detail["rights"],
        "file_count": detail["file_count"],
        "approved_annotation_count": len(approved),
        "pending_annotation_count": detail["pending_annotations"],
        "files": [
            {
                "id": f["id"],
                "filename": f["filename"],
                "storage_key": f["storage_key"],
                "checksum": f["checksum"],
                "media_type": f["media_type"],
                "size_bytes": f["size_bytes"],
            }
            for f in files
        ],
        "approved_annotations": [
            {
                "id": t.id,
                "media_type": t.media_type,
                "payload": t.payload,
                "labels": t.labels,
            }
            for t in approved
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ownership": "Art City owns dataset records, labels, and export manifests.",
    }


def export_dataset(
    db: Session,
    dataset_id: str,
    *,
    fmt: str = "jsonl",
    persist: bool = False,
) -> tuple[bytes, str, str]:
    if fmt not in {"jsonl", "csv"}:
        raise HTTPException(status_code=422, detail="format must be jsonl or csv")
    if not db.get(Dataset, dataset_id):
        raise HTTPException(status_code=404, detail="Dataset not found")

    tasks = (
        db.query(AnnotationTask)
        .filter(
            AnnotationTask.dataset_id == dataset_id,
            AnnotationTask.status == AnnotationStatus.APPROVED.value,
        )
        .order_by(AnnotationTask.created_at.asc())
        .all()
    )
    records = []
    for t in tasks:
        payload = t.payload or {}
        labels = t.labels or {}
        records.append(
            {
                "annotation_id": t.id,
                "dataset_id": dataset_id,
                "media_type": t.media_type,
                "text": payload.get("text"),
                "language": payload.get("language"),
                "dialect": labels.get("dialect"),
                "translation": labels.get("translation"),
                "labels": labels,
                "payload": payload,
                "file_id": payload.get("file_id") or labels.get("file_id"),
                "storage_key": payload.get("storage_key"),
                "source_job_id": labels.get("source_job_id"),
            }
        )

    if fmt == "jsonl":
        body = ("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + ("\n" if records else "")).encode(
            "utf-8"
        )
        media = "application/x-ndjson"
        filename = f"art-city-{dataset_id[:8]}-export.jsonl"
    else:
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=[
                "annotation_id",
                "dataset_id",
                "media_type",
                "text",
                "language",
                "dialect",
                "translation",
                "file_id",
                "storage_key",
                "source_job_id",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        for r in records:
            writer.writerow(r)
        body = buf.getvalue().encode("utf-8")
        media = "text/csv"
        filename = f"art-city-{dataset_id[:8]}-export.csv"

    if persist:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = f"datasets/{dataset_id}/exports/{ts}.{fmt}"
        get_storage().upload_bytes(key, body, media)

    return body, media, filename


def update_annotation_task(
    db: Session,
    *,
    task_id: str,
    user: User,
    labels: Optional[dict] = None,
    status_value: Optional[str] = None,
    comment: Optional[str] = None,
) -> AnnotationTask:
    task = db.get(AnnotationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Annotation not found")

    allowed = {s.value for s in AnnotationStatus}
    if status_value is not None and status_value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Allowed: {sorted(allowed)}",
        )
    if status_value == AnnotationStatus.REJECTED.value and not (comment or "").strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="comment is required when rejecting an annotation",
        )

    history = list(task.revision_history or [])
    history.append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "by": user.email,
            "before_labels": task.labels,
            "before_status": task.status,
        }
    )
    task.revision_history = history
    if labels is not None:
        task.labels = labels
    if status_value is not None:
        task.status = status_value
    if comment:
        comments = list(task.comments or [])
        comments.append(
            {"by": user.email, "text": comment, "at": datetime.now(timezone.utc).isoformat()}
        )
        task.comments = comments
    db.commit()
    db.refresh(task)
    return task
