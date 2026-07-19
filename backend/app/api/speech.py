from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import CurrentUser
from app.services.speech import build_transcript_manifest, simulate_asr

router = APIRouter(prefix="/api/v1/ai/speech", tags=["speech"])


class AsrRequest(BaseModel):
    audio_storage_key: str = Field(..., min_length=1)
    dialect: str = "sorani"


@router.post("/asr")
def run_asr(payload: AsrRequest, user: CurrentUser) -> dict:
    segments = simulate_asr(payload.audio_storage_key, dialect=payload.dialect)
    return build_transcript_manifest(segments)
