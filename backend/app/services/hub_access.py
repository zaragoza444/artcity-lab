"""Production Hub entitlements and permission helpers."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.enums import UserRole
from app.models import User


HUB_MODULES = ("script", "storyboard", "budget", "call")


def hub_features() -> dict[str, bool]:
    s = get_settings()
    return {
        "script": bool(s.hub_feature_script),
        "storyboard": bool(s.hub_feature_storyboard),
        "budget": bool(s.hub_feature_budget),
        "call": bool(s.hub_feature_call),
    }


def require_hub_module(module: str) -> None:
    features = hub_features()
    if module not in features:
        raise HTTPException(status_code=400, detail=f"Unknown hub module: {module}")
    if not features[module]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Hub module '{module}' is not entitled on this deployment",
        )


def is_elevated(user: User) -> bool:
    role = getattr(user, "role", None)
    if isinstance(role, UserRole):
        return role in {UserRole.SUPER_ADMIN, UserRole.ADMINISTRATOR, UserRole.PRODUCER}
    return role in {
        UserRole.SUPER_ADMIN.value,
        UserRole.ADMINISTRATOR.value,
        UserRole.PRODUCER.value,
        UserRole.PROJECT_MANAGER.value,
        UserRole.CREATIVE_DIRECTOR.value,
        UserRole.WRITER.value,
        UserRole.EDITOR.value,
    }


def require_script_edit(user: User) -> None:
    if not is_elevated(user) and getattr(user, "role", None) not in {
        UserRole.WRITER.value,
        UserRole.EDITOR.value,
        "writer",
        "editor",
    }:
        # Authenticated users with active accounts can edit scripts in MVP;
        # platform admins always can.
        if not getattr(user, "is_active", True):
            raise HTTPException(status_code=403, detail="script.edit denied")


def require_script_lock(user: User) -> None:
    role = getattr(user, "role", None)
    allowed = {
        UserRole.SUPER_ADMIN.value,
        UserRole.ADMINISTRATOR.value,
        UserRole.PRODUCER.value,
        UserRole.PROJECT_MANAGER.value,
        UserRole.CREATIVE_DIRECTOR.value,
        "super_admin",
        "administrator",
        "producer",
        "project_manager",
        "creative_director",
    }
    if role not in allowed and not (
        isinstance(role, UserRole) and role.value in allowed
    ):
        raise HTTPException(status_code=403, detail="script.lock denied")
