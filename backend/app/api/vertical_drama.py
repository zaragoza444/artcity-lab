"""Art City Vertical Drama IP Factory API — Sprints 0–4."""

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser
from app.core.ids import load_project
from app.models import Asset, CostRecord, Project
from app.models_vd import (
    VdAssembly,
    VdCanonFact,
    VdCharacter,
    VdContributor,
    VdDeliveryPackage,
    VdDomainEvent,
    VdEpisode,
    VdEpisodeBeat,
    VdEpisodeVersion,
    VdGenerationJob,
    VdIpTitle,
    VdLocation,
    VdProject,
    VdProp,
    VdProvenanceEntry,
    VdQcRun,
    VdRightsRecord,
    VdScene,
    VdSeason,
    VdShot,
    VdStoryBible,
    VdStoryBibleVersion,
    VdSubtitleTrack,
    VdWardrobeItem,
)
from app.services.storage import get_storage
from app.services.vd_access import assert_transition, require_approve, require_edit, require_vd, vd_enabled

router = APIRouter(prefix="/api/v1/vertical-drama", tags=["vertical-drama"])


def _event(db: Session, *, project_id: str, event_type: str, resource_type: str, resource_id: str, payload: dict, user_id: str) -> None:
    db.add(
        VdDomainEvent(
            id=str(uuid4()),
            project_id=project_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            created_by=user_id,
        )
    )


def _vd(db: Session, project_id: str) -> VdProject:
    row = db.query(VdProject).filter(VdProject.project_id == project_id, VdProject.soft_deleted.is_(False)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Vertical Drama project not found")
    return row


class OrmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CreateIn(BaseModel):
    project_id: Optional[str] = None
    name: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    logline: Optional[str] = None
    source_type: str = "idea"
    production_mode: str = "ai_native"
    primary_locale: str = "en"
    content_languages: Optional[list[str]] = None
    seed_golden_a: bool = False


class CanonIn(BaseModel):
    entity_type: str = "world"
    fact_key: str
    fact_value: str


class CharacterIn(BaseModel):
    display_name: str
    locale: str = "en"
    bible_json: Optional[dict[str, Any]] = None
    identity_locked: bool = False


class LocationIn(BaseModel):
    display_name: str
    locale: str = "en"
    notes: Optional[str] = None


class BibleSaveIn(BaseModel):
    sections_json: dict[str, Any]


class SeasonIn(BaseModel):
    title: str = "Season 1"
    target_episode_count: int = 10
    target_episode_seconds: int = 90


class EpisodePatchIn(BaseModel):
    title: Optional[str] = None
    hook: Optional[str] = None
    key_beat: Optional[str] = None
    reveal: Optional[str] = None
    cliffhanger: Optional[str] = None
    status: Optional[str] = None


class ScreenplayIn(BaseModel):
    title: Optional[str] = None
    elements: list[dict[str, Any]] = Field(default_factory=list)


class GenerateShotIn(BaseModel):
    capability: str = "image"
    prompt: Optional[str] = None


class LocalizeIn(BaseModel):
    language: str
    kind: str = "subtitle"
    body: str = ""


@router.get("/features")
def features(user: CurrentUser) -> dict:
    return {"enabled": vd_enabled(), "product": "AC Vertical Drama"}


@router.post("/projects", status_code=201)
def create_vd_project(payload: CreateIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    if payload.project_id:
        project = load_project(db, payload.project_id)
    else:
        project = Project(
            id=str(uuid4()),
            name=payload.name or payload.title,
            description=payload.logline,
            primary_locale=payload.primary_locale,
            content_languages=payload.content_languages or [payload.primary_locale],
        )
        db.add(project)
        db.flush()
    existing = db.query(VdProject).filter(VdProject.project_id == project.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Vertical Drama already exists for this project")
    vd = VdProject(
        id=str(uuid4()),
        project_id=project.id,
        title=payload.title,
        logline=payload.logline,
        source_type=payload.source_type,
        production_mode=payload.production_mode,
        primary_locale=payload.primary_locale,
        content_languages=payload.content_languages or [payload.primary_locale],
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(vd)
    db.flush()
    ip = VdIpTitle(
        id=str(uuid4()),
        vd_project_id=vd.id,
        project_id=project.id,
        title=payload.title,
        logline=payload.logline,
        language=payload.primary_locale,
        created_by=user.id,
    )
    db.add(ip)
    db.flush()
    vd.current_ip_title_id = ip.id
    db.add(
        VdProvenanceEntry(
            id=str(uuid4()),
            ip_title_id=ip.id,
            project_id=project.id,
            kind="human_authorship",
            summary="IP title created",
            created_by=user.id,
        )
    )
    if payload.seed_golden_a:
        _seed_golden_a(db, vd=vd, ip=ip, user_id=user.id)
    _event(db, project_id=project.id, event_type="vd.project.created", resource_type="vd_project", resource_id=vd.id, payload={}, user_id=user.id)
    db.commit()
    db.refresh(vd)
    return _project_out(db, vd)


@router.get("/projects")
def list_vd_projects(user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdProject).filter(VdProject.soft_deleted.is_(False)).order_by(VdProject.updated_at.desc()).all()
    return [_project_out(db, r) for r in rows]


@router.get("/projects/by-platform/{project_id}")
def get_by_platform(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    load_project(db, project_id)
    return _project_out(db, _vd(db, project_id))


@router.get("/projects/{vd_project_id}")
def get_vd(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    return _project_out(db, vd)


@router.post("/projects/{vd_project_id}/rights", status_code=201)
def add_rights(vd_project_id: str, payload: dict, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    if not vd or not vd.current_ip_title_id:
        raise HTTPException(status_code=404, detail="IP title missing")
    row = VdRightsRecord(
        id=str(uuid4()),
        ip_title_id=vd.current_ip_title_id,
        project_id=vd.project_id,
        territory=payload.get("territory") or "IQ",
        window=payload.get("window"),
        rights_type=payload.get("rights_type") or "original",
        status=payload.get("status") or "declared",
        notes=payload.get("notes"),
        blocks_delivery=bool(payload.get("blocks_delivery")),
        created_by=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "territory": row.territory, "status": row.status, "blocks_delivery": row.blocks_delivery}


@router.get("/projects/{vd_project_id}/rights")
def list_rights(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    rows = db.query(VdRightsRecord).filter(VdRightsRecord.ip_title_id == vd.current_ip_title_id).all()
    return [
        {"id": r.id, "territory": r.territory, "rights_type": r.rights_type, "status": r.status, "blocks_delivery": r.blocks_delivery, "notes": r.notes}
        for r in rows
    ]


@router.post("/projects/{vd_project_id}/contributors", status_code=201)
def add_contributor(vd_project_id: str, payload: dict, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    row = VdContributor(
        id=str(uuid4()),
        ip_title_id=vd.current_ip_title_id,
        project_id=vd.project_id,
        display_name=payload.get("display_name") or "Contributor",
        role=payload.get("role") or "creator",
        contribution=payload.get("contribution"),
        created_by=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "display_name": row.display_name, "role": row.role}


@router.get("/projects/{vd_project_id}/contributors")
def list_contributors(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    vd = db.get(VdProject, vd_project_id)
    rows = db.query(VdContributor).filter(VdContributor.ip_title_id == vd.current_ip_title_id).all() if vd else []
    return [{"id": r.id, "display_name": r.display_name, "role": r.role, "contribution": r.contribution} for r in rows]


@router.get("/projects/{vd_project_id}/provenance")
def list_provenance(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    vd = db.get(VdProject, vd_project_id)
    rows = db.query(VdProvenanceEntry).filter(VdProvenanceEntry.ip_title_id == vd.current_ip_title_id).all() if vd else []
    return [{"id": r.id, "kind": r.kind, "summary": r.summary, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]


@router.post("/projects/{vd_project_id}/characters", status_code=201)
def add_character(vd_project_id: str, payload: CharacterIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    row = VdCharacter(
        id=str(uuid4()),
        vd_project_id=vd.id,
        project_id=vd.project_id,
        display_name=payload.display_name,
        locale=payload.locale,
        bible_json=payload.bible_json or {},
        identity_locked=payload.identity_locked,
        status="approved" if payload.identity_locked else "draft",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _char_out(row)


@router.get("/projects/{vd_project_id}/characters")
def list_characters(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdCharacter).filter(VdCharacter.vd_project_id == vd_project_id).all()
    return [_char_out(r) for r in rows]


@router.post("/projects/{vd_project_id}/locations", status_code=201)
def add_location(vd_project_id: str, payload: LocationIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    row = VdLocation(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id, display_name=payload.display_name, locale=payload.locale, notes=payload.notes)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "display_name": row.display_name, "locale": row.locale}


@router.get("/projects/{vd_project_id}/locations")
def list_locations(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdLocation).filter(VdLocation.vd_project_id == vd_project_id).all()
    return [{"id": r.id, "display_name": r.display_name, "locale": r.locale, "notes": r.notes} for r in rows]


@router.post("/projects/{vd_project_id}/props", status_code=201)
def add_prop(vd_project_id: str, payload: dict, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    row = VdProp(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id, display_name=payload.get("display_name") or "Prop", notes=payload.get("notes"))
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "display_name": row.display_name}


@router.get("/projects/{vd_project_id}/props")
def list_props(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdProp).filter(VdProp.vd_project_id == vd_project_id).all()
    return [{"id": r.id, "display_name": r.display_name, "notes": r.notes} for r in rows]


@router.post("/projects/{vd_project_id}/wardrobe", status_code=201)
def add_wardrobe(vd_project_id: str, payload: dict, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    row = VdWardrobeItem(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id, display_name=payload.get("display_name") or "Look", character_id=payload.get("character_id"), notes=payload.get("notes"))
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "display_name": row.display_name, "character_id": row.character_id}


@router.get("/projects/{vd_project_id}/wardrobe")
def list_wardrobe(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdWardrobeItem).filter(VdWardrobeItem.vd_project_id == vd_project_id).all()
    return [{"id": r.id, "display_name": r.display_name, "character_id": r.character_id} for r in rows]


@router.post("/projects/{vd_project_id}/canon", status_code=201)
def add_canon(vd_project_id: str, payload: CanonIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    conflicts = _canon_conflicts(db, vd.id, payload.fact_key, payload.fact_value)
    row = VdCanonFact(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id, entity_type=payload.entity_type, fact_key=payload.fact_key, fact_value=payload.fact_value, created_by=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {**_canon_out(row), "conflicts": conflicts}


@router.get("/projects/{vd_project_id}/canon")
def list_canon(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdCanonFact).filter(VdCanonFact.vd_project_id == vd_project_id).order_by(VdCanonFact.created_at).all()
    return [_canon_out(r) for r in rows]


@router.post("/canon/{fact_id}/approve")
def approve_canon(fact_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_approve(user)
    row = db.get(VdCanonFact, fact_id)
    if not row:
        raise HTTPException(status_code=404, detail="Fact not found")
    if row.status == "locked":
        raise HTTPException(status_code=400, detail="Already locked — supersede to change")
    row.status = "locked"
    row.approved_by = user.id
    _event(db, project_id=row.project_id, event_type="vd.canon.approved", resource_type="vd_canon_fact", resource_id=row.id, payload={"key": row.fact_key}, user_id=user.id)
    db.commit()
    db.refresh(row)
    return _canon_out(row)


@router.post("/canon/{fact_id}/supersede")
def supersede_canon(fact_id: str, payload: CanonIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_approve(user)
    old = db.get(VdCanonFact, fact_id)
    if not old:
        raise HTTPException(status_code=404, detail="Fact not found")
    nxt = VdCanonFact(id=str(uuid4()), vd_project_id=old.vd_project_id, project_id=old.project_id, entity_type=payload.entity_type, fact_key=payload.fact_key or old.fact_key, fact_value=payload.fact_value, status="locked", created_by=user.id, approved_by=user.id)
    db.add(nxt)
    db.flush()
    old.status = "superseded"
    old.superseded_by = nxt.id
    for ep in db.query(VdEpisode).filter(VdEpisode.vd_project_id == old.vd_project_id, VdEpisode.status.in_(["approved", "production_ready", "locked"])).all():
        ep.stale = True
        ep.stale_reason = "OUT OF DATE — CANON SUPERSEDED"
    _event(db, project_id=old.project_id, event_type="vd.canon.superseded", resource_type="vd_canon_fact", resource_id=old.id, payload={"new_id": nxt.id}, user_id=user.id)
    db.commit()
    return _canon_out(nxt)


@router.post("/projects/{vd_project_id}/story-bible", status_code=201)
def create_bible(vd_project_id: str, payload: BibleSaveIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    bible = db.query(VdStoryBible).filter(VdStoryBible.vd_project_id == vd.id).first()
    if not bible:
        bible = VdStoryBible(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id)
        db.add(bible)
        db.flush()
    ver = VdStoryBibleVersion(id=str(uuid4()), story_bible_id=bible.id, project_id=vd.project_id, version_label=f"v{ _count_bible(db, bible.id)+1 }", sections_json=payload.sections_json, created_by=user.id)
    db.add(ver)
    db.flush()
    bible.current_version_id = ver.id
    db.commit()
    return _bible_out(bible, ver)


@router.get("/projects/{vd_project_id}/story-bible")
def get_bible(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    bible = db.query(VdStoryBible).filter(VdStoryBible.vd_project_id == vd_project_id).first()
    if not bible:
        return {"id": None, "versions": []}
    vers = db.query(VdStoryBibleVersion).filter(VdStoryBibleVersion.story_bible_id == bible.id).order_by(VdStoryBibleVersion.created_at.desc()).all()
    current = db.get(VdStoryBibleVersion, bible.current_version_id) if bible.current_version_id else None
    return {"id": bible.id, "status": bible.status, "current_version_id": bible.current_version_id, "current": _bible_ver(current) if current else None, "versions": [_bible_ver(v) for v in vers]}


@router.post("/story-bibles/{version_id}/approve")
def approve_bible(version_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_approve(user)
    ver = db.get(VdStoryBibleVersion, version_id)
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    from datetime import datetime, timezone

    ver.status = "locked"
    ver.approved_by = user.id
    ver.approved_at = datetime.now(timezone.utc)
    bible = db.get(VdStoryBible, ver.story_bible_id)
    if bible:
        bible.status = "locked"
        bible.current_version_id = ver.id
    _event(db, project_id=ver.project_id, event_type="vd.story_bible.approved", resource_type="vd_story_bible_version", resource_id=ver.id, payload={}, user_id=user.id)
    db.commit()
    return _bible_ver(ver)


@router.post("/projects/{vd_project_id}/seasons", status_code=201)
def create_season(vd_project_id: str, payload: SeasonIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    vd = db.get(VdProject, vd_project_id)
    if not vd:
        raise HTTPException(status_code=404, detail="Not found")
    bible = db.query(VdStoryBible).filter(VdStoryBible.vd_project_id == vd.id).first()
    season = VdSeason(
        id=str(uuid4()),
        vd_project_id=vd.id,
        project_id=vd.project_id,
        title=payload.title,
        target_episode_count=payload.target_episode_count,
        target_episode_seconds=payload.target_episode_seconds,
        story_bible_version_id=bible.current_version_id if bible else None,
    )
    db.add(season)
    db.flush()
    episodes = []
    for i in range(1, payload.target_episode_count + 1):
        ep = VdEpisode(
            id=str(uuid4()),
            season_id=season.id,
            vd_project_id=vd.id,
            project_id=vd.project_id,
            episode_number=i,
            title=f"Episode {i}",
            hook="Opening pressure",
            key_beat="Turn",
            reveal="New information",
            cliffhanger="Ending pressure",
            sort_order=i,
        )
        db.add(ep)
        episodes.append(ep)
    db.commit()
    return _season_out(db, season)


@router.get("/projects/{vd_project_id}/seasons")
def list_seasons(vd_project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdSeason).filter(VdSeason.vd_project_id == vd_project_id).all()
    return [_season_out(db, s) for s in rows]


@router.patch("/episodes/{episode_id}")
def patch_episode(episode_id: str, payload: EpisodePatchIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    if ep.status == "locked" and payload.status != "locked":
        raise HTTPException(status_code=400, detail="Locked episode — create a new version")
    for field in ("title", "hook", "key_beat", "reveal", "cliffhanger"):
        val = getattr(payload, field)
        if val is not None:
            setattr(ep, field, val)
    if payload.status and payload.status != ep.status:
        try:
            assert_transition(ep.status, payload.status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        ep.status = payload.status
        if payload.status == "approved":
            _event(db, project_id=ep.project_id, event_type="vd.episode.approved", resource_type="vd_episode", resource_id=ep.id, payload={}, user_id=user.id)
    db.commit()
    db.refresh(ep)
    return _ep_out(ep)


@router.post("/episodes/{episode_id}/screenplay")
def save_screenplay(episode_id: str, payload: ScreenplayIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    if ep.status == "locked":
        raise HTTPException(status_code=400, detail="Cannot edit locked episode")
    n = db.query(VdEpisodeVersion).filter(VdEpisodeVersion.episode_id == ep.id).count()
    ver = VdEpisodeVersion(
        id=str(uuid4()),
        episode_id=ep.id,
        project_id=ep.project_id,
        version_label=f"Draft {n + 1}",
        outline_json={"hook": ep.hook, "cliffhanger": ep.cliffhanger},
        screenplay_json={"title": payload.title or ep.title, "elements": payload.elements},
        created_by=user.id,
    )
    db.add(ver)
    db.flush()
    ep.current_version_id = ver.id
    if ep.status == "planned":
        ep.status = "drafted"
    db.commit()
    return {"version_id": ver.id, "episode_id": ep.id, "status": ep.status, "elements": payload.elements}


@router.get("/episodes/{episode_id}")
def get_episode(episode_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    beats = db.query(VdEpisodeBeat).filter(VdEpisodeBeat.episode_id == ep.id).order_by(VdEpisodeBeat.position).all()
    ver = db.get(VdEpisodeVersion, ep.current_version_id) if ep.current_version_id else None
    scenes = db.query(VdScene).filter(VdScene.episode_id == ep.id).order_by(VdScene.sort_order).all()
    shots = db.query(VdShot).filter(VdShot.episode_id == ep.id).all()
    return {
        **_ep_out(ep),
        "beats": [{"id": b.id, "beat_type": b.beat_type, "display_text": b.display_text} for b in beats],
        "version": {"id": ver.id, "screenplay_json": ver.screenplay_json} if ver else None,
        "scenes": [_scene_out(db, s) for s in scenes],
        "shots": [_shot_out(s) for s in shots],
    }


@router.post("/episodes/{episode_id}/decoupage")
def decoupage(episode_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    if ep.status not in {"approved", "production_ready", "drafted", "reviewed"}:
        raise HTTPException(status_code=400, detail="Approve or draft episode before découpage")
    db.query(VdShot).filter(VdShot.episode_id == ep.id).delete()
    db.query(VdScene).filter(VdScene.episode_id == ep.id).delete()
    ver = db.get(VdEpisodeVersion, ep.current_version_id) if ep.current_version_id else None
    elements = (ver.screenplay_json or {}).get("elements") if ver else []
    headings = [e for e in elements if e.get("element_type") == "scene_heading"] or [{"display_text": "INT. ROOM - DAY"}]
    chars = db.query(VdCharacter).filter(VdCharacter.vd_project_id == ep.vd_project_id).all()
    locked_missing = [c for c in chars if not c.identity_locked]
    scenes_out = []
    for i, h in enumerate(headings[:8], start=1):
        scene = VdScene(id=str(uuid4()), episode_id=ep.id, project_id=ep.project_id, scene_number=i, heading=h.get("display_text") or f"Scene {i}", sort_order=i, duration_seconds=8)
        db.add(scene)
        db.flush()
        for sn in range(1, 3):
            shot = VdShot(
                id=str(uuid4()),
                scene_id=scene.id,
                episode_id=ep.id,
                project_id=ep.project_id,
                shot_number=sn,
                framing="CU" if sn == 1 else "MCU",
                action=f"9:16 {scene.heading} beat {sn}",
                duration_seconds=4,
                character_id=chars[0].id if chars else None,
            )
            db.add(shot)
        scenes_out.append(scene)
    if ep.status == "approved":
        ep.status = "production_ready"
    db.commit()
    return {
        "episode_id": ep.id,
        "scenes": len(scenes_out),
        "identity_warnings": [c.display_name for c in locked_missing],
        "shots": [_shot_out(s) for s in db.query(VdShot).filter(VdShot.episode_id == ep.id).all()],
    }


@router.post("/shots/{shot_id}/generations")
def generate_shot(
    shot_id: str,
    payload: GenerateShotIn,
    user: CurrentUser,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    require_vd()
    require_edit(user)
    shot = db.get(VdShot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    if shot.character_id:
        ch = db.get(VdCharacter, shot.character_id)
        if ch and not ch.identity_locked:
            raise HTTPException(status_code=400, detail=f"Character DNA not locked: {ch.display_name}")
    key = idempotency_key or f"shot-{shot.id}-{payload.capability}"
    existing = db.query(VdGenerationJob).filter(VdGenerationJob.idempotency_key == key).first()
    if existing:
        return _job_out(existing)
    prompt = payload.prompt or shot.action or "Vertical 9:16 cinematic still, Art City drama"
    asset = Asset(
        id=str(uuid4()),
        project_id=shot.project_id,
        asset_type="image" if payload.capability == "image" else "video",
        name=f"VD shot {shot.shot_number}",
        storage_path=f"projects/{shot.project_id}/vd/shots/{shot.id}.json",
        metadata_json={"workflow_key": f"vd.shot.{payload.capability}", "lineage": "vd_generation"},
    )
    body = json.dumps({"prompt": prompt, "aspect": "9:16", "shot_id": shot.id}, ensure_ascii=False).encode("utf-8")
    get_storage().upload_bytes(asset.storage_path, body, "application/json")
    db.add(asset)
    job = VdGenerationJob(
        id=str(uuid4()),
        project_id=shot.project_id,
        shot_id=shot.id,
        episode_id=shot.episode_id,
        workflow_key=f"vd.shot.{payload.capability}",
        capability=payload.capability,
        idempotency_key=key,
        status="succeeded",
        provider="artcity-router",
        model="ac-vd-shot",
        prompt=prompt,
        cost=0,
        result_asset_id=asset.id,
        provenance_json={"schema_version": "1", "workflow_key": f"vd.shot.{payload.capability}", "aspect": "9:16"},
        created_by=user.id,
    )
    db.add(job)
    db.add(CostRecord(project_id=shot.project_id, provider="artcity-router", model="ac-vd-shot", amount=0, currency="USD", note=job.workflow_key))
    shot.selected_asset_id = asset.id
    shot.status = "generated"
    db.commit()
    db.refresh(job)
    return _job_out(job)


@router.get("/generation-jobs/{job_id}")
def get_job(job_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    job = db.get(VdGenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_out(job)


@router.post("/episodes/{episode_id}/assembly")
def assemble(episode_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    shots = db.query(VdShot).filter(VdShot.episode_id == episode_id).order_by(VdShot.shot_number).all()
    manifest = {
        "project_id": ep.project_id,
        "episode_id": ep.id,
        "aspect": "9:16",
        "shots": [{"shot_id": s.id, "asset_id": s.selected_asset_id, "duration_seconds": s.duration_seconds, "framing": s.framing} for s in shots],
    }
    body = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    key = f"projects/{ep.project_id}/vd/handoff/edit/{ep.id}.json"
    get_storage().upload_bytes(key, body, "application/json")
    asset = Asset(id=str(uuid4()), project_id=ep.project_id, asset_type="other", name="VD Edit handoff", storage_path=key, metadata_json={"lineage": "vd_edit_handoff"})
    db.add(asset)
    asm = VdAssembly(id=str(uuid4()), episode_id=ep.id, project_id=ep.project_id, manifest_json=manifest, edit_asset_id=asset.id)
    db.add(asm)
    db.commit()
    return {"ok": True, "assembly_id": asm.id, "asset_id": asset.id, "redirect": "/edit", "manifest": manifest}


@router.post("/episodes/{episode_id}/qc-runs")
def qc_run(episode_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    shots = db.query(VdShot).filter(VdShot.episode_id == episode_id).all()
    findings = []
    for s in shots:
        if s.aspect != "9:16":
            findings.append({"severity": "blocking", "code": "aspect", "message": f"Shot {s.shot_number} is not 9:16"})
        if not s.selected_asset_id:
            findings.append({"severity": "blocking", "code": "missing_media", "message": f"Shot {s.shot_number} has no selected take"})
        if s.duration_seconds <= 0:
            findings.append({"severity": "warning", "code": "duration", "message": f"Shot {s.shot_number} duration"})
    blocking = [f for f in findings if f["severity"] == "blocking"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    run = VdQcRun(
        id=str(uuid4()),
        episode_id=episode_id,
        project_id=ep.project_id,
        passed=len(blocking) == 0 and len(shots) > 0,
        blocking_count=len(blocking),
        warning_count=len(warnings),
        findings_json=findings,
        created_by=user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {"id": run.id, "passed": run.passed, "blocking_count": run.blocking_count, "warning_count": run.warning_count, "findings": findings}


@router.post("/episodes/{episode_id}/localize")
def localize(episode_id: str, payload: LocalizeIn, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_edit(user)
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    track = VdSubtitleTrack(
        id=str(uuid4()),
        episode_id=episode_id,
        project_id=ep.project_id,
        language=payload.language,
        source_version_id=ep.current_version_id,
        kind=payload.kind,
        body=payload.body or (ep.hook or ""),
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    return {"id": track.id, "language": track.language, "kind": track.kind, "source_version_id": track.source_version_id, "body": track.body}


@router.get("/episodes/{episode_id}/localize")
def list_localize(episode_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[dict]:
    require_vd()
    rows = db.query(VdSubtitleTrack).filter(VdSubtitleTrack.episode_id == episode_id).all()
    return [{"id": r.id, "language": r.language, "kind": r.kind, "source_version_id": r.source_version_id, "body": r.body} for r in rows]


@router.post("/episodes/{episode_id}/delivery-packages")
def delivery(episode_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    require_vd()
    require_approve(user)
    ep = db.get(VdEpisode, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    rights = db.query(VdRightsRecord).filter(VdRightsRecord.project_id == ep.project_id, VdRightsRecord.blocks_delivery.is_(True)).all()
    if rights:
        raise HTTPException(status_code=400, detail="Rights state blocks delivery")
    last_qc = db.query(VdQcRun).filter(VdQcRun.episode_id == episode_id).order_by(VdQcRun.created_at.desc()).first()
    if not last_qc or not last_qc.passed:
        raise HTTPException(status_code=400, detail="Cannot mark delivery-ready while blocking QC failures remain")
    tracks = db.query(VdSubtitleTrack).filter(VdSubtitleTrack.episode_id == episode_id).all()
    shots = db.query(VdShot).filter(VdShot.episode_id == episode_id).all()
    manifest = {
        "episode_id": ep.id,
        "project_id": ep.project_id,
        "aspect": "9:16",
        "checksums": {s.id: s.selected_asset_id for s in shots},
        "subtitles": [{"language": t.language, "id": t.id} for t in tracks],
        "qc_run_id": last_qc.id,
    }
    body = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    key = f"projects/{ep.project_id}/vd/delivery/{ep.id}.json"
    get_storage().upload_bytes(key, body, "application/json")
    asset = Asset(id=str(uuid4()), project_id=ep.project_id, asset_type="other", name="VD delivery package", storage_path=key, metadata_json={"lineage": "vd_delivery"})
    db.add(asset)
    pkg = VdDeliveryPackage(id=str(uuid4()), episode_id=ep.id, project_id=ep.project_id, status="ready", manifest_json=manifest, asset_id=asset.id, created_by=user.id)
    db.add(pkg)
    _event(db, project_id=ep.project_id, event_type="vd.delivery.ready", resource_type="vd_delivery_package", resource_id=pkg.id, payload={}, user_id=user.id)
    db.commit()
    return {"id": pkg.id, "status": pkg.status, "asset_id": asset.id, "manifest": manifest}


def _seed_golden_a(db: Session, *, vd: VdProject, ip: VdIpTitle, user_id: str) -> None:
    names = ["دڵخواز", "شیرین", "هێمن", "نازەنین"]
    locs = ["سلێمانی — قاوەخانە", "هەولێر — گرد"]
    for n in names:
        db.add(VdCharacter(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id, display_name=n, locale="ckb-IQ", identity_locked=True, status="approved", bible_json={"role": "lead"}))
    for n in locs:
        db.add(VdLocation(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id, display_name=n, locale="ckb-IQ"))
    db.add(VdRightsRecord(id=str(uuid4()), ip_title_id=ip.id, project_id=vd.project_id, territory="IQ", rights_type="original", status="cleared", created_by=user_id))
    facts = [
        ("hero_name", "دڵخواز"),
        ("city", "سلێمانی"),
        ("secret", "خێزان نهێنی هەیە"),
        ("era", "ئێستا"),
        ("tone", "درامای سۆزدار"),
        ("language", "ckb-IQ"),
        ("antagonist", "هێمن"),
        ("love_interest", "شیرین"),
        ("prop", "ئەڵقەی دایک"),
        ("rule_no_guns", "چەک نیشان نادرێت"),
        ("ending_open", "کۆتایی کراوە"),
        ("format", "9:16"),
    ]
    for k, v in facts:
        db.add(VdCanonFact(id=str(uuid4()), vd_project_id=vd.id, project_id=vd.project_id, fact_key=k, fact_value=v, status="locked", created_by=user_id, approved_by=user_id, entity_type="world"))


def _canon_conflicts(db: Session, vd_id: str, key: str, value: str) -> list[dict]:
    rows = db.query(VdCanonFact).filter(VdCanonFact.vd_project_id == vd_id, VdCanonFact.fact_key == key, VdCanonFact.status.in_(["approved", "locked"])).all()
    out = []
    for r in rows:
        if r.fact_value.strip() != value.strip():
            out.append({"severity": "high", "fact_id": r.id, "existing": r.fact_value, "incoming": value})
    return out


def _count_bible(db: Session, bible_id: str) -> int:
    return db.query(VdStoryBibleVersion).filter(VdStoryBibleVersion.story_bible_id == bible_id).count()


def _project_out(db: Session, vd: VdProject) -> dict:
    ip = db.get(VdIpTitle, vd.current_ip_title_id) if vd.current_ip_title_id else None
    return {
        "id": vd.id,
        "vd_project_id": vd.id,
        "project_id": vd.project_id,
        "title": vd.title,
        "logline": vd.logline,
        "source_type": vd.source_type,
        "production_mode": vd.production_mode,
        "primary_locale": vd.primary_locale,
        "status": vd.status,
        "ip_title": {"id": ip.id, "title": ip.title, "status": ip.status} if ip else None,
    }


def _char_out(r: VdCharacter) -> dict:
    return {"id": r.id, "display_name": r.display_name, "locale": r.locale, "identity_locked": r.identity_locked, "status": r.status, "bible_json": r.bible_json}


def _canon_out(r: VdCanonFact) -> dict:
    return {"id": r.id, "fact_key": r.fact_key, "fact_value": r.fact_value, "status": r.status, "entity_type": r.entity_type, "superseded_by": r.superseded_by}


def _bible_ver(v: VdStoryBibleVersion) -> dict:
    return {"id": v.id, "version_label": v.version_label, "status": v.status, "sections_json": v.sections_json, "approved_at": v.approved_at.isoformat() if v.approved_at else None}


def _bible_out(b: VdStoryBible, v: VdStoryBibleVersion) -> dict:
    return {"id": b.id, "status": b.status, "current_version_id": b.current_version_id, "version": _bible_ver(v)}


def _season_out(db: Session, s: VdSeason) -> dict:
    eps = db.query(VdEpisode).filter(VdEpisode.season_id == s.id).order_by(VdEpisode.sort_order, VdEpisode.episode_number).all()
    return {
        "id": s.id,
        "title": s.title,
        "target_episode_count": s.target_episode_count,
        "status": s.status,
        "episodes": [_ep_out(e) for e in eps],
    }


def _ep_out(e: VdEpisode) -> dict:
    return {
        "id": e.id,
        "episode_number": e.episode_number,
        "title": e.title,
        "hook": e.hook,
        "key_beat": e.key_beat,
        "reveal": e.reveal,
        "cliffhanger": e.cliffhanger,
        "status": e.status,
        "stale": e.stale,
        "stale_reason": e.stale_reason,
        "current_version_id": e.current_version_id,
    }


def _scene_out(db: Session, s: VdScene) -> dict:
    shots = db.query(VdShot).filter(VdShot.scene_id == s.id).order_by(VdShot.shot_number).all()
    return {"id": s.id, "scene_number": s.scene_number, "heading": s.heading, "shots": [_shot_out(x) for x in shots]}


def _shot_out(s: VdShot) -> dict:
    return {
        "id": s.id,
        "shot_number": s.shot_number,
        "framing": s.framing,
        "action": s.action,
        "duration_seconds": s.duration_seconds,
        "aspect": s.aspect,
        "character_id": s.character_id,
        "selected_asset_id": s.selected_asset_id,
        "status": s.status,
        "scene_id": s.scene_id,
    }


def _job_out(j: VdGenerationJob) -> dict:
    return {
        "id": j.id,
        "status": j.status,
        "workflow_key": j.workflow_key,
        "capability": j.capability,
        "provider": j.provider,
        "model": j.model,
        "cost": float(j.cost) if j.cost is not None else 0,
        "result_asset_id": j.result_asset_id,
        "provenance": j.provenance_json,
        "idempotency_key": j.idempotency_key,
    }
