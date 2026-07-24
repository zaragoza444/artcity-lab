"""Art City Edit — control-plane APIs (access, orgs, media, timeline, render, publish)."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models import User

from app.api.schemas_edit import (
    EditAccessApplicationCreate,
    EditAccessApplicationOut,
    EditAnalysisJobOut,
    EditBrandProfileCreate,
    EditBrandProfileOut,
    EditBrandVersionOut,
    EditCandidateDecision,
    EditCandidateOut,
    EditCheckoutSessionOut,
    EditConnectorCreate,
    EditConnectorOut,
    EditMediaAssetOut,
    EditMembershipOut,
    EditOrganisationOut,
    EditPlanOut,
    EditPlanUpdate,
    EditProjectCreate,
    EditProjectOut,
    EditPublicationOut,
    EditPublishRequest,
    EditRenderJobOut,
    EditRenderStart,
    EditReviewAction,
    EditSubscriptionActivate,
    EditSubscriptionOut,
    EditSummaryOut,
    EditTimelineFromCandidates,
    EditTimelineVersionOut,
    EditTranscriptRemoval,
    EditVersionDecision,
    EditWorkspaceOut,
)
from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import CurrentUser, get_current_user, require_roles
from app.core.enums import EDIT_APPROVAL_ROLES, EditAccountState, UserRole
from app.models_edit import (
    EditAccessApplication,
    EditAnalysisJob,
    EditBrandProfile,
    EditBrandProfileVersion,
    EditCandidateClip,
    EditMediaAsset,
    EditOrganisation,
    EditProject,
    EditRenderJob,
    EditTimelineVersion,
    EditWorkspace,
)
from app.services import edit_access, edit_media, edit_publish, edit_render, edit_timeline
from app.services.edit_entitlements import (
    assert_entitled,
    get_user_memberships,
    is_platform_admin,
    require_workspace_access,
)

router = APIRouter(prefix="/api/edit", tags=["edit"], dependencies=[Depends(get_current_user)])


# ── Summary / health ─────────────────────────────────────────────────────────


@router.get("/summary", response_model=EditSummaryOut)
def edit_summary(user: CurrentUser, db: Session = Depends(get_db)) -> EditSummaryOut:
    settings = get_settings()
    memberships = get_user_memberships(db, user.id)
    workspace_ids = {m.workspace_id for m in memberships if m.workspace_id}
    if is_platform_admin(user):
        workspace_count = db.query(EditWorkspace).count()
        project_count = db.query(EditProject).count()
        pending = (
            db.query(EditAccessApplication)
            .filter(EditAccessApplication.state == EditAccountState.PENDING_ART_CITY_REVIEW.value)
            .count()
        )
    else:
        workspace_count = len(workspace_ids)
        project_count = (
            db.query(EditProject).filter(EditProject.workspace_id.in_(workspace_ids)).count()
            if workspace_ids
            else 0
        )
        pending = 0
    return EditSummaryOut(
        workspaces=workspace_count,
        projects=project_count,
        pending_applications=pending,
        feature_flags={
            "publishing": settings.edit_feature_publishing,
            "trend_intelligence": settings.edit_feature_trend_intelligence,
            "multi_cam": settings.edit_feature_multi_cam,
        },
    )


# ── Plans / access / billing ─────────────────────────────────────────────────


@router.get("/plans", response_model=list[EditPlanOut])
def list_plans(db: Session = Depends(get_db)) -> list[EditPlanOut]:
    edit_access.ensure_default_plans(db)
    db.commit()
    return [EditPlanOut.model_validate(p) for p in edit_access.list_plans(db)]


@router.post(
    "/access-applications",
    response_model=EditAccessApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_access_application(
    payload: EditAccessApplicationCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditAccessApplicationOut:
    try:
        app_row = edit_access.submit_application(db, user, payload.model_dump())
        db.commit()
        db.refresh(app_row)
        return EditAccessApplicationOut.model_validate(app_row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/access-applications/mine", response_model=list[EditAccessApplicationOut])
def my_applications(user: CurrentUser, db: Session = Depends(get_db)) -> list[EditAccessApplicationOut]:
    rows = (
        db.query(EditAccessApplication)
        .filter(EditAccessApplication.applicant_user_id == user.id)
        .order_by(EditAccessApplication.created_at.desc())
        .all()
    )
    return [EditAccessApplicationOut.model_validate(r) for r in rows]


@router.get("/access-applications", response_model=list[EditAccessApplicationOut])
def list_applications(
    user: Annotated[User, Depends(require_roles(*EDIT_APPROVAL_ROLES))],
    db: Session = Depends(get_db),
    state: Optional[str] = None,
) -> list[EditAccessApplicationOut]:
    q = db.query(EditAccessApplication).order_by(EditAccessApplication.created_at.desc())
    if state:
        q = q.filter(EditAccessApplication.state == state)
    return [EditAccessApplicationOut.model_validate(r) for r in q.limit(200).all()]


@router.post("/access-applications/{application_id}/review", response_model=EditAccessApplicationOut)
def review_application(
    application_id: str,
    payload: EditReviewAction,
    user: Annotated[User, Depends(require_roles(*EDIT_APPROVAL_ROLES))],
    db: Session = Depends(get_db),
) -> EditAccessApplicationOut:
    try:
        row = edit_access.review_application(
            db,
            application_id,
            user,
            payload.action,
            reason=payload.reason,
            plan_code=payload.plan_code,
            conditions=payload.conditions,
        )
        db.commit()
        db.refresh(row)
        return EditAccessApplicationOut.model_validate(row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/organisations/{organisation_id}/activate", response_model=EditSubscriptionOut)
def activate_subscription(
    organisation_id: str,
    payload: EditSubscriptionActivate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditSubscriptionOut:
    if not is_platform_admin(user):
        org = db.get(EditOrganisation, organisation_id)
        if not org or org.owner_user_id != user.id:
            raise HTTPException(status_code=403, detail="Not organisation owner")
    try:
        sub = edit_access.activate_subscription_invoice(
            db, organisation_id, payload.plan_code, user.id
        )
        db.commit()
        db.refresh(sub)
        return EditSubscriptionOut.model_validate(sub)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/organisations/{organisation_id}/checkout-session", response_model=EditCheckoutSessionOut)
def checkout_session(
    organisation_id: str,
    payload: EditSubscriptionActivate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditCheckoutSessionOut:
    settings = get_settings()
    org = db.get(EditOrganisation, organisation_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    if not is_platform_admin(user) and org.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not organisation owner")
    if settings.stripe_secret_key:
        return EditCheckoutSessionOut(
            mode="stripe",
            checkout_url=None,
            message="Stripe configured — complete checkout via provider integration (invoice fallback available).",
        )
    return EditCheckoutSessionOut(
        mode="invoice",
        checkout_url=None,
        message="No Stripe key; use POST .../activate for invoice/manual activation.",
    )


@router.get("/organisations", response_model=list[EditOrganisationOut])
def list_organisations(user: CurrentUser, db: Session = Depends(get_db)) -> list[EditOrganisationOut]:
    if is_platform_admin(user):
        rows = db.query(EditOrganisation).order_by(EditOrganisation.created_at.desc()).all()
    else:
        memberships = get_user_memberships(db, user.id)
        org_ids = {m.organisation_id for m in memberships}
        rows = (
            db.query(EditOrganisation).filter(EditOrganisation.id.in_(org_ids)).all() if org_ids else []
        )
    return [EditOrganisationOut.model_validate(r) for r in rows]


@router.get("/workspaces", response_model=list[EditWorkspaceOut])
def list_workspaces(user: CurrentUser, db: Session = Depends(get_db)) -> list[EditWorkspaceOut]:
    if is_platform_admin(user):
        rows = db.query(EditWorkspace).order_by(EditWorkspace.created_at.desc()).all()
    else:
        memberships = get_user_memberships(db, user.id)
        ids = {m.workspace_id for m in memberships if m.workspace_id}
        rows = db.query(EditWorkspace).filter(EditWorkspace.id.in_(ids)).all() if ids else []
    return [EditWorkspaceOut.model_validate(r) for r in rows]


@router.get("/memberships/mine", response_model=list[EditMembershipOut])
def my_memberships(user: CurrentUser, db: Session = Depends(get_db)) -> list[EditMembershipOut]:
    return [EditMembershipOut.model_validate(m) for m in get_user_memberships(db, user.id)]


# ── Brand profiles ───────────────────────────────────────────────────────────


@router.post(
    "/workspaces/{workspace_id}/brands",
    response_model=EditBrandProfileOut,
    status_code=status.HTTP_201_CREATED,
)
def create_brand(
    workspace_id: str,
    payload: EditBrandProfileCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditBrandProfileOut:
    try:
        require_workspace_access(db, user, workspace_id, roles=["owner", "admin", "editor"])
        profile = EditBrandProfile(
            workspace_id=workspace_id,
            name=payload.name,
            owner_user_id=user.id,
        )
        db.add(profile)
        db.flush()
        version = EditBrandProfileVersion(
            brand_profile_id=profile.id,
            version=1,
            status="published",
            rules_json=payload.rules
            or {
                "identity": {"brand_name": payload.name},
                "captions": {"languages": ["ckb", "en"]},
                "editorial": {"tone": ["prestigious"]},
            },
            created_by=user.id,
        )
        db.add(version)
        db.commit()
        db.refresh(profile)
        return EditBrandProfileOut.model_validate(profile)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/brands", response_model=list[EditBrandProfileOut])
def list_brands(
    workspace_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditBrandProfileOut]:
    try:
        require_workspace_access(db, user, workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    rows = db.query(EditBrandProfile).filter(EditBrandProfile.workspace_id == workspace_id).all()
    return [EditBrandProfileOut.model_validate(r) for r in rows]


@router.get("/brands/{brand_id}/versions", response_model=list[EditBrandVersionOut])
def list_brand_versions(
    brand_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditBrandVersionOut]:
    profile = db.get(EditBrandProfile, brand_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Brand not found")
    try:
        require_workspace_access(db, user, profile.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    rows = (
        db.query(EditBrandProfileVersion)
        .filter(EditBrandProfileVersion.brand_profile_id == brand_id)
        .order_by(EditBrandProfileVersion.version.desc())
        .all()
    )
    return [EditBrandVersionOut.model_validate(r) for r in rows]


# ── Media / projects / analysis ──────────────────────────────────────────────


@router.post(
    "/workspaces/{workspace_id}/assets",
    response_model=EditMediaAssetOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_asset(
    workspace_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    rights_attested: bool = Form(False),
    rights_notes: Optional[str] = Form(None),
) -> EditMediaAssetOut:
    try:
        require_workspace_access(db, user, workspace_id, roles=["owner", "admin", "editor"])
        workspace = db.get(EditWorkspace, workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        assert_entitled(db, workspace.organisation_id, feature="processing_minutes", amount=0)
        data = await file.read()
        asset = edit_media.upload_source(
            db,
            workspace_id,
            user,
            data,
            file.filename or "upload.bin",
            file.content_type or "application/octet-stream",
            rights_attested=rights_attested,
            rights_notes=rights_notes,
        )
        db.commit()
        db.refresh(asset)
        return EditMediaAssetOut.model_validate(asset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/assets", response_model=list[EditMediaAssetOut])
def list_assets(
    workspace_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditMediaAssetOut]:
    try:
        require_workspace_access(db, user, workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    rows = (
        db.query(EditMediaAsset)
        .filter(EditMediaAsset.workspace_id == workspace_id, EditMediaAsset.soft_deleted.is_(False))
        .order_by(EditMediaAsset.created_at.desc())
        .all()
    )
    return [EditMediaAssetOut.model_validate(r) for r in rows]


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=EditProjectOut,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    workspace_id: str,
    payload: EditProjectCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditProjectOut:
    try:
        project = edit_media.create_project(
            db,
            workspace_id,
            user,
            payload.title,
            payload.source_asset_id,
            brand_profile_version_id=payload.brand_profile_version_id,
            production_project_id=payload.production_project_id,
            brief=payload.brief,
        )
        if payload.objective:
            project.objective = payload.objective
        db.commit()
        db.refresh(project)
        return EditProjectOut.model_validate(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/projects", response_model=list[EditProjectOut])
def list_workspace_projects(
    workspace_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditProjectOut]:
    try:
        require_workspace_access(db, user, workspace_id)
        rows = edit_media.list_projects(db, workspace_id)
        return [EditProjectOut.model_validate(r) for r in rows]
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/projects/{project_id}", response_model=EditProjectOut)
def get_project(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> EditProjectOut:
    try:
        project = edit_media.get_project(db, project_id)
        require_workspace_access(db, user, project.workspace_id)
        return EditProjectOut.model_validate(project)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/projects/{project_id}/analyse", response_model=EditAnalysisJobOut)
def start_analysis(
    project_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> EditAnalysisJobOut:
    try:
        job = edit_media.start_analysis(db, project_id, user)
        db.commit()
        db.refresh(job)
        return EditAnalysisJobOut.model_validate(job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/analysis", response_model=list[EditAnalysisJobOut])
def list_analysis(
    project_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditAnalysisJobOut]:
    try:
        project = edit_media.get_project(db, project_id)
        require_workspace_access(db, user, project.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    rows = (
        db.query(EditAnalysisJob)
        .filter(EditAnalysisJob.project_id == project_id)
        .order_by(EditAnalysisJob.created_at.desc())
        .all()
    )
    return [EditAnalysisJobOut.model_validate(r) for r in rows]


@router.get("/projects/{project_id}/candidates", response_model=list[EditCandidateOut])
def list_candidates(
    project_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditCandidateOut]:
    try:
        project = edit_media.get_project(db, project_id)
        require_workspace_access(db, user, project.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    rows = (
        db.query(EditCandidateClip)
        .filter(EditCandidateClip.project_id == project_id)
        .order_by(EditCandidateClip.score.desc())
        .all()
    )
    return [EditCandidateOut.model_validate(r) for r in rows]


@router.post("/candidates/{candidate_id}/decision", response_model=EditCandidateOut)
def candidate_decision(
    candidate_id: str,
    payload: EditCandidateDecision,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditCandidateOut:
    try:
        cand = db.get(EditCandidateClip, candidate_id)
        if not cand:
            raise ValueError("Candidate not found")
        project = edit_media.get_project(db, cand.project_id)
        require_workspace_access(db, user, project.workspace_id, roles=["owner", "admin", "editor"])
        row = edit_media.decide_candidate(db, candidate_id, payload.decision)
        db.commit()
        db.refresh(row)
        return EditCandidateOut.model_validate(row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── Timeline / review ────────────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/timelines",
    response_model=EditTimelineVersionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_timeline(
    project_id: str,
    payload: EditTimelineFromCandidates,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditTimelineVersionOut:
    try:
        version = edit_timeline.create_timeline_from_candidates(
            db, project_id, user, payload.candidate_ids
        )
        if payload.name:
            version.name = payload.name
        db.commit()
        db.refresh(version)
        return EditTimelineVersionOut.model_validate(version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/timelines", response_model=list[EditTimelineVersionOut])
def list_timelines(
    project_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditTimelineVersionOut]:
    try:
        project = edit_media.get_project(db, project_id)
        require_workspace_access(db, user, project.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    rows = (
        db.query(EditTimelineVersion)
        .filter(EditTimelineVersion.project_id == project_id)
        .order_by(EditTimelineVersion.version_number.desc())
        .all()
    )
    return [EditTimelineVersionOut.model_validate(r) for r in rows]


@router.patch("/timelines/{version_id}", response_model=EditTimelineVersionOut)
def patch_timeline(
    version_id: str,
    payload: EditPlanUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditTimelineVersionOut:
    try:
        version = db.get(EditTimelineVersion, version_id)
        if not version:
            raise ValueError("Timeline version not found")
        project = edit_media.get_project(db, version.project_id)
        require_workspace_access(db, user, project.workspace_id, roles=["owner", "admin", "editor"])
        version = edit_timeline.update_edit_plan(db, version_id, payload.edit_plan)
        db.commit()
        db.refresh(version)
        return EditTimelineVersionOut.model_validate(version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/timelines/{version_id}/transcript-remove", response_model=EditTimelineVersionOut)
def transcript_remove(
    version_id: str,
    payload: EditTranscriptRemoval,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditTimelineVersionOut:
    try:
        version = db.get(EditTimelineVersion, version_id)
        if not version:
            raise ValueError("Timeline version not found")
        project = edit_media.get_project(db, version.project_id)
        require_workspace_access(db, user, project.workspace_id, roles=["owner", "admin", "editor"])
        version = edit_timeline.apply_transcript_removal(
            db, version_id, payload.remove_ranges
        )
        db.commit()
        db.refresh(version)
        return EditTimelineVersionOut.model_validate(version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/timelines/{version_id}/submit-review", response_model=EditTimelineVersionOut)
def submit_review(
    version_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> EditTimelineVersionOut:
    try:
        version = edit_timeline.submit_for_review(db, version_id, user)
        db.commit()
        db.refresh(version)
        return EditTimelineVersionOut.model_validate(version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/timelines/{version_id}/decide", response_model=EditTimelineVersionOut)
def decide_version(
    version_id: str,
    payload: EditVersionDecision,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditTimelineVersionOut:
    try:
        version = edit_timeline.decide_version(
            db,
            version_id,
            user,
            payload.decision,
            comments=payload.comments,
            timecode=payload.timecode_seconds,
        )
        db.commit()
        db.refresh(version)
        return EditTimelineVersionOut.model_validate(version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── Render / export ──────────────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/renders",
    response_model=EditRenderJobOut,
    status_code=status.HTTP_201_CREATED,
)
def start_render(
    project_id: str,
    payload: EditRenderStart,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditRenderJobOut:
    try:
        project = edit_media.get_project(db, project_id)
        require_workspace_access(db, user, project.workspace_id, roles=["owner", "admin", "editor"])
        job = edit_render.start_render(
            db, project_id, payload.timeline_version_id, ratios=payload.ratios
        )
        db.commit()
        db.refresh(job)
        return EditRenderJobOut.model_validate(job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/renders", response_model=list[EditRenderJobOut])
def list_renders(
    project_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditRenderJobOut]:
    try:
        project = edit_media.get_project(db, project_id)
        require_workspace_access(db, user, project.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    rows = (
        db.query(EditRenderJob)
        .filter(EditRenderJob.project_id == project_id)
        .order_by(EditRenderJob.created_at.desc())
        .all()
    )
    return [EditRenderJobOut.model_validate(r) for r in rows]


@router.get("/renders/{render_job_id}/package")
def export_package(
    render_job_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> dict:
    try:
        pkg = edit_render.get_export_package(db, render_job_id)
        project = edit_media.get_project(db, pkg["project_id"])
        require_workspace_access(db, user, project.workspace_id)
        return pkg
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── Publish connectors ───────────────────────────────────────────────────────


@router.get("/workspaces/{workspace_id}/connectors", response_model=list[EditConnectorOut])
def list_connectors(
    workspace_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> list[EditConnectorOut]:
    try:
        require_workspace_access(db, user, workspace_id)
        rows = edit_publish.list_connectors(db, workspace_id)
        return [EditConnectorOut.model_validate(r) for r in rows]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/workspaces/{workspace_id}/connectors",
    response_model=EditConnectorOut,
    status_code=status.HTTP_201_CREATED,
)
def create_connector(
    workspace_id: str,
    payload: EditConnectorCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditConnectorOut:
    try:
        row = edit_publish.create_connector(
            db,
            workspace_id,
            user,
            payload.provider,
            payload.display_name,
            credentials_ref=payload.credentials_ref,
            metadata=payload.metadata,
        )
        db.commit()
        db.refresh(row)
        return EditConnectorOut.model_validate(row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/projects/{project_id}/publish",
    response_model=EditPublicationOut,
    status_code=status.HTTP_201_CREATED,
)
def publish_project(
    project_id: str,
    payload: EditPublishRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> EditPublicationOut:
    try:
        pub = edit_publish.publish_version(
            db,
            project_id,
            payload.timeline_version_id,
            user,
            destination=payload.destination,
            caption_text=payload.caption_text,
            analytics_consent=payload.analytics_consent,
            metadata=payload.metadata,
        )
        db.commit()
        db.refresh(pub)
        return EditPublicationOut.model_validate(pub)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/seed/internal", response_model=EditWorkspaceOut)
def seed_internal(
    user: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMINISTRATOR))],
    db: Session = Depends(get_db),
) -> EditWorkspaceOut:
    org = edit_access.seed_internal_art_city(db, user)
    db.commit()
    workspace = (
        db.query(EditWorkspace)
        .filter(
            EditWorkspace.organisation_id == org.id,
            EditWorkspace.name == "Art City Edit",
        )
        .first()
    )
    if not workspace:
        raise HTTPException(status_code=500, detail="Internal workspace not created")
    return EditWorkspaceOut.model_validate(workspace)
