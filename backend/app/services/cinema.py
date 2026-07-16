"""Art City Cinema — advertising campaign package builder with manifest + QC."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import AssetType, GenerationStatus
from app.models import Asset, CostRecord, GenerationJob
from app.services import media_factory
from app.services.providers import get_provider
from app.services.storage import get_storage
from app.services.validation import EXPORT_PRESETS, load_and_validate_package


def _upload(project_id: str, package_id: str, media: media_factory.MediaFile) -> str:
    key = f"projects/{project_id}/cinema/{package_id}/{media.filename}"
    return get_storage().upload_bytes(key, media.data, media.content_type)


def build_cinematic_package(
    db: Session,
    *,
    project_id: str,
    campaign: str,
    brief: str,
    cta: str = "Discover more",
    brand: str = "Art City",
    voiceover_script: Optional[str] = None,
    music_style: str = "epic",
    duration_seconds: float = 15.0,
    initiated_by: str = "art-city-producer",
    brand_colors: Optional[dict[str, str]] = None,
    usage_rights: str = "Art City proprietary — internal + licensed broadcast/social",
) -> dict[str, Any]:
    """
    Build a complete Art City Cinema advertising campaign:
    Hero film + social cutdowns + music + VO + end card + campaign manifest + technical QC.
    """
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc)
    package_id = str(uuid4())
    provider = get_provider("stub")
    vo_text = voiceover_script or f"{campaign}. {brief}. {cta}."
    colors = brand_colors or {
        "ink": "#05070b",
        "gold": "#c5a15e",
        "gold_bright": "#efd39a",
        "teal": "#3aa39c",
        "paper": "#f3f6fa",
    }

    deliverables: list[dict[str, Any]] = []
    generation_history: list[dict[str, Any]] = []
    total_cost = 0.0
    storage = get_storage()

    def _job(
        modality: str,
        prompt: str,
        primary: str,
        meta: dict[str, Any],
        audio: str | None = None,
    ) -> GenerationJob:
        nonlocal total_cost
        est = provider.estimate_cost(prompt, modality if modality in {"image", "video", "voice", "audio", "music"} else "video")
        prv = provider.submit(
            prompt,
            modality if modality in {"image", "video", "voice", "audio", "music"} else "video",
            "artcity-cinema-v1",
        )
        job = GenerationJob(
            project_id=project_id,
            modality=modality,
            provider=provider.name,
            model="artcity-cinema-v1",
            prompt=prompt,
            status=GenerationStatus.SUCCEEDED.value,
            result_uri=primary,
            estimated_cost=est,
            actual_cost=prv.actual_cost,
            provider_job_id=prv.provider_job_id,
        )
        db.add(job)
        db.flush()
        if prv.actual_cost:
            total_cost += float(prv.actual_cost)
            db.add(
                CostRecord(
                    project_id=project_id,
                    generation_job_id=job.id,
                    provider=provider.name,
                    model="artcity-cinema-v1",
                    amount=prv.actual_cost,
                    note=f"cinema package {package_id[:8]} · {meta.get('role')}",
                )
            )

        history = {
            "role": meta.get("role"),
            "job_id": job.id,
            "prompt": prompt,
            "prompt_version": "cinema-brief-v1",
            "provider": provider.name,
            "model": "artcity-cinema-v1",
            "provider_job_id": prv.provider_job_id,
            "estimated_cost": est,
            "actual_cost": prv.actual_cost,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "storage_path": primary,
            "audio_storage_path": audio,
        }
        generation_history.append(history)

        db.add(
            Asset(
                project_id=project_id,
                asset_type=meta.get("asset_type", AssetType.OTHER.value),
                name=meta.get("name", f"{modality}:{campaign}")[:255],
                storage_path=primary,
                metadata_json={
                    **meta,
                    "package_id": package_id,
                    "campaign": campaign,
                    "brand": brand,
                    "generation": history,
                },
            )
        )
        if audio:
            db.add(
                Asset(
                    project_id=project_id,
                    asset_type=AssetType.AUDIO.value,
                    name=f"bed:{meta.get('name', modality)}"[:255],
                    storage_path=audio,
                    metadata_json={
                        "package_id": package_id,
                        "linked_job": job.id,
                        "role": "cinema_audio_bed",
                    },
                )
            )

        file_map = {
            "broadcast_hero": "broadcast_hero.svg",
            "social_vertical": "social_vertical.svg",
            "social_square": "social_square.svg",
            "music_master": "music_master.wav",
            "voiceover": "voiceover.wav",
            "end_card": "end_card.svg",
        }
        role = meta.get("role") or ""
        entry: dict[str, Any] = {
            "type": role,
            "role": role,
            "modality": modality,
            "job_id": job.id,
            "label": meta.get("name"),
            "aspect_ratio": meta.get("aspect"),
            "aspect": meta.get("aspect"),
            "media_url": f"/api/media/{project_id}/{job.id}/primary",
            "audio_url": f"/api/media/{project_id}/{job.id}/audio" if audio else None,
            "video_file": file_map.get(role) if modality == "video" else None,
            "audio_file": f"{role}_audio_bed.wav" if audio else None,
            "file": file_map.get(role),
            "mood": music_style if role == "music_master" else None,
            "storage_path": primary,
            "generation": history,
            "export_preset": EXPORT_PRESETS.get(meta.get("aspect") or "", None),
        }
        deliverables.append(entry)
        return job

    # Brand logo asset
    logo = media_factory.make_brand_logo()
    logo_key = _upload(project_id, package_id, logo)
    db.add(
        Asset(
            project_id=project_id,
            asset_type=AssetType.IMAGE.value,
            name="Art City Logo",
            storage_path=logo_key,
            metadata_json={"package_id": package_id, "role": "brand_logo", "brand_colors": colors},
        )
    )

    for aspect, role in (("16:9", "broadcast_hero"), ("9:16", "social_vertical"), ("1:1", "social_square")):
        visual, bed = media_factory.make_cinematic_video(
            brief,
            aspect=aspect,
            duration_seconds=duration_seconds,
            brand=brand,
            campaign=campaign,
            cta=cta,
        )
        primary = _upload(project_id, package_id, visual)
        audio = _upload(project_id, package_id, bed)
        _job(
            "video",
            f"[{aspect}] {campaign}: {brief}",
            primary,
            {
                "role": role,
                "aspect": aspect,
                "name": f"{campaign} · {aspect}",
                "asset_type": AssetType.VIDEO.value,
                "preview_kind": "video_proxy",
                "duration_seconds": duration_seconds,
                "cta": cta,
                "fps": 24.0,
            },
            audio=audio,
        )

    music = media_factory.make_cinematic_music(brief, duration_seconds=duration_seconds, style=music_style)
    _job(
        "music",
        f"Music bed · {music_style} · {campaign}",
        _upload(project_id, package_id, music),
        {
            "role": "music_master",
            "name": f"{campaign} · Music",
            "asset_type": AssetType.MUSIC.value,
            "preview_kind": "audio",
            "music_style": music_style,
            "duration_seconds": duration_seconds,
        },
    )

    vo = media_factory.make_ad_voiceover(vo_text, brand=brand)
    _job(
        "voice",
        f"VO · {campaign}",
        _upload(project_id, package_id, vo),
        {
            "role": "voiceover",
            "name": f"{campaign} · Voiceover",
            "asset_type": AssetType.VOICE.value,
            "preview_kind": "audio",
            "script": vo_text,
        },
    )

    end = media_factory.make_end_card(campaign, cta, brand=brand, prompt=brief)
    _job(
        "image",
        f"End card · {campaign}",
        _upload(project_id, package_id, end),
        {
            "role": "end_card",
            "name": f"{campaign} · End card",
            "asset_type": AssetType.IMAGE.value,
            "preview_kind": "image",
            "cta": cta,
            "aspect": "16:9",
        },
    )

    # Attach audio bed bytes for validation sync checks
    jobs_by_id: dict[str, GenerationJob] = {}
    enriched: list[dict[str, Any]] = []
    for d in deliverables:
        job = db.get(GenerationJob, d["job_id"])
        if job:
            jobs_by_id[job.id] = job
        item = dict(d)
        if d.get("audio_url"):
            beds = (
                db.query(Asset)
                .filter(Asset.project_id == project_id, Asset.asset_type == AssetType.AUDIO.value)
                .order_by(Asset.created_at.desc())
                .all()
            )
            linked = next((a for a in beds if (a.metadata_json or {}).get("linked_job") == d["job_id"]), None)
            if linked and linked.storage_path:
                try:
                    item["_audio_bytes"] = storage.get_object(linked.storage_path)[0]
                except Exception:
                    pass
        enriched.append(item)

    validation = load_and_validate_package(
        storage.get_object,
        enriched,
        expected_duration=duration_seconds,
        brand=brand,
        cta=cta,
        jobs_by_id=jobs_by_id,
    )

    elapsed = round(time.perf_counter() - started, 3)
    finished_at = datetime.now(timezone.utc)

    campaign_manifest = {
        "product": "Art City Cinema",
        "campaign_id": package_id,
        "project_id": project_id,
        "campaign_name": campaign,
        "brand": brand,
        "brand_colors": colors,
        "brief": brief,
        "cta": cta,
        "voiceover_script": vo_text,
        "music_style": music_style,
        "duration_seconds": duration_seconds,
        "frame_rate_fps": 24.0,
        "export_presets": EXPORT_PRESETS,
        "initiated_by": initiated_by,
        "started_at": started_at.isoformat(),
        "completed_at": finished_at.isoformat(),
        "production_time_seconds": elapsed,
        "total_cost": total_cost,
        "currency": "USD",
        "usage_rights": usage_rights,
        "approval_status": "pending_review",
        "technical_validation_passed": validation.get("passed"),
        "deliverables": [
            {
                "type": d.get("type"),
                "aspect_ratio": d.get("aspect_ratio"),
                "video_file": d.get("video_file"),
                "audio_file": d.get("audio_file"),
                "file": d.get("file"),
                "mood": d.get("mood"),
                "storage_location": d.get("storage_path"),
                "checksum_sha256": next(
                    (
                        r["technical"].get("sha256")
                        for r in validation.get("deliverables", [])
                        if r.get("role") == d.get("role")
                    ),
                    None,
                ),
                "cost": (d.get("generation") or {}).get("actual_cost"),
                "provider": (d.get("generation") or {}).get("provider"),
                "model": (d.get("generation") or {}).get("model"),
                "prompt_version": (d.get("generation") or {}).get("prompt_version"),
                "generated_at": (d.get("generation") or {}).get("generated_at"),
            }
            for d in deliverables
        ],
        "generation_history": generation_history,
        "ownership": "Art City owns campaign package, masters, stems, prompts, and metadata.",
    }

    # Strip private validation bytes from stored deliverables
    public_deliverables = []
    for d in deliverables:
        clean = {k: v for k, v in d.items() if not k.startswith("_")}
        public_deliverables.append(clean)

    manifest_key = f"projects/{project_id}/cinema/{package_id}/CAMPAIGN_MANIFEST.json"
    storage.upload_bytes(
        manifest_key,
        json.dumps(campaign_manifest, indent=2).encode("utf-8"),
        "application/json",
    )
    validation_key = f"projects/{project_id}/cinema/{package_id}/TECHNICAL_VALIDATION.json"
    storage.upload_bytes(
        validation_key,
        json.dumps(validation, indent=2).encode("utf-8"),
        "application/json",
    )

    package_asset = Asset(
        project_id=project_id,
        asset_type=AssetType.OTHER.value,
        name=f"Art City Cinema · {campaign}"[:255],
        storage_path=manifest_key,
        metadata_json={
            "kind": "cinematic_package",
            "product": "Art City Cinema",
            "package_id": package_id,
            "campaign": campaign,
            "brief": brief,
            "cta": cta,
            "brand": brand,
            "brand_colors": colors,
            "music_style": music_style,
            "duration_seconds": duration_seconds,
            "voiceover_script": vo_text,
            "formats": ["16:9", "9:16", "1:1"],
            "deliverables": public_deliverables,
            "total_cost": total_cost,
            "production_time_seconds": elapsed,
            "initiated_by": initiated_by,
            "usage_rights": usage_rights,
            "campaign_manifest": campaign_manifest,
            "validation": validation,
            "manifest_key": manifest_key,
            "validation_key": validation_key,
            "pipeline": [
                "brief",
                "cinematic_video",
                "format_cutdowns",
                "music",
                "voiceover",
                "end_card",
                "campaign_manifest",
                "technical_validation",
                "review_ready",
            ],
        },
    )
    db.add(package_asset)
    db.commit()
    db.refresh(package_asset)

    return serialize_package(package_asset)


def serialize_package(asset: Asset) -> dict[str, Any]:
    meta = asset.metadata_json or {}
    return {
        "package_id": meta.get("package_id"),
        "asset_id": asset.id,
        "product": meta.get("product", "Art City Cinema"),
        "campaign": meta.get("campaign"),
        "brief": meta.get("brief"),
        "cta": meta.get("cta"),
        "brand": meta.get("brand"),
        "brand_colors": meta.get("brand_colors"),
        "music_style": meta.get("music_style"),
        "duration_seconds": meta.get("duration_seconds"),
        "formats": meta.get("formats", []),
        "deliverables": meta.get("deliverables", []),
        "total_cost": meta.get("total_cost", 0),
        "production_time_seconds": meta.get("production_time_seconds"),
        "initiated_by": meta.get("initiated_by"),
        "usage_rights": meta.get("usage_rights"),
        "campaign_manifest": meta.get("campaign_manifest"),
        "validation": meta.get("validation"),
        "validation_passed": (meta.get("validation") or {}).get("passed"),
        "manifest_url": f"/api/projects/{asset.project_id}/cinema/packages/{meta.get('package_id')}/manifest",
        "validation_url": f"/api/projects/{asset.project_id}/cinema/packages/{meta.get('package_id')}/validation",
        "zip_url": f"/api/projects/{asset.project_id}/cinema/packages/{meta.get('package_id')}/zip",
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }


def list_cinematic_packages(db: Session, project_id: str) -> list[dict[str, Any]]:
    assets = (
        db.query(Asset)
        .filter(Asset.project_id == project_id, Asset.soft_deleted.is_(False))
        .order_by(Asset.created_at.desc())
        .all()
    )
    return [
        serialize_package(a)
        for a in assets
        if (a.metadata_json or {}).get("kind") == "cinematic_package"
    ]


def get_cinematic_package(db: Session, project_id: str, package_id: str) -> dict[str, Any]:
    for pkg in list_cinematic_packages(db, project_id):
        if pkg.get("package_id") == package_id:
            return pkg
    raise ValueError("Cinema package not found")


def revalidate_package(db: Session, project_id: str, package_id: str) -> dict[str, Any]:
    assets = (
        db.query(Asset)
        .filter(Asset.project_id == project_id, Asset.soft_deleted.is_(False))
        .all()
    )
    package_asset = next(
        (
            a
            for a in assets
            if (a.metadata_json or {}).get("kind") == "cinematic_package"
            and (a.metadata_json or {}).get("package_id") == package_id
        ),
        None,
    )
    if not package_asset:
        raise ValueError("Cinema package not found")

    meta = dict(package_asset.metadata_json or {})
    deliverables = meta.get("deliverables") or []
    storage = get_storage()
    jobs_by_id: dict[str, GenerationJob] = {}
    enriched = []
    for d in deliverables:
        job = db.get(GenerationJob, d.get("job_id"))
        if job:
            jobs_by_id[job.id] = job
        item = dict(d)
        if d.get("audio_url"):
            beds = (
                db.query(Asset)
                .filter(Asset.project_id == project_id, Asset.asset_type == AssetType.AUDIO.value)
                .order_by(Asset.created_at.desc())
                .all()
            )
            linked = next((a for a in beds if (a.metadata_json or {}).get("linked_job") == d.get("job_id")), None)
            if linked and linked.storage_path:
                try:
                    item["_audio_bytes"] = storage.get_object(linked.storage_path)[0]
                except Exception:
                    pass
        enriched.append(item)

    validation = load_and_validate_package(
        storage.get_object,
        enriched,
        expected_duration=float(meta.get("duration_seconds") or 15),
        brand=meta.get("brand") or "Art City",
        cta=meta.get("cta") or "",
        jobs_by_id=jobs_by_id,
    )
    meta["validation"] = validation
    if meta.get("campaign_manifest"):
        meta["campaign_manifest"]["technical_validation_passed"] = validation.get("passed")
    storage.upload_bytes(
        meta.get("validation_key")
        or f"projects/{project_id}/cinema/{package_id}/TECHNICAL_VALIDATION.json",
        json.dumps(validation, indent=2).encode("utf-8"),
        "application/json",
    )
    package_asset.metadata_json = meta
    db.add(package_asset)
    db.commit()
    db.refresh(package_asset)
    return serialize_package(package_asset)
