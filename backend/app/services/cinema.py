"""Art City Cinema — advertising campaign packages via Model Gateway."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import AssetType
from app.models import Asset, GenerationJob
from app.services import media_factory
from app.services.audio_mix import mix_music_and_voice
from app.services.delivery_presets import (
    VARIANT_LABELS,
    resolve_delivery_targets,
    variant_brief,
    variant_music_style,
)
from app.services.gateway import enqueue_generation
from app.services.storage import get_storage
from app.services.timeline import apply_timeline_mix, build_timeline
from app.services.validation import EXPORT_PRESETS, load_and_validate_package
from app.services.video_mux import ffmpeg_available, mux_still_with_audio

FILE_MAP = {
    "broadcast_hero": "broadcast_hero.mp4",
    "social_vertical": "social_vertical.mp4",
    "social_square": "social_square.mp4",
    "music_master": "music_master.wav",
    "voiceover": "voiceover.wav",
    "end_card": "end_card.svg",
}

CHANNEL_PRESETS = {
    "broadcast": {"aspect": "16:9", "role": "broadcast_hero", "label": "Broadcast hero"},
    "social_vertical": {"aspect": "9:16", "role": "social_vertical", "label": "Social vertical"},
    "social_square": {"aspect": "1:1", "role": "social_square", "label": "Social square"},
}


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
    dialect: Optional[str] = "sorani",
    character_key: Optional[str] = None,
    character_name: Optional[str] = None,
    channels: Optional[list[str]] = None,
    requested_by: Optional[str] = None,
    delivery_targets: Optional[list[str]] = None,
    variants: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Full Art City Cinema advertising campaign via Model Gateway:
    hero + social cutdowns + music + VO + end card + MP4 mux + timeline + QC.
    """
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc)
    package_id = str(uuid4())
    vo_text = voiceover_script or f"{campaign}. {brief}. {cta}."
    colors = brand_colors or {
        "ink": "#05070b",
        "gold": "#c5a15e",
        "gold_bright": "#efd39a",
        "teal": "#3aa39c",
        "paper": "#f3f6fa",
    }
    selected = channels or ["broadcast", "social_vertical", "social_square"]
    variant_ids = [v.upper() for v in (variants or ["A"]) if v]
    if not variant_ids:
        variant_ids = ["A"]
    variant_ids = variant_ids[:3]
    primary_variant = variant_ids[0]
    work_brief, work_cta = variant_brief(brief, cta, primary_variant)
    work_music = variant_music_style(music_style, primary_variant)
    deliveries = resolve_delivery_targets(delivery_targets)
    deliverables: list[dict[str, Any]] = []
    generation_history: list[dict[str, Any]] = []
    total_cost = 0.0
    storage = get_storage()

    def _from_job(
        job: GenerationJob,
        *,
        role: str,
        modality: str,
        name: str,
        aspect: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        nonlocal total_cost
        cost = float(job.actual_cost or job.estimated_cost or 0)
        total_cost += cost
        audio_path = None
        if modality == "video":
            beds = (
                db.query(Asset)
                .filter(Asset.project_id == project_id, Asset.asset_type == AssetType.AUDIO.value)
                .order_by(Asset.created_at.desc())
                .all()
            )
            linked = next(
                (a for a in beds if (a.metadata_json or {}).get("linked_job") == job.id),
                None,
            )
            if linked:
                audio_path = linked.storage_path

        history = {
            "role": role,
            "job_id": job.id,
            "prompt": job.prompt,
            "prompt_version": "cinema-gateway-v1",
            "provider": job.provider,
            "model": job.model,
            "model_version": job.model_version,
            "registered_model_id": job.registered_model_id,
            "provider_job_id": job.provider_job_id,
            "estimated_cost": job.estimated_cost,
            "actual_cost": job.actual_cost,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "storage_path": job.result_uri,
            "audio_storage_path": audio_path,
            "route_reason": (job.params_json or {}).get("route_reason"),
            "knowledge_hits": (job.params_json or {}).get("knowledge_hits"),
            "dialect": (job.params_json or {}).get("dialect"),
        }
        generation_history.append(history)

        # Tag job assets for cinema package ownership
        for asset in (
            db.query(Asset)
            .filter(Asset.project_id == project_id)
            .order_by(Asset.created_at.desc())
            .limit(40)
            .all()
        ):
            meta = dict(asset.metadata_json or {})
            if meta.get("job_id") == job.id or meta.get("linked_job") == job.id:
                meta.update(
                    {
                        "package_id": package_id,
                        "campaign": campaign,
                        "brand": brand,
                        "cinema_role": role,
                        "product": "Art City Cinema",
                    }
                )
                asset.metadata_json = meta
                db.add(asset)

        entry: dict[str, Any] = {
            "type": role,
            "role": role,
            "modality": modality,
            "job_id": job.id,
            "label": name,
            "aspect_ratio": aspect,
            "aspect": aspect,
            "media_url": f"/api/media/{project_id}/{job.id}/primary",
            "audio_url": f"/api/media/{project_id}/{job.id}/audio" if audio_path else None,
            "video_file": FILE_MAP.get(role) if modality == "video" else None,
            "audio_file": f"{role}_audio_bed.wav" if audio_path else None,
            "file": FILE_MAP.get(role),
            "mood": work_music if role == "music_master" else None,
            "storage_path": job.result_uri,
            "generation": history,
            "export_preset": EXPORT_PRESETS.get(aspect or "", None),
            "channel": next((k for k, v in CHANNEL_PRESETS.items() if v["role"] == role), role),
            "variant": primary_variant,
            "is_mp4": bool(job.result_uri and str(job.result_uri).lower().endswith(".mp4")),
            **(extra or {}),
        }
        if entry["is_mp4"]:
            entry["file"] = FILE_MAP.get(role, f"{role}.mp4")
            entry["video_file"] = entry["file"]
        deliverables.append(entry)

    # Brand logo
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
    db.flush()

    # Video cutdowns via Gateway
    for channel_id in selected:
        preset = CHANNEL_PRESETS.get(channel_id)
        if not preset:
            continue
        aspect = preset["aspect"]
        role = preset["role"]
        prompt = (
            f"[{aspect} Art City advertising {role}] Campaign: {campaign}. "
            f"Brief: {work_brief}. CTA: {work_cta}. Brand: {brand}. "
            f"Variant {primary_variant}. Cinematic commercial for broadcast and social."
        )
        job = enqueue_generation(
            db,
            project_id=project_id,
            modality="video",
            prompt=prompt,
            character_key=character_key,
            character_name=character_name or campaign,
            duration_seconds=duration_seconds,
            requested_by=requested_by,
            params={
                "dialect": dialect,
                "aspect": aspect,
                "campaign": campaign,
                "cta": work_cta,
                "brand": brand,
                "cinema_role": role,
                "package_id": package_id,
                "music_style": work_music,
                "advertising": True,
                "variant": primary_variant,
                "lora_key": character_key,
            },
        )
        if job.status != "succeeded":
            raise ValueError(f"Cinema video failed for {role}: {job.error_message or job.status}")
        _from_job(job, role=role, modality="video", name=f"{campaign} · {aspect}", aspect=aspect)

    # Music master
    music_job = enqueue_generation(
        db,
        project_id=project_id,
        modality="music",
        prompt=f"Advertising music bed · {work_music} · {campaign}. {work_brief}",
        duration_seconds=duration_seconds,
        requested_by=requested_by,
        params={
            "dialect": dialect,
            "music_style": work_music,
            "campaign": campaign,
            "cinema_role": "music_master",
            "package_id": package_id,
            "advertising": True,
            "variant": primary_variant,
        },
    )
    if music_job.status != "succeeded":
        raise ValueError(f"Cinema music failed: {music_job.error_message or music_job.status}")
    _from_job(
        music_job,
        role="music_master",
        modality="music",
        name=f"{campaign} · Music",
        extra={"music_style": work_music},
    )

    # Voice-over
    vo_job = enqueue_generation(
        db,
        project_id=project_id,
        modality="voice",
        prompt=f"Advertising voice-over · {campaign}. Script: {vo_text}",
        character_key=character_key,
        character_name=character_name or brand,
        duration_seconds=min(duration_seconds, 30.0),
        requested_by=requested_by,
        params={
            "dialect": dialect,
            "campaign": campaign,
            "brand": brand,
            "cinema_role": "voiceover",
            "package_id": package_id,
            "script": vo_text,
            "advertising": True,
            "variant": primary_variant,
            "lora_key": character_key,
        },
    )
    if vo_job.status != "succeeded":
        raise ValueError(f"Cinema voice failed: {vo_job.error_message or vo_job.status}")
    vo_transcript: dict[str, Any] | None = None
    if vo_job.result_uri:
        try:
            from app.services.speech import run_asr_job

            vo_transcript = run_asr_job(
                db,
                audio_storage_key=vo_job.result_uri,
                dialect=dialect or "sorani",
                project_id=project_id,
                requested_by=requested_by,
                create_annotation=True,
            )
        except Exception:
            vo_transcript = None
    _from_job(
        vo_job,
        role="voiceover",
        modality="voice",
        name=f"{campaign} · Voiceover",
        extra={
            "script": vo_text,
            "transcript": vo_transcript,
            "transcript_job_id": (vo_transcript or {}).get("job_id"),
            "subtitle_vtt": (vo_transcript or {}).get("media_urls", {}).get("vtt"),
            "subtitle_srt": (vo_transcript or {}).get("media_urls", {}).get("srt"),
        },
    )

    # End card
    end_job = enqueue_generation(
        db,
        project_id=project_id,
        modality="image",
        prompt=(
            f"Advertising end card for {campaign}. Brand {brand}. CTA: {work_cta}. "
            f"Brief mood: {work_brief}. Clean Art City title card."
        ),
        character_key=character_key,
        character_name=character_name,
        requested_by=requested_by,
        params={
            "dialect": dialect,
            "campaign": campaign,
            "cta": work_cta,
            "brand": brand,
            "cinema_role": "end_card",
            "package_id": package_id,
            "aspect": "16:9",
            "advertising": True,
            "end_card": True,
            "variant": primary_variant,
            "lora_key": character_key,
        },
    )
    if end_job.status != "succeeded":
        raise ValueError(f"Cinema end card failed: {end_job.error_message or end_job.status}")
    _from_job(
        end_job,
        role="end_card",
        modality="image",
        name=f"{campaign} · End card",
        aspect="16:9",
        extra={"cta": work_cta},
    )

    # Alternate A/B/C stems (music + end card) when multiple variants requested
    variant_pack: list[dict[str, Any]] = [
        {
            "id": primary_variant,
            "label": VARIANT_LABELS.get(primary_variant, primary_variant),
            "brief": work_brief,
            "cta": work_cta,
            "music_style": work_music,
            "primary": True,
        }
    ]
    for vid in variant_ids[1:]:
        v_brief, v_cta = variant_brief(brief, cta, vid)
        v_music = variant_music_style(music_style, vid)
        v_music_job = enqueue_generation(
            db,
            project_id=project_id,
            modality="music",
            prompt=f"Variant {vid} music · {v_music} · {campaign}. {v_brief}",
            duration_seconds=duration_seconds,
            requested_by=requested_by,
            params={
                "music_style": v_music,
                "campaign": campaign,
                "cinema_role": f"music_master_{vid}",
                "package_id": package_id,
                "advertising": True,
                "variant": vid,
            },
        )
        v_end = enqueue_generation(
            db,
            project_id=project_id,
            modality="image",
            prompt=f"Variant {vid} end card · {campaign} · CTA {v_cta}. {v_brief}",
            character_key=character_key,
            requested_by=requested_by,
            params={
                "campaign": campaign,
                "cta": v_cta,
                "brand": brand,
                "cinema_role": f"end_card_{vid}",
                "package_id": package_id,
                "advertising": True,
                "end_card": True,
                "variant": vid,
            },
        )
        variant_pack.append(
            {
                "id": vid,
                "label": VARIANT_LABELS.get(vid, vid),
                "brief": v_brief,
                "cta": v_cta,
                "music_style": v_music,
                "primary": False,
                "music_job_id": v_music_job.id if v_music_job.status == "succeeded" else None,
                "end_card_job_id": v_end.id if v_end.status == "succeeded" else None,
            }
        )
        if v_music_job.status == "succeeded":
            total_cost += float(v_music_job.actual_cost or v_music_job.estimated_cost or 0)
        if v_end.status == "succeeded":
            total_cost += float(v_end.actual_cost or v_end.estimated_cost or 0)

    # Finishing: duck music under VO, remux channel MP4s with mixed stem when ffmpeg available
    mix_key = None
    if music_job.result_uri and vo_job.result_uri and ffmpeg_available():
        try:
            music_bytes = storage.get_object(music_job.result_uri)[0]
            vo_bytes = storage.get_object(vo_job.result_uri)[0]
            mix = mix_music_and_voice(
                music_bytes,
                vo_bytes,
                duration_seconds=duration_seconds,
                filename="mix_master.wav",
            )
            mix_key = f"projects/{project_id}/cinema/{package_id}/{mix.filename}"
            storage.upload_bytes(mix_key, mix.data, mix.content_type)
            db.add(
                Asset(
                    project_id=project_id,
                    asset_type=AssetType.AUDIO.value,
                    name=f"{campaign} · Mix master",
                    storage_path=mix_key,
                    metadata_json={
                        "package_id": package_id,
                        "role": "mix_master",
                        "cinema_role": "mix_master",
                    },
                )
            )
            for d in deliverables:
                if d.get("modality") != "video":
                    continue
                aspect = d.get("aspect") or "16:9"
                w, h = media_factory.ASPECT_SIZES.get(aspect, media_factory.ASPECT_SIZES["16:9"])
                poster = media_factory.make_cinema_poster_png(
                    campaign=campaign,
                    brief=work_brief,
                    cta=work_cta,
                    brand=brand,
                    aspect=aspect,
                    filename=f"{d['role']}_poster.png",
                )
                mp4 = mux_still_with_audio(
                    poster_png=poster.data,
                    audio_wav=mix.data,
                    duration_seconds=duration_seconds,
                    filename=FILE_MAP.get(d["role"], f"{d['role']}.mp4"),
                    width=w,
                    height=h,
                )
                if not mp4:
                    continue
                mp4_key = f"projects/{project_id}/cinema/{package_id}/{mp4.filename}"
                storage.upload_bytes(mp4_key, mp4.data, mp4.content_type)
                job = db.get(GenerationJob, d["job_id"])
                if job:
                    job.result_uri = mp4_key
                    db.add(job)
                d["storage_path"] = mp4_key
                d["is_mp4"] = True
                d["file"] = mp4.filename
                d["video_file"] = mp4.filename
                d["mp4_url"] = f"/api/media/{project_id}/{d['job_id']}/primary"
                d["mix_audio_path"] = mix_key
                db.add(
                    Asset(
                        project_id=project_id,
                        asset_type=AssetType.VIDEO.value,
                        name=f"{campaign} · {d['role']} MP4",
                        storage_path=mp4_key,
                        metadata_json={
                            "package_id": package_id,
                            "job_id": d["job_id"],
                            "cinema_role": d["role"],
                            "kind": "mp4_master",
                        },
                    )
                )
            db.flush()
        except Exception:
            mix_key = None

    timeline = build_timeline(
        duration_seconds=duration_seconds,
        deliverables=deliverables,
        duck_music_under_vo=True,
    )

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
        cta=work_cta,
        jobs_by_id=jobs_by_id,
        channels=selected,
    )

    elapsed = round(time.perf_counter() - started, 3)
    finished_at = datetime.now(timezone.utc)

    campaign_manifest = {
        "product": "Art City Cinema",
        "kind": "advertising_campaign",
        "campaign_id": package_id,
        "project_id": project_id,
        "campaign_name": campaign,
        "brand": brand,
        "brand_colors": colors,
        "brief": brief,
        "brief_variant": work_brief,
        "cta": cta,
        "cta_variant": work_cta,
        "voiceover_script": vo_text,
        "voiceover_transcript": vo_transcript,
        "music_style": work_music,
        "dialect": dialect,
        "character_key": character_key,
        "lora_key": character_key,
        "channels": selected,
        "delivery_targets": deliveries,
        "variants": variant_pack,
        "timeline": timeline,
        "mix_master_path": mix_key,
        "mp4_mux": ffmpeg_available(),
        "duration_seconds": duration_seconds,
        "frame_rate_fps": 24.0,
        "export_presets": EXPORT_PRESETS,
        "gateway": "Art City Model Gateway",
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
                "channel": d.get("channel"),
                "aspect_ratio": d.get("aspect_ratio"),
                "video_file": d.get("video_file"),
                "audio_file": d.get("audio_file"),
                "file": d.get("file"),
                "is_mp4": d.get("is_mp4"),
                "mp4_url": d.get("mp4_url"),
                "mood": d.get("mood"),
                "variant": d.get("variant"),
                "storage_location": d.get("storage_path"),
                "job_id": d.get("job_id"),
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

    public_deliverables = [{k: v for k, v in d.items() if not k.startswith("_")} for d in deliverables]

    manifest_key = f"projects/{project_id}/cinema/{package_id}/CAMPAIGN_MANIFEST.json"
    storage.upload_bytes(manifest_key, json.dumps(campaign_manifest, indent=2).encode("utf-8"), "application/json")
    validation_key = f"projects/{project_id}/cinema/{package_id}/TECHNICAL_VALIDATION.json"
    storage.upload_bytes(validation_key, json.dumps(validation, indent=2).encode("utf-8"), "application/json")

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
            "music_style": work_music,
            "dialect": dialect,
            "character_key": character_key,
            "channels": selected,
            "delivery_targets": deliveries,
            "variants": variant_pack,
            "timeline": timeline,
            "mix_master_path": mix_key,
            "duration_seconds": duration_seconds,
            "voiceover_script": vo_text,
            "voiceover_transcript": vo_transcript,
            "formats": [CHANNEL_PRESETS[c]["aspect"] for c in selected if c in CHANNEL_PRESETS],
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
                "model_gateway",
                "advertising_video_cutdowns",
                "music",
                "voiceover",
                "end_card",
                "variants",
                "mix_and_mp4_mux",
                "finishing_timeline",
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
        "dialect": meta.get("dialect"),
        "character_key": meta.get("character_key"),
        "channels": meta.get("channels", []),
        "delivery_targets": meta.get("delivery_targets", []),
        "variants": meta.get("variants", []),
        "timeline": meta.get("timeline"),
        "mix_master_path": meta.get("mix_master_path"),
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


def update_package_timeline(
    db: Session,
    project_id: str,
    package_id: str,
    mix: dict[str, Any],
) -> dict[str, Any]:
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
    timeline = apply_timeline_mix(meta.get("timeline") or {}, mix)
    meta["timeline"] = timeline
    if meta.get("campaign_manifest"):
        meta["campaign_manifest"] = dict(meta["campaign_manifest"])
        meta["campaign_manifest"]["timeline"] = timeline
        storage = get_storage()
        storage.upload_bytes(
            meta.get("manifest_key")
            or f"projects/{project_id}/cinema/{package_id}/CAMPAIGN_MANIFEST.json",
            json.dumps(meta["campaign_manifest"], indent=2).encode("utf-8"),
            "application/json",
        )
    package_asset.metadata_json = meta
    db.add(package_asset)
    db.commit()
    db.refresh(package_asset)
    return serialize_package(package_asset)


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
        channels=list(meta.get("channels") or []),
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
