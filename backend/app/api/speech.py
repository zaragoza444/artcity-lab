from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import CurrentUser
from app.services.speech import (
    SUPPORTED_DIALECTS,
    detect_language_dialect,
    get_asr_job,
    get_job_subtitle_bytes,
    get_job_transcript_bytes,
    normalize_dialect,
    run_asr,
    run_asr_job,
    segments_to_srt,
    segments_to_vtt,
    upload_speech_audio,
)

router = APIRouter(prefix="/api/v1/ai/speech", tags=["speech"])


class AsrRequest(BaseModel):
    audio_storage_key: str = Field(..., min_length=1)
    dialect: str = "sorani"
    duration_hint: float | None = Field(default=None, ge=1.0, le=600.0)
    project_id: Optional[str] = None
    create_annotation: bool = True

    @field_validator("dialect", mode="before")
    @classmethod
    def coerce_dialect(cls, v: object) -> object:
        if isinstance(v, str):
            return normalize_dialect(v)
        return v


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


class SubtitleRequest(BaseModel):
    audio_storage_key: str = Field(..., min_length=1)
    dialect: str = "sorani"
    format: str = Field(default="vtt", pattern="^(vtt|srt)$")


@router.get("/dialects")
def list_dialects(user: CurrentUser) -> dict:
    settings = get_settings()
    return {
        "language": "ku",
        "dialects": [
            {"id": "sorani", "label": "Central Kurdish (Sorani)", "script": "arabic"},
            {"id": "badini", "label": "Badini / Behdini", "script": "arabic"},
            {"id": "kurmanji", "label": "Northern Kurdish (Kurmanji)", "script": "latin"},
        ],
        "model": settings.asr_model_name,
        "engine": settings.asr_engine,
        "supported": list(SUPPORTED_DIALECTS),
    }


@router.post("/detect")
def detect_text(payload: DetectRequest, user: CurrentUser) -> dict:
    return detect_language_dialect(payload.text)


@router.post("/upload")
async def upload_audio(
    user: CurrentUser,
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> dict:
    data = await file.read()
    return upload_speech_audio(
        db,
        data=data,
        filename=file.filename or f"upload-{uuid4().hex[:8]}.wav",
        content_type=file.content_type or "audio/wav",
        project_id=project_id,
        requested_by=user.id,
    )


@router.post("/asr")
def asr(payload: AsrRequest, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    return run_asr_job(
        db,
        audio_storage_key=payload.audio_storage_key,
        dialect=payload.dialect,
        duration_hint=payload.duration_hint,
        project_id=payload.project_id,
        requested_by=user.id,
        create_annotation=payload.create_annotation,
    )


@router.get("/jobs/{job_id}")
def speech_job(job_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    return get_asr_job(db, job_id)


@router.get("/jobs/{job_id}/transcript")
def speech_transcript(job_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> Response:
    data = get_job_transcript_bytes(db, job_id)
    return Response(content=data, media_type="application/json")


@router.get("/jobs/{job_id}/subtitles")
def speech_job_subtitles(
    job_id: str,
    user: CurrentUser,
    format: str = Query(default="vtt", pattern="^(vtt|srt)$"),
    db: Session = Depends(get_db),
) -> Response:
    data, media, filename = get_job_subtitle_bytes(db, job_id, fmt=format)
    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/subtitles")
def subtitles(payload: SubtitleRequest, user: CurrentUser) -> Response:
    """Generate subtitles from an existing audio key (runs engine; does not persist job)."""
    dialect = normalize_dialect(payload.dialect)
    segments = run_asr(payload.audio_storage_key, dialect=dialect)
    if payload.format == "srt":
        body = segments_to_srt(segments)
        media = "application/x-subrip"
        filename = f"art-city-{dialect}.srt"
    else:
        body = segments_to_vtt(segments)
        media = "text/vtt"
        filename = f"art-city-{dialect}.vtt"
    return Response(
        content=body.encode("utf-8"),
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
