"""Art City Edit — tenancy, media, timeline, render, and billing models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.enums import (
    EditAccountState,
    EditJobStatus,
    EditProjectStatus,
    EditVersionReviewStatus,
    EditWorkspaceRole,
)


class EditOrganisation(Base):
    __tablename__ = "edit_organisations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    org_type: Mapped[str] = mapped_column(String(100), default="creator")
    status: Mapped[str] = mapped_column(String(50), default=EditAccountState.PENDING_ART_CITY_REVIEW.value)
    owner_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    risk_level: Mapped[str] = mapped_column(String(50), default="standard")
    website: Mapped[Optional[str]] = mapped_column(String(512))
    ai_training_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditWorkspace(Base):
    __tablename__ = "edit_workspaces"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    organisation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_organisations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=EditAccountState.ACTIVE.value)
    default_brand_profile_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    retention_policy_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    require_approval_before_export: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditMembership(Base):
    __tablename__ = "edit_memberships"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    organisation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_organisations.id"), nullable=False, index=True
    )
    workspace_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_workspaces.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default=EditWorkspaceRole.EDITOR.value)
    status: Mapped[str] = mapped_column(String(50), default="active")
    invited_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditAccessApplication(Base):
    __tablename__ = "edit_access_applications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    organisation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_organisations.id"), index=True
    )
    applicant_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True
    )
    requested_plan_code: Mapped[str] = mapped_column(String(100), default="creator")
    use_case: Mapped[Optional[str]] = mapped_column(Text)
    expected_monthly_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    website: Mapped[Optional[str]] = mapped_column(String(512))
    organisation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(String(100))
    billing_contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    declarations_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[str] = mapped_column(String(50), default=EditAccountState.PENDING_ART_CITY_REVIEW.value)
    reviewer_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    decision_reason: Mapped[Optional[str]] = mapped_column(Text)
    documents_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    conditions_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditPlan(Base):
    __tablename__ = "edit_plans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    feature_flags: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    limits_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    price_usd_monthly: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditSubscription(Base):
    __tablename__ = "edit_subscriptions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    organisation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_organisations.id"), nullable=False, index=True
    )
    plan_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("edit_plans.id"), nullable=False)
    billing_method: Mapped[str] = mapped_column(String(50), default="invoice")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255))
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditEntitlement(Base):
    __tablename__ = "edit_entitlements"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    organisation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_organisations.id"), nullable=False, index=True
    )
    workspace_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_workspaces.id"), index=True
    )
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    limit_value: Mapped[float] = mapped_column(Float, default=0)
    used_value: Mapped[float] = mapped_column(Float, default=0)
    reset_rule: Mapped[str] = mapped_column(String(50), default="monthly")
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditUsageRecord(Base):
    __tablename__ = "edit_usage_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    organisation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_organisations.id"), nullable=False, index=True
    )
    workspace_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("edit_workspaces.id"))
    job_id: Mapped[Optional[str]] = mapped_column(String(255))
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    billing_period: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditBrandProfile(Base):
    __tablename__ = "edit_brand_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_workspaces.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    owner_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditBrandProfileVersion(Base):
    __tablename__ = "edit_brand_profile_versions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    brand_profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_brand_profiles.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="published")
    rules_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditMediaAsset(Base):
    __tablename__ = "edit_media_assets"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_workspaces.id"), nullable=False, index=True
    )
    owner_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    proxy_key: Mapped[Optional[str]] = mapped_column(String(1024))
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(1024))
    waveform_key: Mapped[Optional[str]] = mapped_column(String(1024))
    checksum: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    frame_rate: Mapped[Optional[float]] = mapped_column(Float)
    rights_attested: Mapped[bool] = mapped_column(Boolean, default=False)
    rights_notes: Mapped[Optional[str]] = mapped_column(Text)
    rights_status: Mapped[str] = mapped_column(String(50), default="declared")
    technical_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    soft_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditProject(Base):
    __tablename__ = "edit_projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_workspaces.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default=EditProjectStatus.DRAFT.value)
    brand_profile_version_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_brand_profile_versions.id")
    )
    source_asset_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_media_assets.id")
    )
    production_project_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id")
    )
    brief_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditAnalysisJob(Base):
    __tablename__ = "edit_analysis_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_projects.id"), nullable=False, index=True
    )
    asset_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_media_assets.id"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(50), default="full")
    provider: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(50), default=EditJobStatus.QUEUED.value)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    outputs_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditCandidateClip(Base):
    __tablename__ = "edit_candidate_clips"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_projects.id"), nullable=False, index=True
    )
    source_in: Mapped[float] = mapped_column(Float, nullable=False)
    source_out: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    risks_json: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    user_decision: Mapped[str] = mapped_column(String(50), default="pending")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditTimelineVersion(Base):
    __tablename__ = "edit_timeline_versions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_projects.id"), nullable=False, index=True
    )
    parent_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    edit_plan_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    transcript_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(50), default=EditVersionReviewStatus.DRAFT.value)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditRenderJob(Base):
    __tablename__ = "edit_render_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_projects.id"), nullable=False, index=True
    )
    timeline_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_timeline_versions.id"), nullable=False
    )
    preset: Mapped[str] = mapped_column(String(100), default="social_multi")
    state: Mapped[str] = mapped_column(String(50), default=EditJobStatus.QUEUED.value)
    outputs_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    qc_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EditApproval(Base):
    __tablename__ = "edit_approvals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    timeline_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_timeline_versions.id"), nullable=False, index=True
    )
    approver_user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(50))
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    timecode_seconds: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditPublication(Base):
    __tablename__ = "edit_publications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_projects.id"), nullable=False, index=True
    )
    timeline_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_timeline_versions.id"), nullable=False
    )
    destination: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    caption_text: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    analytics_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditPublishConnector(Base):
    __tablename__ = "edit_publish_connectors"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_workspaces.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    credentials_ref: Mapped[Optional[str]] = mapped_column(String(255))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditFeatureFlag(Base):
    __tablename__ = "edit_feature_flags"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    organisation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("edit_organisations.id")
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
