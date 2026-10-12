"""Communications roles. Studio roles are not reused except to bootstrap the first super admin."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.models_comm import CommMembership

ROLES = {
    "super_admin",
    "marketing_manager",
    "campaign_approver",
    "operator",
    "inbox_agent",
    "analyst",
    "auditor",
}

_PERMS: dict[str, set[str]] = {
    "overview.read": ROLES,
    "contacts.read": ROLES - {"auditor"},
    "contacts.write": {"super_admin", "marketing_manager"},
    "contacts.consent": {"super_admin", "marketing_manager"},
    "contacts.optout": {"super_admin", "marketing_manager", "operator", "inbox_agent"},
    "contacts.export": {"super_admin", "marketing_manager", "analyst"},
    "segments.write": {"super_admin", "marketing_manager"},
    "templates.sync": {"super_admin", "marketing_manager"},
    "campaigns.create": {"super_admin", "marketing_manager"},
    "campaigns.approve": {"super_admin", "campaign_approver"},
    "campaigns.operate": {"super_admin", "operator", "marketing_manager"},
    "inbox.read": {"super_admin", "inbox_agent", "operator", "marketing_manager", "auditor"},
    "inbox.reply": {"super_admin", "inbox_agent", "operator"},
    "billing.read": {"super_admin", "analyst", "auditor", "marketing_manager", "campaign_approver"},
    "billing.write": {"super_admin"},
    "admin.secrets": {"super_admin"},
    "admin.members": {"super_admin"},
    "audit.read": {"super_admin", "auditor"},
}


def allows(role: str, perm: str) -> bool:
    return role in _PERMS.get(perm, set())


def require_membership(membership: CommMembership | None, perm: str) -> CommMembership:
    if membership is None or not membership.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Communications role required")
    if not allows(membership.role, perm):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient communications role")
    return membership


def require_totp(membership: CommMembership, code: str | None) -> None:
    if not membership.totp_enabled or not membership.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "mfa_required", "message": "Enroll an authenticator before changing billing or secrets"},
        )
    import pyotp

    if not code or not pyotp.TOTP(membership.totp_secret).verify(code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authenticator code")
