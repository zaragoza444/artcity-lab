"""Art City Edit — access applications, plans, and subscription activation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import EditAccountState, EditWorkspaceRole
from app.models import User
from app.models_edit import (
    EditAccessApplication,
    EditMembership,
    EditOrganisation,
    EditPlan,
    EditSubscription,
    EditWorkspace,
)
from app.services.audit import write_audit
from app.services.edit_entitlements import is_platform_admin, issue_plan_entitlements

DEFAULT_PLANS: list[dict[str, Any]] = [
    {
        "code": "creator",
        "name": "Creator",
        "description": "Approved individual creator or small team.",
        "price_usd_monthly": 49.0,
        "feature_flags": {"exports": "standard", "review": "basic"},
        "limits_json": {
            "processing_minutes": 120,
            "storage_gb": 50,
            "workspaces": 1,
            "seats": 3,
            "exports_per_month": 40,
        },
    },
    {
        "code": "professional",
        "name": "Professional",
        "description": "Production company, agency, label or media team.",
        "price_usd_monthly": 199.0,
        "feature_flags": {"exports": "advanced", "review": "advanced", "analytics": True},
        "limits_json": {
            "processing_minutes": 600,
            "storage_gb": 500,
            "workspaces": 5,
            "seats": 15,
            "exports_per_month": 200,
        },
    },
    {
        "code": "broadcast",
        "name": "Broadcast / Enterprise",
        "description": "Broadcaster, archive, government or large organisation.",
        "price_usd_monthly": None,
        "feature_flags": {"exports": "broadcast", "sso": True, "audit_export": True},
        "limits_json": {
            "processing_minutes": 5000,
            "storage_gb": 5000,
            "workspaces": 50,
            "seats": 100,
            "exports_per_month": 2000,
        },
    },
    {
        "code": "internal_art_city",
        "name": "Internal Art City",
        "description": "Art City Group brands and approved departments.",
        "price_usd_monthly": 0.0,
        "feature_flags": {"exports": "broadcast", "internal": True},
        "limits_json": {
            "processing_minutes": 100000,
            "storage_gb": 100000,
            "workspaces": 100,
            "seats": 500,
            "exports_per_month": 100000,
        },
    },
]


def list_plans(db: Session) -> list[EditPlan]:
    return db.query(EditPlan).filter(EditPlan.is_active.is_(True)).order_by(EditPlan.name).all()


def ensure_default_plans(db: Session) -> list[EditPlan]:
    plans: list[EditPlan] = []
    for spec in DEFAULT_PLANS:
        plan = db.query(EditPlan).filter(EditPlan.code == spec["code"]).first()
        if plan:
            plan.name = spec["name"]
            plan.description = spec["description"]
            plan.feature_flags = spec["feature_flags"]
            plan.limits_json = spec["limits_json"]
            plan.price_usd_monthly = spec["price_usd_monthly"]
            plan.is_active = True
        else:
            plan = EditPlan(
                id=str(uuid4()),
                code=spec["code"],
                name=spec["name"],
                description=spec["description"],
                feature_flags=spec["feature_flags"],
                limits_json=spec["limits_json"],
                price_usd_monthly=spec["price_usd_monthly"],
                is_active=True,
            )
            db.add(plan)
        plans.append(plan)
    db.flush()
    return plans


def submit_application(db: Session, user: User, payload: dict[str, Any]) -> EditAccessApplication:
    org_name = (payload.get("organisation_name") or "").strip()
    if not org_name:
        raise ValueError("organisation_name is required")
    if not payload.get("declarations_accepted"):
        raise ValueError("declarations_accepted must be true")

    plan_code = payload.get("requested_plan_code") or "creator"
    ensure_default_plans(db)
    plan = db.query(EditPlan).filter(EditPlan.code == plan_code, EditPlan.is_active.is_(True)).first()
    if not plan:
        raise ValueError(f"Unknown plan: {plan_code}")

    org = EditOrganisation(
        id=str(uuid4()),
        legal_name=org_name,
        display_name=payload.get("display_name") or org_name,
        country=payload.get("country"),
        org_type=payload.get("business_type") or "creator",
        status=EditAccountState.PENDING_ART_CITY_REVIEW.value,
        owner_user_id=user.id,
        website=payload.get("website"),
        ai_training_opt_in=bool(payload.get("ai_training_opt_in", False)),
        metadata_json=payload.get("metadata_json") or {},
    )
    db.add(org)
    db.flush()

    application = EditAccessApplication(
        id=str(uuid4()),
        organisation_id=org.id,
        applicant_user_id=user.id,
        requested_plan_code=plan_code,
        use_case=payload.get("use_case"),
        expected_monthly_minutes=payload.get("expected_monthly_minutes"),
        country=payload.get("country"),
        website=payload.get("website"),
        organisation_name=org_name,
        business_type=payload.get("business_type"),
        billing_contact_email=payload.get("billing_contact_email") or user.email,
        declarations_accepted=True,
        state=EditAccountState.PENDING_ART_CITY_REVIEW.value,
        documents_json=payload.get("documents_json") or {},
        conditions_json={},
    )
    db.add(application)
    db.flush()

    write_audit(
        db,
        action="edit.application.submitted",
        resource_type="edit_access_application",
        resource_id=application.id,
        user_id=user.id,
        detail={"organisation_id": org.id, "plan": plan_code},
    )
    db.flush()
    return application


def _activate_org_with_plan(
    db: Session,
    *,
    org: EditOrganisation,
    plan: EditPlan,
    actor_user_id: str,
    billing_method: str = "invoice",
    workspace_name: Optional[str] = None,
) -> tuple[EditSubscription, EditWorkspace]:
    now = datetime.now(timezone.utc)
    sub = EditSubscription(
        id=str(uuid4()),
        organisation_id=org.id,
        plan_id=plan.id,
        billing_method=billing_method,
        status="active",
        period_start=now,
        metadata_json={"activated_by": actor_user_id},
    )
    db.add(sub)

    org.status = EditAccountState.ACTIVE.value
    db.add(org)

    issue_plan_entitlements(db, org.id, plan)

    workspace = (
        db.query(EditWorkspace)
        .filter(EditWorkspace.organisation_id == org.id)
        .order_by(EditWorkspace.created_at.asc())
        .first()
    )
    if not workspace:
        workspace = EditWorkspace(
            id=str(uuid4()),
            organisation_id=org.id,
            name=workspace_name or f"{org.display_name} Workspace",
            status=EditAccountState.ACTIVE.value,
        )
        db.add(workspace)
        db.flush()

    owner_membership = (
        db.query(EditMembership)
        .filter(
            EditMembership.organisation_id == org.id,
            EditMembership.user_id == org.owner_user_id,
            EditMembership.role == EditWorkspaceRole.OWNER.value,
        )
        .first()
    )
    if org.owner_user_id and not owner_membership:
        db.add(
            EditMembership(
                id=str(uuid4()),
                organisation_id=org.id,
                workspace_id=workspace.id,
                user_id=org.owner_user_id,
                role=EditWorkspaceRole.OWNER.value,
                status="active",
                invited_by=actor_user_id,
            )
        )
    db.flush()
    return sub, workspace


def review_application(
    db: Session,
    application_id: str,
    reviewer: User,
    action: str,
    reason: Optional[str] = None,
    plan_code: Optional[str] = None,
    conditions: Optional[dict[str, Any]] = None,
) -> EditAccessApplication:
    if not is_platform_admin(reviewer):
        raise ValueError("Only platform admins may review applications")

    application = db.get(EditAccessApplication, application_id)
    if not application:
        raise ValueError("Application not found")
    org = db.get(EditOrganisation, application.organisation_id) if application.organisation_id else None
    if not org:
        raise ValueError("Organisation not found for application")

    action = action.lower().strip()
    ensure_default_plans(db)
    chosen_code = plan_code or application.requested_plan_code or "creator"
    plan = db.query(EditPlan).filter(EditPlan.code == chosen_code).first()
    if not plan:
        raise ValueError(f"Unknown plan: {chosen_code}")

    application.reviewer_user_id = reviewer.id
    application.decision_reason = reason
    if conditions is not None:
        application.conditions_json = conditions

    if action == "approve":
        application.requested_plan_code = chosen_code
        if chosen_code == "internal_art_city":
            application.state = EditAccountState.ACTIVE.value
            _activate_org_with_plan(
                db,
                org=org,
                plan=plan,
                actor_user_id=reviewer.id,
                billing_method="internal",
                workspace_name="Art City Edit",
            )
        else:
            application.state = EditAccountState.APPROVED_PENDING_BILLING.value
            org.status = EditAccountState.APPROVED_PENDING_BILLING.value
            db.add(org)
            # Pending subscription record (not active until billing)
            pending = EditSubscription(
                id=str(uuid4()),
                organisation_id=org.id,
                plan_id=plan.id,
                billing_method="invoice",
                status="pending",
                metadata_json={"approved_by": reviewer.id, "conditions": conditions or {}},
            )
            db.add(pending)
    elif action == "reject":
        if not reason:
            raise ValueError("reason is required for reject")
        application.state = EditAccountState.REJECTED.value
        org.status = EditAccountState.REJECTED.value
        db.add(org)
    elif action == "request_info":
        application.state = EditAccountState.MORE_INFORMATION_REQUIRED.value
        org.status = EditAccountState.MORE_INFORMATION_REQUIRED.value
        db.add(org)
    elif action == "suspend":
        if not reason:
            raise ValueError("reason is required for suspend")
        application.state = EditAccountState.SUSPENDED.value
        org.status = EditAccountState.SUSPENDED.value
        db.add(org)
        for sub in (
            db.query(EditSubscription)
            .filter(
                EditSubscription.organisation_id == org.id,
                EditSubscription.status == "active",
            )
            .all()
        ):
            sub.status = "suspended"
            db.add(sub)
    else:
        raise ValueError(f"Unknown action: {action}")

    db.add(application)
    db.flush()
    write_audit(
        db,
        action=f"edit.application.{action}",
        resource_type="edit_access_application",
        resource_id=application.id,
        user_id=reviewer.id,
        detail={
            "organisation_id": org.id,
            "plan": chosen_code,
            "reason": reason,
            "state": application.state,
        },
    )
    db.flush()
    return application


def activate_subscription_invoice(
    db: Session,
    organisation_id: str,
    plan_code: str,
    actor_user_id: str,
) -> EditSubscription:
    org = db.get(EditOrganisation, organisation_id)
    if not org:
        raise ValueError("Organisation not found")
    if org.status not in {
        EditAccountState.APPROVED_PENDING_BILLING.value,
        EditAccountState.ACTIVE.value,
        EditAccountState.PAST_DUE.value,
    }:
        raise ValueError(f"Organisation status {org.status} cannot activate billing")

    ensure_default_plans(db)
    plan = db.query(EditPlan).filter(EditPlan.code == plan_code, EditPlan.is_active.is_(True)).first()
    if not plan:
        raise ValueError(f"Unknown plan: {plan_code}")

    # Supersede prior pending/active rows
    for sub in (
        db.query(EditSubscription)
        .filter(
            EditSubscription.organisation_id == organisation_id,
            EditSubscription.status.in_(["pending", "active"]),
        )
        .all()
    ):
        sub.status = "superseded"
        db.add(sub)

    sub, _workspace = _activate_org_with_plan(
        db,
        org=org,
        plan=plan,
        actor_user_id=actor_user_id,
        billing_method="invoice",
    )
    write_audit(
        db,
        action="edit.subscription.activated",
        resource_type="edit_subscription",
        resource_id=sub.id,
        user_id=actor_user_id,
        detail={"organisation_id": organisation_id, "plan": plan_code, "method": "invoice"},
    )
    db.flush()
    return sub


def seed_internal_art_city(db: Session, admin_user: User) -> EditOrganisation:
    ensure_default_plans(db)
    plan = db.query(EditPlan).filter(EditPlan.code == "internal_art_city").first()
    if not plan:
        raise ValueError("internal_art_city plan missing")

    org = (
        db.query(EditOrganisation)
        .filter(EditOrganisation.display_name == "Art City Group")
        .first()
    )
    if org and org.status == EditAccountState.ACTIVE.value:
        return org

    if not org:
        org = EditOrganisation(
            id=str(uuid4()),
            legal_name="Art City Group",
            display_name="Art City Group",
            country="IQ",
            org_type="internal",
            status=EditAccountState.ACTIVE.value,
            owner_user_id=admin_user.id,
            risk_level="internal",
            ai_training_opt_in=False,
            metadata_json={"seeded": True},
        )
        db.add(org)
        db.flush()
    else:
        org.status = EditAccountState.ACTIVE.value
        org.owner_user_id = org.owner_user_id or admin_user.id
        db.add(org)

    _activate_org_with_plan(
        db,
        org=org,
        plan=plan,
        actor_user_id=admin_user.id,
        billing_method="internal",
        workspace_name="Art City Edit",
    )

    # Ensure dedicated Art City Edit workspace + owner membership
    workspace = (
        db.query(EditWorkspace)
        .filter(
            EditWorkspace.organisation_id == org.id,
            EditWorkspace.name == "Art City Edit",
        )
        .first()
    )
    if not workspace:
        workspace = EditWorkspace(
            id=str(uuid4()),
            organisation_id=org.id,
            name="Art City Edit",
            status=EditAccountState.ACTIVE.value,
        )
        db.add(workspace)
        db.flush()

    membership = (
        db.query(EditMembership)
        .filter(
            EditMembership.workspace_id == workspace.id,
            EditMembership.user_id == admin_user.id,
        )
        .first()
    )
    if not membership:
        db.add(
            EditMembership(
                id=str(uuid4()),
                organisation_id=org.id,
                workspace_id=workspace.id,
                user_id=admin_user.id,
                role=EditWorkspaceRole.OWNER.value,
                status="active",
                invited_by=admin_user.id,
            )
        )

    write_audit(
        db,
        action="edit.org.seed_internal",
        resource_type="edit_organisation",
        resource_id=org.id,
        user_id=admin_user.id,
        detail={"workspace": "Art City Edit", "plan": "internal_art_city"},
    )
    db.flush()
    return org
