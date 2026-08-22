"""Parse screenplay elements into Scene objects."""

from __future__ import annotations

import re
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models_hub import HubCharacter, HubLocation, HubScene, HubScriptElement
from app.services.hub_i18n_normalize import estimate_page_eighths, normalize_for_search

SCENE_HEADING_RE = re.compile(
    r"^\s*(INT\.?|EXT\.?|I/E\.?|E/I\.?)\s*(.*?)(?:\s*[-–—]\s*(.+))?\s*$",
    re.IGNORECASE,
)


def parse_heading(text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    m = SCENE_HEADING_RE.match(text or "")
    if not m:
        return None, text.strip() or None, None
    int_ext = (m.group(1) or "").upper().replace(".", "")
    if int_ext in {"I/E", "E/I"}:
        int_ext = "I/E"
    location = (m.group(2) or "").strip() or None
    tod = (m.group(3) or "").strip() or None
    return int_ext, location, tod


def rebuild_scenes_from_elements(
    db: Session,
    *,
    project_id: str,
    script_id: str,
    script_version_id: str,
) -> list[HubScene]:
    # Clear prior scenes for this version (elements keep scene_id null until reassigned)
    db.query(HubScriptElement).filter(HubScriptElement.script_version_id == script_version_id).update(
        {"scene_id": None}, synchronize_session=False
    )
    db.query(HubScene).filter(HubScene.script_version_id == script_version_id).delete(synchronize_session=False)
    db.flush()

    elements = (
        db.query(HubScriptElement)
        .filter(HubScriptElement.script_version_id == script_version_id)
        .order_by(HubScriptElement.position.asc())
        .all()
    )

    scenes: list[HubScene] = []
    current: Optional[HubScene] = None
    scene_texts: list[str] = []
    scene_idx = 0

    def flush_scene() -> None:
        nonlocal current, scene_texts
        if current is not None:
            current.page_eighths = estimate_page_eighths(scene_texts)
            db.add(current)
        scene_texts = []

    for el in elements:
        if el.element_type == "scene_heading":
            flush_scene()
            scene_idx += 1
            int_ext, location_name, tod = parse_heading(el.display_text)
            location_id = None
            if location_name:
                loc = (
                    db.query(HubLocation)
                    .filter(
                        HubLocation.project_id == project_id,
                        HubLocation.display_name == location_name,
                    )
                    .first()
                )
                if not loc:
                    loc = HubLocation(
                        id=str(uuid4()),
                        project_id=project_id,
                        script_id=script_id,
                        display_name=location_name,
                        search_normalized=normalize_for_search(location_name),
                        bible_json={},
                    )
                    db.add(loc)
                    db.flush()
                location_id = loc.id
            current = HubScene(
                id=str(uuid4()),
                script_version_id=script_version_id,
                project_id=project_id,
                scene_number=str(scene_idx),
                int_ext=int_ext,
                location_name=location_name,
                time_of_day=tod,
                heading_display=el.display_text,
                page_eighths=8,
                sort_order=scene_idx,
                location_id=location_id,
                metadata_json={},
            )
            db.add(current)
            db.flush()
            el.scene_id = current.id
            scenes.append(current)
            scene_texts = [el.display_text]
        else:
            if current is None:
                scene_idx += 1
                current = HubScene(
                    id=str(uuid4()),
                    script_version_id=script_version_id,
                    project_id=project_id,
                    scene_number=str(scene_idx),
                    heading_display="UNTITLED",
                    page_eighths=8,
                    sort_order=scene_idx,
                    metadata_json={},
                )
                db.add(current)
                db.flush()
                scenes.append(current)
            el.scene_id = current.id
            scene_texts.append(el.display_text or "")
            if el.element_type == "character" and (el.display_text or "").strip():
                name = el.display_text.strip()
                ch = (
                    db.query(HubCharacter)
                    .filter(HubCharacter.project_id == project_id, HubCharacter.display_name == name)
                    .first()
                )
                if not ch:
                    ch = HubCharacter(
                        id=str(uuid4()),
                        project_id=project_id,
                        script_id=script_id,
                        display_name=name,
                        search_normalized=normalize_for_search(name),
                        bible_json={},
                    )
                    db.add(ch)
                    db.flush()
                el.character_id = ch.id
            db.add(el)

    flush_scene()
    db.flush()
    return scenes
