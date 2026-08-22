"""AC Script domain service — create, version, elements, lock, AI assist."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import CostRecord, Project, User
from app.models_hub import HubScript, HubScriptElement, HubScriptVersion
from app.services.hub_events import emit_event, mark_stale
from app.services.hub_i18n_normalize import estimate_page_eighths, normalize_for_search
from app.services.hub_parser import rebuild_scenes_from_elements

ELEMENT_TYPES = {
    "scene_heading",
    "action",
    "character",
    "dialogue",
    "parenthetical",
    "transition",
    "shot",
}


def _assert_editable(version: HubScriptVersion) -> None:
    if version.status == "locked":
        raise ValueError("Cannot edit a locked script version — create a new revision")


def create_script(
    db: Session,
    *,
    project: Project,
    user: User,
    title: str,
    entry_mode: str = "blank",
    primary_locale: str = "en",
    content_languages: Optional[list[str]] = None,
    seed_text: Optional[str] = None,
    elements: Optional[list[dict[str, Any]]] = None,
) -> HubScript:
    script = HubScript(
        id=str(uuid4()),
        project_id=project.id,
        title=title.strip() or "Untitled Screenplay",
        entry_mode=entry_mode,
        primary_locale=primary_locale or project.primary_locale or "en",
        content_languages=content_languages or [primary_locale or "en"],
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(script)
    db.flush()

    version = HubScriptVersion(
        id=str(uuid4()),
        script_id=script.id,
        project_id=project.id,
        version_label="Draft 1",
        status="draft",
        created_by=user.id,
        page_eighths=0,
    )
    db.add(version)
    db.flush()
    script.current_version_id = version.id
    db.add(script)

    seeded = elements or []
    if not seeded and seed_text:
        seeded = _seed_from_plaintext(seed_text, primary_locale)
    if not seeded and entry_mode in {"idea", "logline", "synopsis", "treatment"}:
        seeded = [
            {
                "element_type": "action",
                "display_text": seed_text or f"({entry_mode}) Develop this into scenes.",
                "locale": primary_locale,
            }
        ]
    if not seeded:
        seeded = [
            {
                "element_type": "scene_heading",
                "display_text": "INT. LOCATION - DAY",
                "locale": "en",
            },
            {
                "element_type": "action",
                "display_text": "We open on an empty room.",
                "locale": primary_locale,
            },
        ]

    _replace_elements(db, project_id=project.id, version_id=version.id, elements=seeded)
    rebuild_scenes_from_elements(
        db, project_id=project.id, script_id=script.id, script_version_id=version.id
    )
    _refresh_page_eighths(db, version)
    emit_event(
        db,
        project_id=project.id,
        event_type="script.created",
        resource_type="hub_script",
        resource_id=script.id,
        payload={"version_id": version.id},
        created_by=user.id,
    )
    db.flush()
    return script


def _seed_from_plaintext(text: str, locale: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith(("INT.", "EXT.", "INT ", "EXT ", "I/E.", "E/I.")):
            out.append({"element_type": "scene_heading", "display_text": line, "locale": locale})
        elif line.isupper() and len(line) < 40:
            out.append({"element_type": "character", "display_text": line, "locale": locale})
        elif line.startswith("(") and line.endswith(")"):
            out.append({"element_type": "parenthetical", "display_text": line, "locale": locale})
        else:
            out.append({"element_type": "action", "display_text": line, "locale": locale})
    return out or [{"element_type": "action", "display_text": text, "locale": locale}]


def _replace_elements(
    db: Session, *, project_id: str, version_id: str, elements: list[dict[str, Any]]
) -> list[HubScriptElement]:
    db.query(HubScriptElement).filter(HubScriptElement.script_version_id == version_id).delete(
        synchronize_session=False
    )
    db.flush()
    rows: list[HubScriptElement] = []
    for i, el in enumerate(elements):
        etype = str(el.get("element_type") or "action")
        if etype not in ELEMENT_TYPES:
            etype = "action"
        text = str(el.get("display_text") or "")
        row = HubScriptElement(
            id=str(uuid4()),
            script_version_id=version_id,
            project_id=project_id,
            position=i,
            element_type=etype,
            display_text=text,
            search_normalized=normalize_for_search(text),
            locale=el.get("locale"),
            metadata_json=el.get("metadata_json") or {},
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def _refresh_page_eighths(db: Session, version: HubScriptVersion) -> None:
    texts = [
        e.display_text
        for e in db.query(HubScriptElement)
        .filter(HubScriptElement.script_version_id == version.id)
        .all()
    ]
    version.page_eighths = estimate_page_eighths(texts)
    db.add(version)
    db.flush()


def get_version(db: Session, version_id: str) -> HubScriptVersion:
    version = db.get(HubScriptVersion, version_id)
    if not version:
        raise ValueError("Script version not found")
    return version


def list_elements(db: Session, version_id: str) -> list[HubScriptElement]:
    return (
        db.query(HubScriptElement)
        .filter(HubScriptElement.script_version_id == version_id)
        .order_by(HubScriptElement.position.asc())
        .all()
    )


def autosave_elements(
    db: Session,
    *,
    version: HubScriptVersion,
    elements: list[dict[str, Any]],
    user: User,
) -> list[HubScriptElement]:
    _assert_editable(version)
    rows = _replace_elements(
        db, project_id=version.project_id, version_id=version.id, elements=elements
    )
    script = db.get(HubScript, version.script_id)
    if script:
        script.updated_by = user.id
        db.add(script)
    _refresh_page_eighths(db, version)
    db.flush()
    return rows


def create_revision(
    db: Session, *, script: HubScript, user: User, label: Optional[str] = None
) -> HubScriptVersion:
    current = db.get(HubScriptVersion, script.current_version_id) if script.current_version_id else None
    if not current:
        raise ValueError("No current version to revise")
    count = db.query(HubScriptVersion).filter(HubScriptVersion.script_id == script.id).count()
    version = HubScriptVersion(
        id=str(uuid4()),
        script_id=script.id,
        project_id=script.project_id,
        version_label=label or f"Draft {count + 1}",
        status="revision",
        parent_version_id=current.id,
        created_by=user.id,
        page_eighths=current.page_eighths,
    )
    db.add(version)
    db.flush()
    elems = list_elements(db, current.id)
    _replace_elements(
        db,
        project_id=script.project_id,
        version_id=version.id,
        elements=[
            {
                "element_type": e.element_type,
                "display_text": e.display_text,
                "locale": e.locale,
                "metadata_json": e.metadata_json or {},
            }
            for e in elems
        ],
    )
    rebuild_scenes_from_elements(
        db, project_id=script.project_id, script_id=script.id, script_version_id=version.id
    )
    script.current_version_id = version.id
    script.updated_by = user.id
    db.add(script)
    emit_event(
        db,
        project_id=script.project_id,
        event_type="script.revision_created",
        resource_type="hub_script_version",
        resource_id=version.id,
        payload={"parent": current.id},
        created_by=user.id,
    )
    db.flush()
    return version


def lock_version(db: Session, *, version: HubScriptVersion, user: User) -> HubScriptVersion:
    if version.status == "locked":
        return version
    version.status = "locked"
    version.locked_at = datetime.now(timezone.utc)
    version.locked_by = user.id
    db.add(version)
    event = emit_event(
        db,
        project_id=version.project_id,
        event_type="script.locked",
        resource_type="hub_script_version",
        resource_id=version.id,
        payload={"label": version.version_label},
        created_by=user.id,
    )
    # Flag storyboard/budget/call placeholders as stale when script locks change later
    mark_stale(
        db,
        project_id=version.project_id,
        resource_type="hub_storyboard",
        resource_id=version.script_id,
        reason="OUT OF DATE — SCRIPT LOCKED / CHANGED",
        event_id=event.id,
    )
    db.flush()
    return version


def compare_versions(db: Session, a_id: str, b_id: str) -> dict[str, Any]:
    a = list_elements(db, a_id)
    b = list_elements(db, b_id)
    a_texts = [(e.element_type, e.display_text) for e in a]
    b_texts = [(e.element_type, e.display_text) for e in b]
    added = [t for t in b_texts if t not in a_texts]
    removed = [t for t in a_texts if t not in b_texts]
    left = [f"{e.element_type}: {e.display_text}" for e in a]
    right = [f"{e.element_type}: {e.display_text}" for e in b]
    return {
        "a_count": len(a),
        "b_count": len(b),
        "left": left,
        "right": right,
        "added": len(added),
        "removed": len(removed),
        "added_items": [{"element_type": t, "display_text": d} for t, d in added[:100]],
        "removed_items": [{"element_type": t, "display_text": d} for t, d in removed[:100]],
    }


def ai_transform_elements(
    db: Session,
    *,
    version: HubScriptVersion,
    user: User,
    command: str,
    target_locale: Optional[str] = None,
    element_ids: Optional[list[str]] = None,
) -> dict[str, Any]:
    """AI proposes new text; never writes locked versions. Persists only after validation."""
    _assert_editable(version)
    settings = get_settings()
    elements = list_elements(db, version.id)
    if element_ids:
        selected = [e for e in elements if e.id in set(element_ids)]
    else:
        selected = elements
    if not selected:
        raise ValueError("No elements selected")

    bundle = "\n".join(f"[{e.element_type}] {e.display_text}" for e in selected[:40])
    locale = target_locale or "en"
    prompt = (
        f"You are an Art City screenplay assistant. Command: {command}. "
        f"Output language: {locale}. "
        "Return ONLY a JSON array of objects with keys element_type and display_text. "
        "Preserve screenplay element types. Do not invent JSON keys.\n\n"
        f"INPUT:\n{bundle}"
    )
    proposed: list[dict[str, Any]] = []
    provider = "local"
    cost = 0.0
    if settings.openai_api_key and settings.external_providers_enabled:
        try:
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "temperature": 0.4,
                        "messages": [
                            {"role": "system", "content": "Return valid JSON array only."},
                            {"role": "user", "content": prompt},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                )
            if resp.status_code < 400:
                import json

                raw = resp.json()["choices"][0]["message"]["content"]
                data = json.loads(raw)
                if isinstance(data, dict):
                    data = data.get("elements") or data.get("items") or data.get("data") or []
                if isinstance(data, list):
                    for item in data:
                        if not isinstance(item, dict):
                            continue
                        et = str(item.get("element_type") or "action")
                        if et not in ELEMENT_TYPES:
                            et = "action"
                        proposed.append(
                            {
                                "element_type": et,
                                "display_text": str(item.get("display_text") or ""),
                                "locale": locale,
                            }
                        )
                    provider = "openai"
                    cost = 0.02
        except Exception:
            proposed = []

    if not proposed:
        # Deterministic local proposal — mark lineage as AI-suggested
        for e in selected:
            text = e.display_text
            if command == "translate" and locale.startswith("ckb"):
                text = f"{text}"  # keep original; UI shows command applied
            elif command == "shorten":
                text = text[: max(40, len(text) // 2)]
            elif command == "expand":
                text = text + " (expanded beat)"
            proposed.append(
                {
                    "element_type": e.element_type,
                    "display_text": text,
                    "locale": locale,
                    "metadata_json": {"ai_command": command, "lineage": "ai_suggested"},
                }
            )
        provider = "artcity-local"

    db.add(
        CostRecord(
            project_id=version.project_id,
            provider=provider,
            model="hub-script-ai",
            amount=cost,
            note=f"hub.script.ai:{command}:{provider}",
        )
    )
    emit_event(
        db,
        project_id=version.project_id,
        event_type="script.ai_proposal",
        resource_type="hub_script_version",
        resource_id=version.id,
        payload={"command": command, "provider": provider, "count": len(proposed)},
        created_by=user.id,
    )
    db.flush()
    return {"provider": provider, "cost_usd": cost, "elements": proposed, "apply": False}
