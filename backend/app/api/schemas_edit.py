"""Pydantic schemas for Art City Edit APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EditPlanOut(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    feature_flags: Optional[dict[str, Any]] = None
    limits_json: Optional[dict[str, Any]] = None
    price_usd_monthly: Optional[float] = None

    model_config = {"from_attributes": True}


class EditAccessApplicationCreate(BaseModel):
    organisation_name: str
    requested_plan_code: str = "creator"
    use_case: Optional[str] = None
    expected_monthly_minutes: Optional[int] = None
    country: Optional[str] = None
    website: Optional[str] = None
    business_type: Optional[str] = None
    billing_contact_email: Optional[str] = None
    declarations_accepted: bool = False


class EditAccessApplicationOut(BaseModel):
    id: str
    organisation_id: Optional[str] = None
    applicant_user_id: str
    requested_plan_code: str
    use_case: Optional[str] = None
    expected_monthly_minutes: Optional[int] = None
    country: Optional[str] = None
    website: Optional[str] = None
    organisation_name: str
    business_type: Optional[str] = None
    billing_contact_email: Optional[str] = None
    declarations_accepted: bool
    state: str
    reviewer_user_id: Optional[str] = None
    decision_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EditReviewAction(BaseModel):
    action: str = Field(description="approve | reject | request_info | suspend")
    reason: Optional[str] = None
    plan_code: Optional[str] = None
    conditions: Optional[dict[str, Any]] = None


class EditOrganisationOut(BaseModel):
    id: str
    legal_name: str
    display_name: str
    country: Optional[str] = None
    org_type: str
    status: str
    owner_user_id: Optional[str] = None
    website: Optional[str] = None
    ai_training_opt_in: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EditWorkspaceOut(BaseModel):
    id: str
    organisation_id: str
    name: str
    status: str
    require_approval_before_export: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EditMembershipOut(BaseModel):
    id: str
    organisation_id: str
    workspace_id: Optional[str] = None
    user_id: str
    role: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EditSubscriptionActivate(BaseModel):
    plan_code: str = "creator"
    billing_method: str = "invoice"


class EditSubscriptionOut(BaseModel):
    id: str
    organisation_id: str
    plan_id: str
    billing_method: str
    status: str
    provider_ref: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditCheckoutSessionOut(BaseModel):
    mode: str
    checkout_url: Optional[str] = None
    message: str


class EditBrandProfileCreate(BaseModel):
    name: str
    rules: Optional[dict[str, Any]] = None


class EditBrandProfileOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EditBrandVersionOut(BaseModel):
    id: str
    brand_profile_id: str
    version: int
    status: str
    rules_json: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditMediaAssetOut(BaseModel):
    id: str
    workspace_id: str
    filename: str
    storage_key: str
    proxy_key: Optional[str] = None
    thumbnail_key: Optional[str] = None
    checksum: str
    content_type: Optional[str] = None
    size_bytes: int
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    rights_attested: bool
    rights_notes: Optional[str] = None
    rights_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EditProjectCreate(BaseModel):
    title: str
    source_asset_id: str
    brand_profile_version_id: Optional[str] = None
    production_project_id: Optional[str] = None
    objective: Optional[str] = None
    brief: Optional[dict[str, Any]] = None


class EditProjectOut(BaseModel):
    id: str
    workspace_id: str
    title: str
    objective: Optional[str] = None
    status: str
    brand_profile_version_id: Optional[str] = None
    source_asset_id: Optional[str] = None
    production_project_id: Optional[str] = None
    brief_json: Optional[dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EditCandidateOut(BaseModel):
    id: str
    project_id: str
    source_in: float
    source_out: float
    score: float
    explanation: Optional[str] = None
    risks_json: Optional[list[Any]] = None
    user_decision: str
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditCandidateDecision(BaseModel):
    decision: str = Field(description="pin | reject | pending")


class EditAnalysisJobOut(BaseModel):
    id: str
    project_id: str
    asset_id: str
    job_type: str
    state: str
    cost_usd: float
    outputs_json: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditTimelineVersionOut(BaseModel):
    id: str
    project_id: str
    parent_version_id: Optional[str] = None
    version_number: int
    name: Optional[str] = None
    edit_plan_json: Optional[dict[str, Any]] = None
    transcript_json: Optional[dict[str, Any]] = None
    status: str
    created_by: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditTimelineFromCandidates(BaseModel):
    candidate_ids: list[str]
    name: Optional[str] = None


class EditPlanUpdate(BaseModel):
    edit_plan: dict[str, Any]


class EditTranscriptRemoval(BaseModel):
    remove_ranges: list[dict[str, float]]


class EditVersionDecision(BaseModel):
    decision: str = Field(description="approve | reject | request_changes")
    comments: Optional[str] = None
    timecode_seconds: Optional[float] = None


class EditRenderStart(BaseModel):
    timeline_version_id: str
    ratios: list[str] = Field(default_factory=lambda: ["9:16", "16:9", "4:5", "1:1"])


class EditRenderJobOut(BaseModel):
    id: str
    project_id: str
    timeline_version_id: str
    preset: str
    state: str
    outputs_json: Optional[dict[str, Any]] = None
    qc_json: Optional[dict[str, Any]] = None
    cost_usd: float
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditConnectorCreate(BaseModel):
    provider: str
    display_name: str
    credentials_ref: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class EditConnectorOut(BaseModel):
    id: str
    workspace_id: str
    provider: str
    display_name: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EditPublishRequest(BaseModel):
    timeline_version_id: str
    destination: str
    caption_text: Optional[str] = None
    analytics_consent: bool = False
    metadata: Optional[dict[str, Any]] = None


class EditPublicationOut(BaseModel):
    id: str
    project_id: str
    timeline_version_id: str
    destination: str
    external_id: Optional[str] = None
    caption_text: Optional[str] = None
    analytics_consent: bool
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditSummaryOut(BaseModel):
    product: str = "Art City Edit"
    workspaces: int = 0
    projects: int = 0
    pending_applications: int = 0
    feature_flags: dict[str, bool] = Field(default_factory=dict)
