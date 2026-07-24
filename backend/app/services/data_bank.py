"""Project Data Bank — catalog of project media (uploads + Studio generations)."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import AssetType, GenerationStatus
from app.models import Asset, GenerationJob, Project
from app.services.gateway import enqueue_generation
from app.services.storage import get_storage

BANK_PROJECT_NAME = "Art City Data Bank"

BANK_BUILDING_PROMPT = (
    "Cinematic architectural photograph of a prestigious modern bank building facade, "
    "Art City Studios production still, marble and glass tower with stone columns, "
    "gold Art City crest above the entrance, evening city lights, dramatic wide angle, "
    "photorealistic, 16:9 framing, high detail exterior architecture"
)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(name: str) -> str:
    base = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].strip() or "upload.bin"
    cleaned = _SAFE_NAME.sub("_", base)[:180]
    return cleaned or "upload.bin"


def _guess_asset_type(filename: str, content_type: str) -> str:
    ct = (content_type or "").lower()
    lower = filename.lower()
    if ct.startswith("image/") or lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return AssetType.IMAGE.value
    if ct.startswith("video/") or lower.endswith((".mp4", ".mov", ".webm", ".mkv")):
        return AssetType.VIDEO.value
    if "audio" in ct or lower.endswith((".wav", ".mp3", ".m4a", ".ogg", ".flac")):
        if "music" in lower:
            return AssetType.MUSIC.value
        return AssetType.AUDIO.value
    if lower.endswith((".srt", ".vtt")):
        return AssetType.SUBTITLE.value
    if lower.endswith((".txt", ".md", ".pdf", ".docx")):
        return AssetType.SCRIPT.value
    return AssetType.OTHER.value


def enrich_asset(asset: Asset) -> dict[str, Any]:
    meta = dict(asset.metadata_json or {})
    return {
        "id": asset.id,
        "project_id": asset.project_id,
        "asset_type": asset.asset_type,
        "name": asset.name,
        "storage_path": asset.storage_path,
        "checksum": asset.checksum,
        "metadata_json": meta,
        "soft_deleted": asset.soft_deleted,
        "created_at": asset.created_at,
        "media_url": f"/api/assets/file/{asset.id}" if asset.storage_path else None,
        "source": meta.get("source") or ("generation" if meta.get("job_id") else "upload"),
        "tags": meta.get("tags") or [],
        "prompt": meta.get("prompt"),
        "size_bytes": meta.get("size_bytes"),
        "content_type": meta.get("content_type"),
    }


def list_bank_assets(
    db: Session,
    project_id: str,
    *,
    q: Optional[str] = None,
    asset_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    query = db.query(Asset).filter(Asset.project_id == project_id, Asset.soft_deleted.is_(False))
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type.strip().lower())
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Asset.name.ilike(term),
                Asset.storage_path.ilike(term),
            )
        )
    rows = query.order_by(Asset.created_at.desc()).limit(max(1, min(limit, 500))).all()
    out = [enrich_asset(a) for a in rows]
    if source:
        src = source.strip().lower()
        out = [r for r in out if (r.get("source") or "").lower() == src]
    if q:
        ql = q.strip().lower()
        out = [
            r
            for r in out
            if ql in (r.get("name") or "").lower()
            or ql in (r.get("prompt") or "").lower()
            or any(ql in str(t).lower() for t in (r.get("tags") or []))
        ]
    return out


def bank_summary(db: Session, project_id: str) -> dict[str, Any]:
    rows = (
        db.query(Asset)
        .filter(Asset.project_id == project_id, Asset.soft_deleted.is_(False))
        .all()
    )
    by_type: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for a in rows:
        by_type[a.asset_type] = by_type.get(a.asset_type, 0) + 1
        meta = a.metadata_json or {}
        src = meta.get("source") or ("generation" if meta.get("job_id") else "upload")
        by_source[src] = by_source.get(src, 0) + 1
    return {
        "project_id": project_id,
        "total": len(rows),
        "by_type": by_type,
        "by_source": by_source,
    }


def upload_to_bank(
    db: Session,
    *,
    project_id: str,
    filename: str,
    data: bytes,
    content_type: str,
    name: Optional[str] = None,
    tags: Optional[list[str]] = None,
    notes: Optional[str] = None,
) -> Asset:
    safe = _safe_filename(filename)
    checksum = hashlib.sha256(data).hexdigest()
    key = f"projects/{project_id}/data-bank/{uuid4().hex[:12]}_{safe}"
    storage = get_storage()
    storage.upload_bytes(key, data, content_type or "application/octet-stream")
    asset_type = _guess_asset_type(safe, content_type)
    asset = Asset(
        project_id=project_id,
        asset_type=asset_type,
        name=(name or safe)[:255],
        storage_path=key,
        checksum=checksum,
        metadata_json={
            "source": "upload",
            "original_filename": filename,
            "content_type": content_type,
            "size_bytes": len(data),
            "tags": tags or ["data-bank"],
            "notes": notes,
            "bank": True,
        },
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def sync_generations_into_bank(db: Session, project_id: str) -> dict[str, int]:
    """Index succeeded Studio/Cinema generation outputs that are missing as bank assets."""
    jobs = (
        db.query(GenerationJob)
        .filter(
            GenerationJob.project_id == project_id,
            GenerationJob.status == GenerationStatus.SUCCEEDED.value,
            GenerationJob.result_uri.isnot(None),
        )
        .all()
    )
    existing_paths = {
        a.storage_path
        for a in db.query(Asset)
        .filter(Asset.project_id == project_id, Asset.soft_deleted.is_(False))
        .all()
        if a.storage_path
    }
    linked_jobs = {
        (a.metadata_json or {}).get("job_id")
        for a in db.query(Asset).filter(Asset.project_id == project_id).all()
        if (a.metadata_json or {}).get("job_id")
    }
    created = 0
    skipped = 0
    for job in jobs:
        if job.id in linked_jobs or (job.result_uri and job.result_uri in existing_paths):
            skipped += 1
            continue
        modality = (job.modality or AssetType.OTHER.value).lower()
        asset_type = modality if modality in {t.value for t in AssetType} else AssetType.OTHER.value
        asset = Asset(
            project_id=project_id,
            asset_type=asset_type,
            name=f"{modality}: {(job.prompt or job.id)[:60]}",
            storage_path=job.result_uri,
            metadata_json={
                "source": "generation",
                "job_id": job.id,
                "provider": job.provider,
                "prompt": job.prompt,
                "provider_job_id": job.provider_job_id,
                "tags": ["data-bank", "synced", modality],
                "bank": True,
            },
        )
        db.add(asset)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped, "jobs_scanned": len(jobs)}


def soft_delete_bank_asset(db: Session, project_id: str, asset_id: str) -> Asset:
    asset = db.get(Asset, asset_id)
    if not asset or asset.project_id != project_id or asset.soft_deleted:
        raise ValueError("Asset not found")
    asset.soft_deleted = True
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_or_create_bank_project(db: Session) -> Project:
    existing = (
        db.query(Project)
        .filter(Project.name == BANK_PROJECT_NAME)
        .order_by(Project.created_at.desc())
        .first()
    )
    if existing:
        return existing
    project = Project(
        name=BANK_PROJECT_NAME,
        description="Central project media data bank — uploads, Studio stills, and synced generations",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def seed_data_bank(db: Session, *, requested_by: Optional[str] = None) -> dict[str, Any]:
    """Ensure bank project exists, seed a bank-building image, sync generations."""
    project = get_or_create_bank_project(db)
    job = enqueue_generation(
        db,
        project_id=project.id,
        modality="image",
        prompt=BANK_BUILDING_PROMPT,
        model="artcity-local-v1",
        prefer_external=True,
        requested_by=requested_by,
        params={"demo": "bank_building", "bank": True, "tags": ["bank-building", "seed"]},
    )
    # Tag the primary asset if present
    assets = (
        db.query(Asset)
        .filter(Asset.project_id == project.id, Asset.storage_path == job.result_uri)
        .all()
    )
    for asset in assets:
        meta = dict(asset.metadata_json or {})
        meta["source"] = meta.get("source") or "generation"
        meta["job_id"] = job.id
        meta["bank"] = True
        meta["tags"] = list({*(meta.get("tags") or []), "bank-building", "seed", "data-bank"})
        meta["prompt"] = job.prompt
        asset.metadata_json = meta
        if not asset.name.startswith("bank"):
            asset.name = f"bank-building · {(job.prompt or '')[:40]}"
        db.add(asset)
    db.commit()
    sync = sync_generations_into_bank(db, project.id)
    summary = bank_summary(db, project.id)
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
        },
        "seed_job_id": job.id,
        "seed_status": job.status,
        "seed_media_url": f"/api/media/{project.id}/{job.id}/primary" if job.result_uri else None,
        "sync": sync,
        "summary": summary,
    }


def hub_overview(db: Session) -> dict[str, Any]:
    projects = db.query(Project).order_by(Project.created_at.desc()).limit(50).all()
    items = []
    total_assets = 0
    for p in projects:
        s = bank_summary(db, p.id)
        if s["total"] == 0:
            continue
        total_assets += s["total"]
        items.append({"project_id": p.id, "name": p.name, **s})
    bank = (
        db.query(Project)
        .filter(Project.name == BANK_PROJECT_NAME)
        .order_by(Project.created_at.desc())
        .first()
    )
    return {
        "projects_with_assets": len(items),
        "total_assets": total_assets,
        "bank_project_id": bank.id if bank else None,
        "projects": items,
    }
