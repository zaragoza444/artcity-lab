"""Art City Production Hub API — AC Script + Breakdown + handoff."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser
from app.core.ids import load_project
from app.models import Asset, Project
from app.models_hub import (
    HubBreakdownItem,
    HubCharacter,
    HubLocation,
    HubScene,
    HubScript,
    HubScriptElement,
    HubScriptVersion,
    HubStaleFlag,
)
from app.services import hub_breakdown, hub_export, hub_script
from app.services.hub_access import hub_features, require_hub_module, require_script_edit, require_script_lock
from app.services.hub_events import emit_event
from app.services.hub_parser import rebuild_scenes_from_elements
from app.services.storage import get_storage

router = APIRouter(prefix="/api/v1/hub", tags=["production-hub"])


class FeaturesOut(BaseModel):
    script: bool
    storyboard: bool
    budget: bool
    call: bool


class ScriptCreateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    entry_mode: str = "blank"
    primary_locale: str = "en"
    content_languages: Optional[list[str]] = None
    seed_text: Optional[str] = None


class ElementIn(BaseModel):
    element_type: str
    display_text: str = ""
    locale: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
    id: Optional[str] = None


class ElementsSaveIn(BaseModel):
    elements: list[ElementIn]


class AiCommandIn(BaseModel):
    command: Literal[
        "rewrite",
        "shorten",
        "expand",
        "polish",
        "translate",
        "improve_dialogue",
        "add_conflict",
    ]
    target_locale: Optional[str] = None
    element_ids: Optional[list[str]] = None
    apply: bool = False


class BreakdownDecisionIn(BaseModel):
    approval_status: Literal["approved", "rejected", "proposed"]


class HandoffIn(BaseModel):
    script_version_id: Optional[str] = None
    scene_ids: Optional[list[str]] = None


class ScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    entry_mode: str
    primary_locale: str
    content_languages: Optional[list] = None
    current_version_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    script_id: str
    project_id: str
    version_label: str
    status: str
    page_eighths: int
    locked_at: Optional[datetime]
    parent_version_id: Optional[str]
    created_at: datetime


class ElementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    script_version_id: str
    position: int
    element_type: str
    display_text: str
    scene_id: Optional[str]
    character_id: Optional[str]
    locale: Optional[str]
    metadata_json: Optional[dict] = None


class SceneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    script_version_id: str
    scene_number: str
    int_ext: Optional[str]
    location_name: Optional[str]
    time_of_day: Optional[str]
    heading_display: Optional[str]
    page_eighths: int
    sort_order: int


class BreakdownOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scene_id: str
    category: str
    display_text: str
    quantity: Optional[float]
    approval_status: str
    source: str


@router.get("/features", response_model=FeaturesOut)
def get_features(user: CurrentUser) -> FeaturesOut:
    return FeaturesOut(**hub_features())


@router.get("/projects/{project_id}/scripts", response_model=list[ScriptOut])
def list_scripts(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[HubScript]:
    require_hub_module("script")
    load_project(db, project_id)
    return (
        db.query(HubScript)
        .filter(HubScript.project_id == project_id, HubScript.status == "active")
        .order_by(HubScript.updated_at.desc())
        .all()
    )


@router.post("/projects/{project_id}/scripts", response_model=ScriptOut, status_code=201)
def create_script(
    project_id: str, payload: ScriptCreateIn, user: CurrentUser, db: Session = Depends(get_db)
) -> HubScript:
    require_hub_module("script")
    require_script_edit(user)
    project = load_project(db, project_id)
    try:
        script = hub_script.create_script(
            db,
            project=project,
            user=user,
            title=payload.title,
            entry_mode=payload.entry_mode,
            primary_locale=payload.primary_locale,
            content_languages=payload.content_languages,
            seed_text=payload.seed_text,
        )
        db.commit()
        db.refresh(script)
        return script
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/scripts/{script_id}", response_model=ScriptOut)
def get_script(script_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> HubScript:
    require_hub_module("script")
    script = db.get(HubScript, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.get("/scripts/{script_id}/versions", response_model=list[VersionOut])
def list_versions(script_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[HubScriptVersion]:
    require_hub_module("script")
    return (
        db.query(HubScriptVersion)
        .filter(HubScriptVersion.script_id == script_id)
        .order_by(HubScriptVersion.created_at.desc())
        .all()
    )


@router.post("/scripts/{script_id}/versions", response_model=VersionOut, status_code=201)
def new_revision(
    script_id: str, user: CurrentUser, db: Session = Depends(get_db), label: Optional[str] = None
) -> HubScriptVersion:
    require_hub_module("script")
    require_script_edit(user)
    script = db.get(HubScript, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    try:
        version = hub_script.create_revision(db, script=script, user=user, label=label)
        db.commit()
        db.refresh(version)
        return version
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/versions/{version_id}/lock", response_model=VersionOut)
def lock_version(version_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> HubScriptVersion:
    require_hub_module("script")
    require_script_lock(user)
    version = hub_script.get_version(db, version_id)
    version = hub_script.lock_version(db, version=version, user=user)
    db.commit()
    db.refresh(version)
    return version


@router.get("/versions/{version_id}/elements", response_model=list[ElementOut])
def get_elements(version_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[HubScriptElement]:
    require_hub_module("script")
    hub_script.get_version(db, version_id)
    return hub_script.list_elements(db, version_id)


@router.put("/versions/{version_id}/elements", response_model=list[ElementOut])
def save_elements(
    version_id: str, payload: ElementsSaveIn, user: CurrentUser, db: Session = Depends(get_db)
) -> list[HubScriptElement]:
    require_hub_module("script")
    require_script_edit(user)
    version = hub_script.get_version(db, version_id)
    try:
        rows = hub_script.autosave_elements(
            db,
            version=version,
            elements=[e.model_dump() for e in payload.elements],
            user=user,
        )
        db.commit()
        return rows
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/versions/{version_id}/parse-scenes", response_model=list[SceneOut])
def parse_scenes(version_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[HubScene]:
    require_hub_module("script")
    require_script_edit(user)
    version = hub_script.get_version(db, version_id)
    if version.status == "locked":
        raise HTTPException(status_code=400, detail="Cannot re-parse a locked version")
    scenes = rebuild_scenes_from_elements(
        db, project_id=version.project_id, script_id=version.script_id, script_version_id=version.id
    )
    emit_event(
        db,
        project_id=version.project_id,
        event_type="script.scenes_parsed",
        resource_type="hub_script_version",
        resource_id=version.id,
        payload={"scene_count": len(scenes)},
        created_by=user.id,
    )
    db.commit()
    return scenes


@router.get("/versions/{version_id}/scenes", response_model=list[SceneOut])
def list_scenes(version_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[HubScene]:
    require_hub_module("script")
    return (
        db.query(HubScene)
        .filter(HubScene.script_version_id == version_id)
        .order_by(HubScene.sort_order.asc())
        .all()
    )


@router.get("/versions/compare")
def compare(a: str, b: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_hub_module("script")
    return hub_script.compare_versions(db, a, b)


@router.post("/versions/{version_id}/ai")
def ai_command(
    version_id: str, payload: AiCommandIn, user: CurrentUser, db: Session = Depends(get_db)
) -> dict:
    require_hub_module("script")
    require_script_edit(user)
    version = hub_script.get_version(db, version_id)
    try:
        result = hub_script.ai_transform_elements(
            db,
            version=version,
            user=user,
            command=payload.command,
            target_locale=payload.target_locale,
            element_ids=payload.element_ids,
        )
        if payload.apply and result.get("elements"):
            hub_script.autosave_elements(db, version=version, elements=result["elements"], user=user)
            result["apply"] = True
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/versions/{version_id}/breakdown/propose", response_model=list[BreakdownOut])
def propose_breakdown(
    version_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[HubBreakdownItem]:
    require_hub_module("script")
    require_script_edit(user)
    version = hub_script.get_version(db, version_id)
    items = hub_breakdown.propose_breakdown(
        db, project_id=version.project_id, script_version_id=version.id, user_id=user.id
    )
    db.commit()
    return items


@router.get("/versions/{version_id}/breakdown", response_model=list[BreakdownOut])
def list_breakdown(version_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[HubBreakdownItem]:
    require_hub_module("script")
    return (
        db.query(HubBreakdownItem)
        .filter(HubBreakdownItem.script_version_id == version_id)
        .order_by(HubBreakdownItem.created_at.asc())
        .all()
    )


@router.post("/breakdown/{item_id}/decision", response_model=BreakdownOut)
def decide_breakdown(
    item_id: str, payload: BreakdownDecisionIn, user: CurrentUser, db: Session = Depends(get_db)
) -> HubBreakdownItem:
    require_hub_module("script")
    require_script_edit(user)
    item = db.get(HubBreakdownItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Breakdown item not found")
    item.approval_status = payload.approval_status
    item.updated_by = user.id
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/versions/{version_id}/export/{fmt}")
def export_version(
    version_id: str, fmt: Literal["docx", "pdf"], user: CurrentUser, db: Session = Depends(get_db)
) -> Response:
    require_hub_module("script")
    version = hub_script.get_version(db, version_id)
    script = db.get(HubScript, version.script_id)
    elements = [
        {"element_type": e.element_type, "display_text": e.display_text}
        for e in hub_script.list_elements(db, version_id)
    ]
    title = script.title if script else "Screenplay"
    locale = script.primary_locale if script else "en"
    if fmt == "docx":
        data = hub_export.export_screenplay_docx(
            title=title, version_label=version.version_label, elements=elements, primary_locale=locale
        )
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{title}-{version.version_label}.docx".replace(" ", "_")
    else:
        data = hub_export.export_screenplay_pdf_bytes(
            title=title, version_label=version.version_label, elements=elements
        )
        media = "application/pdf"
        filename = f"{title}-{version.version_label}.pdf".replace(" ", "_")

    key = f"projects/{version.project_id}/hub/exports/{version.id}/{filename}"
    get_storage().upload_bytes(key, data, media)
    db.add(
        Asset(
            project_id=version.project_id,
            asset_type="script",
            name=filename,
            storage_path=key,
            metadata_json={
                "hub_script_version_id": version.id,
                "format": fmt,
                "lineage": "hub_export",
            },
        )
    )
    db.commit()
    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/projects/{project_id}/handoff/{target}")
def handoff(
    project_id: str,
    target: Literal["cinema", "studio", "edit"],
    payload: HandoffIn,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    require_hub_module("script")
    project = load_project(db, project_id)
    script = (
        db.query(HubScript)
        .filter(HubScript.project_id == project_id, HubScript.status == "active")
        .order_by(HubScript.updated_at.desc())
        .first()
    )
    version_id = payload.script_version_id or (script.current_version_id if script else None)
    if not version_id:
        raise HTTPException(status_code=400, detail="No script version to hand off")
    version = hub_script.get_version(db, version_id)
    scenes = (
        db.query(HubScene).filter(HubScene.script_version_id == version.id).order_by(HubScene.sort_order).all()
    )
    if payload.scene_ids:
        scenes = [s for s in scenes if s.id in set(payload.scene_ids)]
    characters = db.query(HubCharacter).filter(HubCharacter.project_id == project_id).all()
    locations = db.query(HubLocation).filter(HubLocation.project_id == project_id).all()

    package = {
        "project_id": project.id,
        "target": target,
        "script_id": version.script_id,
        "script_version_id": version.id,
        "version_label": version.version_label,
        "version_status": version.status,
        "scenes": [
            {
                "scene_id": s.id,
                "scene_number": s.scene_number,
                "heading": s.heading_display,
                "int_ext": s.int_ext,
                "location": s.location_name,
                "time_of_day": s.time_of_day,
                "page_eighths": s.page_eighths,
            }
            for s in scenes
        ],
        "characters": [{"id": c.id, "name": c.display_name} for c in characters],
        "locations": [{"id": loc.id, "name": loc.display_name} for loc in locations],
    }
    import json

    body = json.dumps(package, ensure_ascii=False, indent=2).encode("utf-8")
    key = f"projects/{project_id}/hub/handoff/{target}/{version.id}.json"
    get_storage().upload_bytes(key, body, "application/json")
    asset = Asset(
        id=str(uuid4()),
        project_id=project_id,
        asset_type="other",
        name=f"Hub handoff → {target}",
        storage_path=key,
        metadata_json={
            "hub_handoff": target,
            "script_version_id": version.id,
            "scene_ids": [s.id for s in scenes],
            "lineage": "hub_handoff",
        },
    )
    db.add(asset)
    emit_event(
        db,
        project_id=project_id,
        event_type=f"handoff.{target}",
        resource_type="hub_script_version",
        resource_id=version.id,
        payload={"asset_id": asset.id, "scene_count": len(scenes)},
        created_by=user.id,
    )
    db.commit()
    links = {
        "cinema": f"/cinema/{project_id}",
        "studio": f"/studio/{project_id}",
        "edit": f"/edit",
    }
    return {
        "ok": True,
        "target": target,
        "asset_id": asset.id,
        "storage_key": key,
        "redirect": links[target],
        "package": package,
    }


@router.get("/projects/{project_id}/stale")
def list_stale(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_hub_module("script")
    load_project(db, project_id)
    flags = (
        db.query(HubStaleFlag)
        .filter(HubStaleFlag.project_id == project_id, HubStaleFlag.active.is_(True))
        .all()
    )
    return [
        {
            "id": f.id,
            "resource_type": f.resource_type,
            "resource_id": f.resource_id,
            "reason": f.reason,
        }
        for f in flags
    ]


@router.get("/projects/{project_id}/characters")
def list_characters(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_hub_module("script")
    rows = db.query(HubCharacter).filter(HubCharacter.project_id == project_id).all()
    return [{"id": r.id, "display_name": r.display_name, "bible_json": r.bible_json} for r in rows]


@router.get("/projects/{project_id}/locations")
def list_locations(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_hub_module("script")
    rows = db.query(HubLocation).filter(HubLocation.project_id == project_id).all()
    return [{"id": r.id, "display_name": r.display_name, "bible_json": r.bible_json} for r in rows]
