"""Art City Kurdish speech — production ASR pipeline (MinIO + pluggable engine)."""

from __future__ import annotations

import hashlib
import io
import json
import re
import wave
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import AnnotationStatus, AssetType, GenerationStatus
from app.models import AnnotationTask, Asset, CostRecord, GenerationJob, Project
from app.services.asr_engine import (
    SUPPORTED_DIALECTS,
    TranscriptSegment,
    normalize_dialect,
    resolve_asr_engine,
)
from app.services.storage import get_storage

_LATIN_HINTS = {
    "kurmanji": ("silav", "çîrok", "çiyan", "vegeri", "malê", "hûn"),
    "badini": ("slav", "behêr", "çiyayan"),
    "sorani": ("slaw", "chîrok", "kardokh", "kurdiya", "newroz", "zagros"),
}


def detect_language_dialect(text: str) -> dict:
    """Heuristic language/dialect detection for ingest and prompt prep."""
    sample = (text or "").strip()
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", sample))
    latin = len(re.findall(r"[A-Za-z]", sample))
    lower = sample.lower()

    scores = {d: 0.0 for d in SUPPORTED_DIALECTS}
    for dialect, hints in _LATIN_HINTS.items():
        for h in hints:
            if h in lower:
                scores[dialect] += 1.5
    if arabic_chars > latin:
        scores["sorani"] += 2.0
        scores["badini"] += 1.0
    elif latin > 0:
        scores["kurmanji"] += 1.5

    dialect = max(scores, key=scores.get)
    confidence = min(0.95, 0.45 + scores[dialect] * 0.12)
    return {
        "language": "ku",
        "dialect": dialect,
        "script": "arabic" if arabic_chars >= latin else "latin",
        "confidence": round(confidence, 3),
        "supported_dialects": list(SUPPORTED_DIALECTS),
    }


def wav_duration_seconds(audio_bytes: bytes) -> float | None:
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate() or 1
            return round(frames / float(rate), 3)
    except Exception:  # noqa: BLE001
        return None


def load_audio_bytes(audio_storage_key: str) -> tuple[bytes, str]:
    key = (audio_storage_key or "").strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="audio_storage_key is required",
        )
    storage = get_storage()
    if not storage.object_exists(key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio object not found: {key}",
        )
    data, content_type = storage.get_object(key)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio object is empty",
        )
    return data, content_type


def run_asr(
    audio_key: str,
    dialect: str = "sorani",
    *,
    duration_hint: float | None = None,
    audio_bytes: bytes | None = None,
) -> list[TranscriptSegment]:
    """Transcribe audio via the configured ASR engine (requires real MinIO object)."""
    if audio_bytes is None:
        audio_bytes, _ = load_audio_bytes(audio_key)
    duration = duration_hint or wav_duration_seconds(audio_bytes)
    engine = resolve_asr_engine()
    result = engine.transcribe(
        audio_bytes,
        dialect=dialect,
        audio_key=audio_key,
        duration_hint=duration,
    )
    return result.segments


def simulate_asr(audio_key: str, dialect: str = "sorani") -> list[TranscriptSegment]:
    return run_asr(audio_key, dialect=dialect)


def build_transcript_manifest(
    segments: list[TranscriptSegment],
    *,
    dialect: str | None = None,
    engine_name: str | None = None,
    model: str | None = None,
    status_label: str | None = None,
    audio_key: str | None = None,
    audio_bytes: bytes | None = None,
    job_id: str | None = None,
    media_urls: dict[str, str] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    dialect = normalize_dialect(dialect or (segments[0].dialect if segments else "sorani"))
    avg = sum(s.confidence for s in segments) / len(segments) if segments else 0.0
    checksum = hashlib.sha256(audio_bytes).hexdigest() if audio_bytes else None
    return {
        "engine": engine_name or resolve_asr_engine().name,
        "model": model or settings.asr_model_name,
        "status": status_label or "pilot",
        "language": "ku",
        "dialect": dialect,
        "supported_dialects": list(SUPPORTED_DIALECTS),
        "average_confidence": round(avg, 3),
        "segment_count": len(segments),
        "audio_storage_key": audio_key,
        "audio_sha256": checksum,
        "audio_bytes": len(audio_bytes) if audio_bytes else None,
        "duration_seconds": wav_duration_seconds(audio_bytes) if audio_bytes else None,
        "job_id": job_id,
        "media_urls": media_urls or {},
        "segments": [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text,
                "speaker": s.speaker,
                "dialect": s.dialect,
                "language": s.language,
                "confidence": s.confidence,
            }
            for s in segments
        ],
    }


def segments_to_vtt(segments: list[TranscriptSegment]) -> str:
    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{ts(seg.start)} --> {ts(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    return "\n".join(lines)


def segments_to_srt(segments: list[TranscriptSegment]) -> str:
    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{ts(seg.start)} --> {ts(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    return "\n".join(lines)


def _ensure_speech_project(db: Session, project_id: str | None) -> Project:
    if project_id:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    project = (
        db.query(Project)
        .filter(Project.name == "Art City Speech Lab")
        .order_by(Project.created_at.desc())
        .first()
    )
    if project:
        return project
    project = Project(
        name="Art City Speech Lab",
        description="Default project for Kurdish ASR uploads and transcript jobs",
        status="active",
    )
    db.add(project)
    db.flush()
    return project


def upload_speech_audio(
    db: Session,
    *,
    data: bytes,
    filename: str,
    content_type: str,
    project_id: str | None = None,
    requested_by: str | None = None,
) -> dict[str, Any]:
    if not data:
        raise HTTPException(status_code=422, detail="Empty audio upload")
    project = _ensure_speech_project(db, project_id)
    digest = hashlib.sha256(data).hexdigest()
    safe_name = (filename or "audio.wav").replace("/", "_").replace("\\", "_")
    key = f"projects/{project.id}/speech/uploads/{digest[:16]}_{safe_name}"
    get_storage().upload_bytes(key, data, content_type or "audio/wav")
    asset = Asset(
        project_id=project.id,
        asset_type=AssetType.AUDIO.value,
        name=f"speech upload · {safe_name}"[:255],
        storage_path=key,
        checksum=digest,
        metadata_json={
            "role": "speech_upload",
            "filename": safe_name,
            "uploaded_by": requested_by,
            "duration_seconds": wav_duration_seconds(data),
        },
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {
        "audio_storage_key": key,
        "project_id": project.id,
        "asset_id": asset.id,
        "checksum": digest,
        "bytes": len(data),
        "duration_seconds": wav_duration_seconds(data),
        "content_type": content_type or "audio/wav",
    }


def run_asr_job(
    db: Session,
    *,
    audio_storage_key: str,
    dialect: str = "sorani",
    duration_hint: float | None = None,
    project_id: str | None = None,
    requested_by: str | None = None,
    dataset_id: str | None = None,
    create_annotation: bool = True,
) -> dict[str, Any]:
    """Full production ASR: load audio, transcribe, persist job + transcript/VTT/SRT."""
    settings = get_settings()
    dialect = normalize_dialect(dialect)
    audio_bytes, content_type = load_audio_bytes(audio_storage_key)
    duration = duration_hint or wav_duration_seconds(audio_bytes)

    project = _ensure_speech_project(db, project_id)
    engine = resolve_asr_engine()
    engine_result = engine.transcribe(
        audio_bytes,
        dialect=dialect,
        audio_key=audio_storage_key,
        duration_hint=duration,
    )
    segments = engine_result.segments

    job = GenerationJob(
        id=str(uuid4()),
        project_id=project.id,
        modality="speech",
        provider="artcity-asr",
        model=engine_result.model or settings.asr_model_name,
        model_version="v1",
        prompt=f"ASR {dialect} · {audio_storage_key}",
        status=GenerationStatus.RUNNING.value,
        estimated_cost=0.02,
        params_json={
            "dialect": dialect,
            "audio_storage_key": audio_storage_key,
            "engine": engine_result.engine_name,
            "content_type": content_type,
        },
        requested_by=requested_by,
        dataset_id=dataset_id,
    )
    db.add(job)
    db.flush()

    vtt = segments_to_vtt(segments)
    srt = segments_to_srt(segments)
    root = f"projects/{project.id}/speech/{job.id}"
    transcript_key = f"{root}/transcript.json"
    vtt_key = f"{root}/transcript.vtt"
    srt_key = f"{root}/transcript.srt"
    storage = get_storage()

    media_urls = {
        "transcript": f"/api/v1/ai/speech/jobs/{job.id}/transcript",
        "vtt": f"/api/v1/ai/speech/jobs/{job.id}/subtitles?format=vtt",
        "srt": f"/api/v1/ai/speech/jobs/{job.id}/subtitles?format=srt",
    }
    manifest = build_transcript_manifest(
        segments,
        dialect=dialect,
        engine_name=engine_result.engine_name,
        model=engine_result.model,
        status_label=engine_result.status,
        audio_key=audio_storage_key,
        audio_bytes=audio_bytes,
        job_id=job.id,
        media_urls=media_urls,
    )

    storage.upload_bytes(
        transcript_key,
        json.dumps(manifest, indent=2).encode("utf-8"),
        "application/json",
    )
    storage.upload_bytes(vtt_key, vtt.encode("utf-8"), "text/vtt")
    storage.upload_bytes(srt_key, srt.encode("utf-8"), "application/x-subrip")

    job.status = GenerationStatus.SUCCEEDED.value
    job.result_uri = transcript_key
    job.actual_cost = 0.02
    job.provider_job_id = f"asr-{job.id[:8]}"
    job.params_json = {
        **(job.params_json or {}),
        "manifest": manifest,
        "vtt_key": vtt_key,
        "srt_key": srt_key,
        "transcript_key": transcript_key,
    }
    db.add(job)

    db.add(
        Asset(
            project_id=project.id,
            asset_type=AssetType.SUBTITLE.value,
            name=f"ASR transcript · {dialect}"[:255],
            storage_path=transcript_key,
            checksum=manifest.get("audio_sha256"),
            metadata_json={
                "job_id": job.id,
                "role": "asr_transcript",
                "dialect": dialect,
                "model": job.model,
                "engine": engine_result.engine_name,
                "vtt_key": vtt_key,
                "srt_key": srt_key,
                "audio_storage_key": audio_storage_key,
            },
        )
    )
    db.add(
        CostRecord(
            project_id=project.id,
            generation_job_id=job.id,
            provider="artcity-asr",
            model=job.model,
            amount=0.02,
            note=f"asr:{dialect}",
        )
    )

    if create_annotation:
        db.add(
            AnnotationTask(
                dataset_id=dataset_id or _speech_dataset_id(db),
                media_type="speech",
                payload={
                    "text": " ".join(s.text for s in segments),
                    "segments": manifest["segments"],
                    "audio_storage_key": audio_storage_key,
                    "language": "ku",
                },
                labels={
                    "dialect": dialect,
                    "source_job_id": job.id,
                    "model": job.model,
                    "engine": engine_result.engine_name,
                },
                status=AnnotationStatus.PENDING.value,
                assignee_id=requested_by,
                comments=[{"note": "Auto-created from Art City ASR"}],
                revision_history=[],
            )
        )

    db.commit()
    db.refresh(job)
    return {
        "job_id": job.id,
        "project_id": project.id,
        "status": job.status,
        "model": job.model,
        "provider": job.provider,
        "result_uri": job.result_uri,
        **manifest,
    }


def _speech_dataset_id(db: Session) -> str:
    from app.models import Dataset

    ds = db.query(Dataset).filter(Dataset.name == "KD-SPEECH-KU-v1").first()
    if ds:
        return ds.id
    # Fallback ephemeral dataset row if seed missing
    ds = Dataset(
        name="KD-SPEECH-KU-v1",
        description="Kurdish speech corpus scaffold",
        category="speech",
        media_type="audio",
        language="ku",
        dialect="sorani",
        owner="Art City",
        status="evaluation_only",
        version="v1",
        record_count=0,
    )
    db.add(ds)
    db.flush()
    return ds.id


def get_asr_job(db: Session, job_id: str) -> dict[str, Any]:
    job = db.get(GenerationJob, job_id)
    if not job or job.modality != "speech":
        raise HTTPException(status_code=404, detail="ASR job not found")
    params = job.params_json or {}
    manifest = params.get("manifest")
    if not manifest and job.result_uri:
        try:
            data, _ = get_storage().get_object(job.result_uri)
            manifest = json.loads(data.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=404, detail="Transcript missing in storage") from exc
    return {
        "job_id": job.id,
        "project_id": job.project_id,
        "status": job.status,
        "model": job.model,
        "provider": job.provider,
        "result_uri": job.result_uri,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        **(manifest or {}),
    }


def get_job_subtitle_bytes(db: Session, job_id: str, fmt: str = "vtt") -> tuple[bytes, str, str]:
    job = db.get(GenerationJob, job_id)
    if not job or job.modality != "speech":
        raise HTTPException(status_code=404, detail="ASR job not found")
    params = job.params_json or {}
    if fmt == "srt":
        key = params.get("srt_key")
        media = "application/x-subrip"
        filename = f"art-city-{job_id[:8]}.srt"
    else:
        key = params.get("vtt_key")
        media = "text/vtt"
        filename = f"art-city-{job_id[:8]}.vtt"
    if not key:
        raise HTTPException(status_code=404, detail="Subtitle missing")
    data, _ = get_storage().get_object(key)
    return data, media, filename


def get_job_transcript_bytes(db: Session, job_id: str) -> bytes:
    job = db.get(GenerationJob, job_id)
    if not job or job.modality != "speech" or not job.result_uri:
        raise HTTPException(status_code=404, detail="ASR job not found")
    data, _ = get_storage().get_object(job.result_uri)
    return data
