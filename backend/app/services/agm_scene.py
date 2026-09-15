"""AC Graphic Motion scene/revision domain service."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.ids import load_project
from app.models_agm import AgmRevision, AgmScene
from app.services import agm_brand
from app.services.agm_patch import PatchError, apply_patch
from app.services.agm_validate import validate_graph


def content_hash(graph: dict[str, Any]) -> str:
    payload = json.dumps(graph, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _default_graph(*, scene_id: str, project_id: str, name: str, locale: str, direction: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "scene_id": scene_id,
        "project_id": project_id,
        "name": name,
        "locale": locale,
        "direction": direction,
        "canvas": {
            "width": 1920,
            "height": 1080,
            "fps": 25,
            "duration_ms": 8000,
            "background": "#00000000",
            "color_space": "rec709",
        },
        "timeline": {"timebase": "ms", "play_start_ms": 0, "play_end_ms": 8000},
        "brand_context": None,
        "variables": {},
        "nodes": [],
        "markers": [],
        "audio": [],
        "metadata": {},
    }


def create_scene(
    db: Session,
    *,
    project_id: str,
    name: str,
    user_id: Optional[str],
    graph: Optional[dict[str, Any]] = None,
    locale: str = "ckb-IQ",
    direction: str = "rtl",
    idempotency_key: Optional[str] = None,
) -> tuple[AgmScene, AgmRevision]:
    load_project(db, project_id)
    if idempotency_key:
        existing = (
            db.query(AgmScene)
            .filter(AgmScene.project_id == project_id, AgmScene.idempotency_key == idempotency_key)
            .first()
        )
        if existing and not existing.soft_deleted:
            rev = db.get(AgmRevision, existing.head_revision_id) if existing.head_revision_id else None
            if rev:
                return existing, rev

    scene_id = str(uuid4())
    base = graph or _default_graph(
        scene_id=scene_id, project_id=project_id, name=name, locale=locale, direction=direction
    )
    base = dict(base)
    base["scene_id"] = scene_id
    base["project_id"] = project_id
    base["name"] = name
    base.setdefault("locale", locale)
    base.setdefault("direction", direction)
    base.setdefault("schema_version", "1.0.0")

    report = validate_graph(base, db=db, strict_assets=False)
    if not report["valid"]:
        raise HTTPException(status_code=400, detail={"code": report["error_codes"][0], "errors": report["errors"]})

    ch = content_hash(base)
    scene = AgmScene(
        id=scene_id,
        project_id=project_id,
        name=name[:160],
        locale=base.get("locale") or locale,
        direction=base.get("direction") or direction,
        content_hash=ch,
        etag=ch,
        idempotency_key=idempotency_key,
        created_by=user_id,
    )
    db.add(scene)
    db.flush()
    rev = AgmRevision(
        scene_id=scene.id,
        project_id=project_id,
        revision_no=1,
        graph_json=base,
        content_hash=ch,
        created_by=user_id,
    )
    db.add(rev)
    db.flush()
    scene.head_revision_id = rev.id
    db.add(scene)
    db.commit()
    db.refresh(scene)
    db.refresh(rev)
    return scene, rev


def get_scene(db: Session, scene_id: str) -> AgmScene:
    scene = db.get(AgmScene, scene_id)
    if not scene or scene.soft_deleted:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


def soft_delete_scene(db: Session, scene_id: str) -> AgmScene:
    scene = get_scene(db, scene_id)
    scene.soft_deleted = True
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


def list_revisions(db: Session, scene_id: str) -> list[AgmRevision]:
    get_scene(db, scene_id)
    return (
        db.query(AgmRevision)
        .filter(AgmRevision.scene_id == scene_id)
        .order_by(AgmRevision.revision_no.asc())
        .all()
    )


def get_revision(db: Session, scene_id: str, revision_id: str) -> AgmRevision:
    get_scene(db, scene_id)
    rev = db.get(AgmRevision, revision_id)
    if not rev or rev.scene_id != scene_id:
        raise HTTPException(status_code=404, detail="Revision not found")
    return rev


def patch_scene(
    db: Session,
    *,
    scene_id: str,
    operations: list[dict[str, Any]],
    if_match: str,
    user_id: Optional[str],
) -> tuple[AgmScene, AgmRevision]:
    scene = get_scene(db, scene_id)
    if not scene.etag or scene.etag != if_match.strip().strip('"'):
        raise HTTPException(
            status_code=409,
            detail={"code": "AGM_REVISION_CONFLICT", "message": "If-Match does not match head revision"},
        )
    if not scene.head_revision_id:
        raise HTTPException(status_code=400, detail="Scene has no head revision")
    head = db.get(AgmRevision, scene.head_revision_id)
    if not head:
        raise HTTPException(status_code=400, detail="Head revision missing")

    try:
        new_graph = apply_patch(head.graph_json or {}, operations)
    except PatchError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc

    new_graph["scene_id"] = scene.id
    new_graph["project_id"] = scene.project_id
    brand_errs = agm_brand.assert_no_logo_mutation(head.graph_json or {}, new_graph)
    if brand_errs:
        raise HTTPException(status_code=400, detail={"code": "AGM_BRAND_LOGO_MUTATION", "errors": brand_errs})

    report = validate_graph(new_graph, db=db, strict_assets=False)
    if not report["valid"]:
        raise HTTPException(status_code=400, detail={"code": report["error_codes"][0], "errors": report["errors"]})

    ch = content_hash(new_graph)
    rev = AgmRevision(
        scene_id=scene.id,
        project_id=scene.project_id,
        revision_no=head.revision_no + 1,
        graph_json=new_graph,
        content_hash=ch,
        parent_revision_id=head.id,
        created_by=user_id,
    )
    db.add(rev)
    db.flush()
    scene.head_revision_id = rev.id
    scene.content_hash = ch
    scene.etag = ch
    scene.name = str(new_graph.get("name") or scene.name)[:160]
    db.add(scene)
    db.commit()
    db.refresh(scene)
    db.refresh(rev)
    return scene, rev


def scene_out(scene: AgmScene, rev: Optional[AgmRevision] = None) -> dict[str, Any]:
    return {
        "id": scene.id,
        "project_id": scene.project_id,
        "name": scene.name,
        "locale": scene.locale,
        "direction": scene.direction,
        "head_revision_id": scene.head_revision_id,
        "etag": scene.etag,
        "content_hash": scene.content_hash,
        "soft_deleted": scene.soft_deleted,
        "created_at": scene.created_at,
        "updated_at": scene.updated_at,
        "revision": revision_out(rev) if rev else None,
    }


def revision_out(rev: AgmRevision) -> dict[str, Any]:
    return {
        "id": rev.id,
        "scene_id": rev.scene_id,
        "project_id": rev.project_id,
        "revision_no": rev.revision_no,
        "content_hash": rev.content_hash,
        "parent_revision_id": rev.parent_revision_id,
        "graph": rev.graph_json,
        "created_at": rev.created_at,
    }
