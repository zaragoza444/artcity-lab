"""Art City Model Gateway — single entry for all AI generation."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.enums import AssetType, GenerationStatus
from app.models import Asset, CostRecord, GenerationJob
from app.services import media_factory
from app.services.providers import get_provider
from app.services.router_engine import resolve_route
from app.services.storage import get_storage


MODALITY_ASSET = {
    "image": AssetType.IMAGE,
    "video": AssetType.VIDEO,
    "voice": AssetType.VOICE,
    "audio": AssetType.AUDIO,
    "music": AssetType.MUSIC,
}


def enqueue_generation(
    db: Session,
    *,
    project_id: str,
    modality: str,
    prompt: str,
    model: Optional[str] = None,
    character_key: Optional[str] = None,
    character_name: Optional[str] = None,
    duration_seconds: float = 4.0,
    dialogue_lines: Optional[list[str]] = None,
    prefer_external: bool = False,
    requested_by: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
) -> GenerationJob:
    decision = resolve_route(
        db,
        modality=modality,
        character_key=character_key,
        model=model,
        prefer_external=prefer_external,
    )
    provider = get_provider(decision.provider)
    estimated = provider.estimate_cost(prompt, modality)

    job = GenerationJob(
        project_id=project_id,
        modality=modality,
        provider=decision.provider,
        model=decision.model_name or model,
        model_version=decision.model_version,
        registered_model_id=decision.registered_model_id,
        character_key=decision.character_key,
        requested_by=requested_by,
        prompt=prompt,
        status=GenerationStatus.QUEUED.value,
        estimated_cost=estimated,
        params_json={
            **(params or {}),
            "duration_seconds": duration_seconds,
            "dialogue_lines": dialogue_lines or [],
            "character_name": character_name,
            "route_reason": decision.reason,
        },
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Push to Redis for optional workers; always execute inline so API works
    # without a separate worker process (worker becomes optional scale-out).
    try:
        from app.services.queue import enqueue_job

        enqueue_job(job.id)
    except Exception:
        pass
    process_generation_job(db, job.id)
    db.refresh(job)
    return job


def process_generation_job(db: Session, job_id: str) -> GenerationJob:
    job = db.get(GenerationJob, job_id)
    if not job:
        raise ValueError("job not found")
    if job.status in {
        GenerationStatus.CANCELLED.value,
        GenerationStatus.SUCCEEDED.value,
        GenerationStatus.RUNNING.value,
    }:
        return job

    job.status = GenerationStatus.RUNNING.value
    db.commit()

    params = job.params_json or {}
    provider = get_provider(job.provider)
    try:
        result = provider.submit_generation(
            job.prompt or "",
            job.modality,
            job.model,
            duration_seconds=params.get("duration_seconds", 4.0),
            character_name=params.get("character_name"),
            character_key=job.character_key,
            dialogue_lines=params.get("dialogue_lines"),
        )
        job.provider_job_id = result.provider_job_id

        primary_key = _materialize_output(db, job, result, params)
        job.result_uri = primary_key
        job.actual_cost = result.actual_cost
        job.status = GenerationStatus.SUCCEEDED.value
        job.error_message = None

        db.add(
            CostRecord(
                project_id=job.project_id,
                generation_job_id=job.id,
                provider=job.provider,
                model=job.model,
                amount=float(result.actual_cost or job.estimated_cost or 0),
                note=f"gateway:{job.modality}",
            )
        )
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:  # noqa: BLE001
        job.status = GenerationStatus.FAILED.value
        job.error_message = str(exc)
        db.commit()
        db.refresh(job)
        return job


def _materialize_output(db: Session, job: GenerationJob, result, params: dict) -> str:
    storage = get_storage()
    modality = job.modality
    title = params.get("character_name") or job.character_key or modality.upper()
    prompt = job.prompt or ""
    duration = float(params.get("duration_seconds") or 4.0)
    dialogue_lines = params.get("dialogue_lines") or []

    if result.output_bytes and result.filename:
        key = f"projects/{job.project_id}/jobs/{job.id}/{result.filename}"
        storage.upload_bytes(key, result.output_bytes, result.content_type or "application/octet-stream")
        _add_asset(db, job, key, modality, prompt, title, {"provider_job_id": result.provider_job_id})
        return key

    # Stub / legacy path — synthesize via media_factory
    if modality == "image":
        media = media_factory.make_image(prompt, title=str(title))
        key = f"projects/{job.project_id}/jobs/{job.id}/{media.filename}"
        storage.upload_bytes(key, media.data, media.content_type)
        _add_asset(db, job, key, modality, prompt, title, {"preview_kind": "image"})
        return key
    if modality == "video":
        visual, bed = media_factory.make_video_proxy(prompt, duration_seconds=duration)
        key = f"projects/{job.project_id}/jobs/{job.id}/{visual.filename}"
        audio_key = f"projects/{job.project_id}/jobs/{job.id}/{bed.filename}"
        storage.upload_bytes(key, visual.data, visual.content_type)
        storage.upload_bytes(audio_key, bed.data, bed.content_type)
        _add_asset(
            db,
            job,
            key,
            modality,
            prompt,
            title,
            {"preview_kind": "video_proxy", "audio_key": audio_key},
        )
        return key
    if modality == "voice":
        if dialogue_lines:
            media = media_factory.make_voice_conversation(prompt, dialogue_lines)
        else:
            media = media_factory.make_ad_voiceover(prompt, brand=str(title))
        key = f"projects/{job.project_id}/jobs/{job.id}/{media.filename}"
        storage.upload_bytes(key, media.data, media.content_type)
        _add_asset(db, job, key, modality, prompt, title, {"preview_kind": "audio"})
        return key
    if modality == "music":
        media = media_factory.make_cinematic_music(prompt, duration_seconds=max(duration, 8.0), style="warm")
        key = f"projects/{job.project_id}/jobs/{job.id}/{media.filename}"
        storage.upload_bytes(key, media.data, media.content_type)
        _add_asset(db, job, key, modality, prompt, title, {"preview_kind": "audio"})
        return key
    media = media_factory.make_sfx(prompt)
    key = f"projects/{job.project_id}/jobs/{job.id}/{media.filename}"
    storage.upload_bytes(key, media.data, media.content_type)
    _add_asset(db, job, key, modality, prompt, title, {"preview_kind": "audio"})
    return key


def _add_asset(db: Session, job: GenerationJob, key: str, modality: str, prompt: str, title: str, meta: dict) -> None:
    db.add(
        Asset(
            project_id=job.project_id,
            asset_type=MODALITY_ASSET.get(modality, AssetType.OTHER).value,
            name=f"{title} · {modality}",
            storage_path=key,
            metadata_json={
                "prompt": prompt,
                "job_id": job.id,
                "model": job.model,
                "model_version": job.model_version,
                "provider": job.provider,
                "character_key": job.character_key,
                **meta,
            },
        )
    )


def cancel_job(db: Session, job_id: str) -> GenerationJob:
    job = db.get(GenerationJob, job_id)
    if not job:
        raise ValueError("job not found")
    if job.status in {GenerationStatus.SUCCEEDED.value, GenerationStatus.FAILED.value}:
        return job
    job.status = GenerationStatus.CANCELLED.value
    if job.provider_job_id:
        get_provider(job.provider).cancel_generation(job.provider_job_id)
    db.commit()
    db.refresh(job)
    return job


def retry_job(db: Session, job_id: str) -> GenerationJob:
    job = db.get(GenerationJob, job_id)
    if not job:
        raise ValueError("job not found")
    return enqueue_generation(
        db,
        project_id=job.project_id,
        modality=job.modality,
        prompt=job.prompt or "",
        model=job.model,
        character_key=job.character_key,
        character_name=(job.params_json or {}).get("character_name"),
        duration_seconds=float((job.params_json or {}).get("duration_seconds") or 4.0),
        dialogue_lines=(job.params_json or {}).get("dialogue_lines"),
        requested_by=job.requested_by,
        params=job.params_json,
    )
