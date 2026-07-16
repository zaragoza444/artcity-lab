from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.enums import AssetType, GenerationStatus
from app.models import Asset, CostRecord, GenerationJob, Review
from app.services import media_factory
from app.services.providers import get_provider
from app.services.storage import get_storage


MODALITY_ASSET = {
    "image": AssetType.IMAGE,
    "video": AssetType.VIDEO,
    "voice": AssetType.VOICE,
    "audio": AssetType.AUDIO,
    "music": AssetType.MUSIC,
}


def _upload(project_id: str, job_id: str, media: media_factory.MediaFile) -> str:
    key = f"projects/{project_id}/jobs/{job_id}/{media.filename}"
    return get_storage().upload_bytes(key, media.data, media.content_type)


def run_studio_generation(
    db: Session,
    *,
    project_id: str,
    modality: str,
    prompt: str,
    model: Optional[str] = "artcity-local-v1",
    provider_name: str = "stub",
    duration_seconds: float = 4.0,
    dialogue_lines: Optional[list[str]] = None,
    character_name: Optional[str] = None,
) -> GenerationJob:
    provider = get_provider(provider_name)
    estimated = provider.estimate_cost(prompt, modality)
    provider_result = provider.submit(prompt, modality, model)

    job = GenerationJob(
        project_id=project_id,
        modality=modality,
        provider=provider.name,
        model=model,
        prompt=prompt,
        status=GenerationStatus.RUNNING.value,
        estimated_cost=estimated,
        provider_job_id=provider_result.provider_job_id,
    )
    db.add(job)
    db.flush()

    title = character_name or modality.upper()
    primary_key: str
    audio_key: Optional[str] = None
    meta: dict[str, Any] = {
        "title": title,
        "prompt": prompt,
        "modality": modality,
        "duration_seconds": duration_seconds,
        "local_production": True,
        "provider_job_id": provider_result.provider_job_id,
    }

    if modality == "image":
        media = media_factory.make_image(prompt, title=title)
        primary_key = _upload(project_id, job.id, media)
        meta["preview_kind"] = "image"
    elif modality == "video":
        if duration_seconds >= 8:
            visual, bed = media_factory.make_cinematic_video(
                prompt,
                aspect="16:9",
                duration_seconds=duration_seconds,
                brand="Art City",
                campaign=title,
                cta="Art City Studios",
            )
        else:
            visual, bed = media_factory.make_video_proxy(prompt, duration_seconds=duration_seconds)
        primary_key = _upload(project_id, job.id, visual)
        audio_key = _upload(project_id, job.id, bed)
        meta["preview_kind"] = "video_proxy"
        meta["audio_key"] = audio_key
        meta["cinematic"] = duration_seconds >= 8
    elif modality == "voice":
        if dialogue_lines:
            media = media_factory.make_voice_conversation(prompt, dialogue_lines)
        else:
            media = media_factory.make_ad_voiceover(prompt, brand=character_name or "Art City")
        primary_key = _upload(project_id, job.id, media)
        meta["preview_kind"] = "audio"
        meta["dialogue_lines"] = dialogue_lines or []
        if character_name:
            meta["character_name"] = character_name
    elif modality == "music":
        media = media_factory.make_cinematic_music(
            prompt, duration_seconds=max(duration_seconds, 8.0), style="warm"
        )
        primary_key = _upload(project_id, job.id, media)
        meta["preview_kind"] = "audio"
    elif modality == "audio":
        media = media_factory.make_sfx(prompt)
        primary_key = _upload(project_id, job.id, media)
        meta["preview_kind"] = "audio"
    else:
        media = media_factory.make_image(prompt, title=title)
        primary_key = _upload(project_id, job.id, media)
        meta["preview_kind"] = "image"

    job.status = GenerationStatus.SUCCEEDED.value
    job.result_uri = primary_key
    job.actual_cost = provider_result.actual_cost
    db.add(job)

    asset = Asset(
        project_id=project_id,
        asset_type=MODALITY_ASSET.get(modality, AssetType.OTHER).value,
        name=f"{modality}: {prompt[:60]}",
        storage_path=primary_key,
        metadata_json=meta,
    )
    db.add(asset)

    if audio_key:
        db.add(
            Asset(
                project_id=project_id,
                asset_type=AssetType.AUDIO.value,
                name=f"video-bed: {prompt[:50]}",
                storage_path=audio_key,
                metadata_json={"linked_job": job.id, "role": "video_audio_bed"},
            )
        )

    if job.actual_cost is not None:
        db.add(
            CostRecord(
                project_id=project_id,
                generation_job_id=job.id,
                provider=provider.name,
                model=model,
                amount=job.actual_cost,
                note=f"{modality} studio generation",
            )
        )

    db.commit()
    db.refresh(job)
    return job


def add_review(
    db: Session,
    *,
    job: GenerationJob,
    decision: str,
    notes: Optional[str] = None,
    quality_score: Optional[float] = None,
) -> Review:
    review = Review(
        generation_job_id=job.id,
        decision=decision,
        notes=notes,
        quality_score=quality_score,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
