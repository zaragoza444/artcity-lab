from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field, field_validator

from app.core.deps import CurrentUser
from app.services.speech import (
    SUPPORTED_DIALECTS,
    build_transcript_manifest,
    detect_language_dialect,
    normalize_dialect,
    run_asr,
    segments_to_srt,
    segments_to_vtt,
)

router = APIRouter(prefix="/api/v1/ai/speech", tags=["speech"])


class AsrRequest(BaseModel):
    audio_storage_key: str = Field(..., min_length=1)
    dialect: str = "sorani"
    duration_hint: float | None = Field(default=None, ge=1.0, le=600.0)

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
    return {
        "language": "ku",
        "dialects": [
            {"id": "sorani", "label": "Central Kurdish (Sorani)", "script": "arabic"},
            {"id": "badini", "label": "Badini / Behdini", "script": "arabic"},
            {"id": "kurmanji", "label": "Northern Kurdish (Kurmanji)", "script": "latin"},
        ],
        "model": "AC-KURDISH-ASR-v1",
        "supported": list(SUPPORTED_DIALECTS),
    }


@router.post("/detect")
def detect_text(payload: DetectRequest, user: CurrentUser) -> dict:
    return detect_language_dialect(payload.text)


@router.post("/asr")
def asr(payload: AsrRequest, user: CurrentUser) -> dict:
    segments = run_asr(
        payload.audio_storage_key,
        dialect=payload.dialect,
        duration_hint=payload.duration_hint,
    )
    return build_transcript_manifest(segments, dialect=payload.dialect)


@router.post("/subtitles")
def subtitles(payload: SubtitleRequest, user: CurrentUser) -> Response:
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
