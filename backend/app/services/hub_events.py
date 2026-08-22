"""Domain events and stale-dependency flags for Production Hub."""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models_hub import HubDomainEvent, HubStaleFlag


def emit_event(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    resource_type: str,
    resource_id: str,
    payload: Optional[dict[str, Any]] = None,
    created_by: Optional[str] = None,
) -> HubDomainEvent:
    event = HubDomainEvent(
        id=str(uuid4()),
        project_id=project_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        payload_json=payload or {},
        created_by=created_by,
    )
    db.add(event)
    db.flush()
    return event


def mark_stale(
    db: Session,
    *,
    project_id: str,
    resource_type: str,
    resource_id: str,
    reason: str,
    event_id: Optional[str] = None,
) -> HubStaleFlag:
    existing = (
        db.query(HubStaleFlag)
        .filter(
            HubStaleFlag.project_id == project_id,
            HubStaleFlag.resource_type == resource_type,
            HubStaleFlag.resource_id == resource_id,
        )
        .first()
    )
    if existing:
        existing.active = True
        existing.reason = reason
        existing.caused_by_event_id = event_id
        existing.resolved_at = None
        db.add(existing)
        db.flush()
        return existing
    flag = HubStaleFlag(
        id=str(uuid4()),
        project_id=project_id,
        resource_type=resource_type,
        resource_id=resource_id,
        reason=reason,
        active=True,
        caused_by_event_id=event_id,
    )
    db.add(flag)
    db.flush()
    return flag


def resolve_stale(db: Session, project_id: str, resource_type: str, resource_id: str) -> None:
    from datetime import datetime, timezone

    flag = (
        db.query(HubStaleFlag)
        .filter(
            HubStaleFlag.project_id == project_id,
            HubStaleFlag.resource_type == resource_type,
            HubStaleFlag.resource_id == resource_id,
            HubStaleFlag.active.is_(True),
        )
        .first()
    )
    if flag:
        flag.active = False
        flag.resolved_at = datetime.now(timezone.utc)
        db.add(flag)
        db.flush()
