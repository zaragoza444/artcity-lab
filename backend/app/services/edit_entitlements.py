"""Art City Edit — entitlement and workspace access checks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import EDIT_APPROVAL_ROLES, EditAccountState, UserRole
from app.models import User
from app.models_edit import (
    EditEntitlement,
    EditMembership,
    EditOrganisation,
    EditPlan,
    EditSubscription,
    EditUsageRecord,
    EditWorkspace,
)


def is_platform_admin(user: User) -> bool:
    role = getattr(user, "role", None)
    if isinstance(role, UserRole):
        return role in EDIT_APPROVAL_ROLES
    return role in {UserRole.SUPER_ADMIN.value, UserRole.ADMINISTRATOR.value}


def get_user_memberships(db: Session, user_id: str) -> list[EditMembership]:
    return (
        db.query(EditMembership)
        .filter(EditMembership.user_id == user_id, EditMembership.status == "active")
        .all()
    )


def require_workspace_access(
    db: Session,
    user: User,
    workspace_id: str,
    roles: Optional[Sequence[str]] = None,
) -> EditMembership:
    if is_platform_admin(user):
        workspace = db.get(EditWorkspace, workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        membership = (
            db.query(EditMembership)
            .filter(
                EditMembership.user_id == user.id,
                EditMembership.workspace_id == workspace_id,
                EditMembership.status == "active",
            )
            .first()
        )
        if membership:
            return membership
        # Synthetic admin membership for platform operators
        return EditMembership(
            id=str(uuid4()),
            organisation_id=workspace.organisation_id,
            workspace_id=workspace_id,
            user_id=user.id,
            role="admin",
            status="active",
        )

    q = db.query(EditMembership).filter(
        EditMembership.user_id == user.id,
        EditMembership.status == "active",
        EditMembership.workspace_id == workspace_id,
    )
    membership = q.first()
    if not membership:
        # Org-level membership without workspace scoping
        workspace = db.get(EditWorkspace, workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        membership = (
            db.query(EditMembership)
            .filter(
                EditMembership.user_id == user.id,
                EditMembership.organisation_id == workspace.organisation_id,
                EditMembership.status == "active",
                EditMembership.workspace_id.is_(None),
            )
            .first()
        )
    if not membership:
        raise ValueError("Workspace access denied")
    if roles and membership.role not in roles and not is_platform_admin(user):
        raise ValueError(f"Role required: {', '.join(roles)}")
    return membership


def org_is_processable(db: Session, org_id: str) -> bool:
    org = db.get(EditOrganisation, org_id)
    if not org or org.status != EditAccountState.ACTIVE.value:
        return False
    sub = (
        db.query(EditSubscription)
        .filter(
            EditSubscription.organisation_id == org_id,
            EditSubscription.status == "active",
        )
        .order_by(EditSubscription.created_at.desc())
        .first()
    )
    return sub is not None


def assert_entitled(
    db: Session,
    organisation_id: str,
    feature: str = "processing_minutes",
    amount: float = 0,
) -> EditEntitlement:
    org = db.get(EditOrganisation, organisation_id)
    if not org:
        raise ValueError("Organisation not found")
    if org.status in {
        EditAccountState.SUSPENDED.value,
        EditAccountState.TERMINATED.value,
        EditAccountState.CANCELLED.value,
        EditAccountState.REJECTED.value,
    }:
        raise ValueError(f"Organisation is {org.status}")
    if not org_is_processable(db, organisation_id):
        raise ValueError("Organisation is not processable — inactive subscription or status")

    entitlement = (
        db.query(EditEntitlement)
        .filter(
            EditEntitlement.organisation_id == organisation_id,
            EditEntitlement.feature == feature,
        )
        .order_by(EditEntitlement.created_at.desc())
        .first()
    )
    if not entitlement:
        raise ValueError(f"No entitlement for feature '{feature}'")
    if entitlement.limit_value >= 0 and (entitlement.used_value + amount) > entitlement.limit_value:
        raise ValueError(f"Entitlement limit exceeded for '{feature}'")
    return entitlement


def record_usage(
    db: Session,
    organisation_id: str,
    metric: str,
    quantity: float,
    cost_usd: float = 0,
    workspace_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> EditUsageRecord:
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    record = EditUsageRecord(
        id=str(uuid4()),
        organisation_id=organisation_id,
        workspace_id=workspace_id,
        job_id=job_id,
        metric=metric,
        quantity=quantity,
        cost_usd=cost_usd,
        billing_period=period,
    )
    db.add(record)

    entitlement = (
        db.query(EditEntitlement)
        .filter(
            EditEntitlement.organisation_id == organisation_id,
            EditEntitlement.feature == metric,
        )
        .order_by(EditEntitlement.created_at.desc())
        .first()
    )
    if entitlement:
        entitlement.used_value = float(entitlement.used_value or 0) + float(quantity)
        db.add(entitlement)

    db.flush()
    return record


def issue_plan_entitlements(
    db: Session,
    organisation_id: str,
    plan: EditPlan,
) -> list[EditEntitlement]:
    limits = plan.limits_json or {}
    now = datetime.now(timezone.utc)
    issued: list[EditEntitlement] = []
    for feature, limit_value in limits.items():
        try:
            numeric = float(limit_value)
        except (TypeError, ValueError):
            continue
        existing = (
            db.query(EditEntitlement)
            .filter(
                EditEntitlement.organisation_id == organisation_id,
                EditEntitlement.feature == feature,
            )
            .order_by(EditEntitlement.created_at.desc())
            .first()
        )
        if existing:
            existing.limit_value = numeric
            existing.used_value = 0
            existing.effective_from = now
            db.add(existing)
            issued.append(existing)
        else:
            ent = EditEntitlement(
                id=str(uuid4()),
                organisation_id=organisation_id,
                feature=feature,
                limit_value=numeric,
                used_value=0,
                reset_rule="monthly",
                effective_from=now,
            )
            db.add(ent)
            issued.append(ent)
    db.flush()
    return issued
