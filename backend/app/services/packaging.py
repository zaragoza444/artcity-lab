"""Build downloadable Art City Cinema ZIP packages (masters + manifest + report)."""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any

from sqlalchemy.orm import Session

from app.models import Asset, GenerationJob
from app.services.cinema import list_cinematic_packages
from app.services.storage import get_storage


CANONICAL_NAMES = {
    "broadcast_hero": ("broadcast_hero.mp4", "broadcast_hero_audio_bed.wav"),
    "social_vertical": ("social_vertical.mp4", "social_vertical_audio_bed.wav"),
    "social_square": ("social_square.mp4", "social_square_audio_bed.wav"),
    "music_master": ("music_master.wav", None),
    "voiceover": ("voiceover.wav", None),
    "end_card": ("end_card.png", None),
}


def build_campaign_zip(db: Session, project_id: str, package_id: str) -> bytes:
    packages = list_cinematic_packages(db, project_id)
    package = next((p for p in packages if p.get("package_id") == package_id), None)
    if not package:
        raise ValueError("Cinema package not found")

    storage = get_storage()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Campaign manifest
        manifest = package.get("campaign_manifest") or {}
        zf.writestr(
            "CAMPAIGN_MANIFEST.json",
            json.dumps(manifest, indent=2),
        )
        # Technical validation
        validation = package.get("validation") or {}
        zf.writestr(
            "TECHNICAL_VALIDATION.json",
            json.dumps(validation, indent=2),
        )

        for d in package.get("deliverables") or []:
            role = d.get("role")
            names = CANONICAL_NAMES.get(role or "", (f"{role}.bin", None))
            job = db.get(GenerationJob, d.get("job_id"))
            if not job or not job.result_uri:
                continue
            data, ctype = storage.get_object(job.result_uri)
            out_name = names[0]
            # Keep extension honest when still shipping SVG proxy (no ffmpeg)
            if out_name.endswith(".mp4") and not (
                (ctype or "").endswith("mp4") or (len(data) > 12 and data[4:8] == b"ftyp")
            ):
                out_name = out_name.replace(".mp4", ".svg")
            zf.writestr(f"deliverables/{out_name}", data)

            # audio bed
            if names[1]:
                beds = (
                    db.query(Asset)
                    .filter(Asset.project_id == project_id, Asset.asset_type == "audio")
                    .order_by(Asset.created_at.desc())
                    .all()
                )
                linked = next(
                    (a for a in beds if (a.metadata_json or {}).get("linked_job") == job.id),
                    None,
                )
                if linked and linked.storage_path:
                    adata, _ = storage.get_object(linked.storage_path)
                    zf.writestr(f"deliverables/{names[1]}", adata)

        # Logo
        logo_assets = [
            a
            for a in db.query(Asset).filter(Asset.project_id == project_id).all()
            if (a.metadata_json or {}).get("role") == "brand_logo"
            and (a.metadata_json or {}).get("package_id") == package_id
        ]
        if logo_assets and logo_assets[0].storage_path:
            ldata, _ = storage.get_object(logo_assets[0].storage_path)
            zf.writestr("brand/art_city_logo.svg", ldata)

        readme = f"""# Art City Cinema · Delivery Package

Campaign: {package.get('campaign')}
Brand: {package.get('brand')}
Package ID: {package_id}

Contents:
- CAMPAIGN_MANIFEST.json (delivery targets, variants, timeline)
- TECHNICAL_VALIDATION.json
- deliverables/ (MP4 channel masters when muxed, stems, end card)
- brand/art_city_logo.svg

Ownership: Art City proprietary package.
"""
        zf.writestr("README.txt", readme)
        # Mix master stem
        mix_path = package.get("mix_master_path")
        if mix_path:
            try:
                mdata, _ = storage.get_object(mix_path)
                zf.writestr("deliverables/mix_master.wav", mdata)
            except Exception:
                pass
        # Timeline finishing doc
        timeline = package.get("timeline") or (package.get("campaign_manifest") or {}).get("timeline")
        if timeline:
            zf.writestr("TIMELINE.json", json.dumps(timeline, indent=2))

    return buf.getvalue()
