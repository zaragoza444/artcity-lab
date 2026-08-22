"""Vertical Drama entitlements and RBAC."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.enums import UserRole
from app.models import User

EPISODE_TRANSITIONS = {
    "planned": {"drafted"},
    "drafted": {"reviewed", "planned"},
    "reviewed": {"approved", "drafted"},
    "approved": {"production_ready"},
    "production_ready": {"locked"},
    "locked": set(),
}


def vd_enabled() -> bool:
    return bool(get_settings().vd_feature_enabled)


def require_vd() -> None:
    if not vd_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vertical Drama is not entitled on this deployment",
        )


def _role(user: User) -> str:
    role = getattr(user, "role", None)
    return role.value if isinstance(role, UserRole) else str(role or "")


def can_edit(user: User) -> bool:
    return _role(user) not in {UserRole.VIEWER.value, "viewer"}


def can_approve(user: User) -> bool:
    return _role(user) in {
        UserRole.SUPER_ADMIN.value,
        UserRole.ADMINISTRATOR.value,
        UserRole.PRODUCER.value,
        UserRole.PROJECT_MANAGER.value,
        UserRole.CREATIVE_DIRECTOR.value,
        UserRole.EDITOR.value,
        "super_admin",
        "administrator",
        "producer",
        "project_manager",
        "creative_director",
        "editor",
    }


def require_edit(user: User) -> None:
    if not can_edit(user) or not getattr(user, "is_active", True):
        raise HTTPException(status_code=403, detail="vertical_drama.edit denied")


def require_approve(user: User) -> None:
    if not can_approve(user):
        raise HTTPException(status_code=403, detail="vertical_drama.approve denied")


def assert_transition(current: str, nxt: str) -> None:
    allowed = EPISODE_TRANSITIONS.get(current, set())
    if nxt not in allowed:
        raise ValueError(f"Invalid episode transition {current} → {nxt}")
