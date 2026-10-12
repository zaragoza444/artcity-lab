"""Append-only communications audit. Secrets and message bodies are not stored."""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models_comm import CommAuditLog

_REDACT = {"phone", "phone_e164", "body", "body_text", "token", "access_token", "authorization", "secret", "to"}


def ip_hash(ip: str | None) -> str | None:
    if not ip:
        return None
    settings = get_settings()
    material = f"{settings.secret_key}:{ip}".encode()
    return hashlib.sha256(material).hexdigest()


def redact(metadata: dict[str, Any] | None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key.lower() in _REDACT:
            clean[key] = "[redacted]"
        elif isinstance(value, dict):
            clean[key] = redact(value)
        else:
            clean[key] = value
    return clean


def audit(
    db: Session,
    *,
    actor_id: str | None,
    action: str,
    object_type: str,
    object_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip: str | None = None,
) -> CommAuditLog:
    row = CommAuditLog(
        actor_id=actor_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        metadata_json=redact(metadata),
        ip_hash=ip_hash(ip),
    )
    db.add(row)
    db.flush()
    return row
