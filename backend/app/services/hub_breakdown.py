"""Scene breakdown proposals from structured scenes."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.models_hub import HubBreakdownItem, HubScene, HubScriptElement
from app.services.hub_i18n_normalize import normalize_for_search

CATEGORIES = (
    "cast",
    "location",
    "prop",
    "wardrobe",
    "vehicle",
    "vfx",
    "sfx",
    "stunt",
    "animal",
    "extra",
)


def propose_breakdown(db: Session, *, project_id: str, script_version_id: str, user_id: str | None) -> list[HubBreakdownItem]:
    # Replace prior AI proposals only
    db.query(HubBreakdownItem).filter(
        HubBreakdownItem.script_version_id == script_version_id,
        HubBreakdownItem.source == "ai",
        HubBreakdownItem.approval_status == "proposed",
    ).delete(synchronize_session=False)
    db.flush()

    scenes = (
        db.query(HubScene)
        .filter(HubScene.script_version_id == script_version_id)
        .order_by(HubScene.sort_order.asc())
        .all()
    )
    created: list[HubBreakdownItem] = []
    for scene in scenes:
        if scene.location_name:
            item = HubBreakdownItem(
                id=str(uuid4()),
                project_id=project_id,
                script_version_id=script_version_id,
                scene_id=scene.id,
                category="location",
                display_text=scene.location_name,
                search_normalized=normalize_for_search(scene.location_name),
                quantity=1,
                approval_status="proposed",
                source="ai",
                metadata_json={"int_ext": scene.int_ext, "time_of_day": scene.time_of_day},
                created_by=user_id,
            )
            db.add(item)
            created.append(item)

        els = (
            db.query(HubScriptElement)
            .filter(
                HubScriptElement.script_version_id == script_version_id,
                HubScriptElement.scene_id == scene.id,
            )
            .order_by(HubScriptElement.position.asc())
            .all()
        )
        seen_cast: set[str] = set()
        for el in els:
            if el.element_type == "character":
                name = (el.display_text or "").strip()
                if name and name not in seen_cast:
                    seen_cast.add(name)
                    item = HubBreakdownItem(
                        id=str(uuid4()),
                        project_id=project_id,
                        script_version_id=script_version_id,
                        scene_id=scene.id,
                        category="cast",
                        display_text=name,
                        search_normalized=normalize_for_search(name),
                        quantity=1,
                        approval_status="proposed",
                        source="ai",
                        metadata_json={},
                        created_by=user_id,
                    )
                    db.add(item)
                    created.append(item)
            if el.element_type == "action":
                text = (el.display_text or "").lower()
                if any(k in text for k in ("gun", "چەک", "sword", "knife")):
                    item = HubBreakdownItem(
                        id=str(uuid4()),
                        project_id=project_id,
                        script_version_id=script_version_id,
                        scene_id=scene.id,
                        category="prop",
                        display_text="Prop cue (review)",
                        search_normalized=normalize_for_search("prop cue"),
                        quantity=1,
                        approval_status="proposed",
                        source="ai",
                        metadata_json={"from_action": el.display_text[:200]},
                        created_by=user_id,
                    )
                    db.add(item)
                    created.append(item)
                if any(k in text for k in ("rain", "باران", "explosion", "fire", "ئاگر")):
                    item = HubBreakdownItem(
                        id=str(uuid4()),
                        project_id=project_id,
                        script_version_id=script_version_id,
                        scene_id=scene.id,
                        category="sfx",
                        display_text="SFX cue (review)",
                        search_normalized=normalize_for_search("sfx cue"),
                        quantity=1,
                        approval_status="proposed",
                        source="ai",
                        metadata_json={"from_action": el.display_text[:200]},
                        created_by=user_id,
                    )
                    db.add(item)
                    created.append(item)
    db.flush()
    return created
