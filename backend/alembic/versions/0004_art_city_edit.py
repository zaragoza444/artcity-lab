"""Art City Edit tenancy, media, timeline, render, and billing.

Revision ID: 0004_art_city_edit
Revises: 0003_data_lab_files
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_art_city_edit"
down_revision: Union[str, None] = "0003_data_lab_files"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("account_state", sa.String(50), server_default="active", nullable=False),
    )

    op.create_table(
        "edit_organisations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100)),
        sa.Column("org_type", sa.String(100), server_default="creator"),
        sa.Column("status", sa.String(50), server_default="pending_art_city_review"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("risk_level", sa.String(50), server_default="standard"),
        sa.Column("website", sa.String(512)),
        sa.Column("ai_training_opt_in", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "edit_workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_organisations.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("default_brand_profile_id", postgresql.UUID(as_uuid=False)),
        sa.Column("retention_policy_json", postgresql.JSONB()),
        sa.Column("require_approval_before_export", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_workspaces_organisation_id", "edit_workspaces", ["organisation_id"])

    op.create_table(
        "edit_plans",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("feature_flags", postgresql.JSONB()),
        sa.Column("limits_json", postgresql.JSONB()),
        sa.Column("price_usd_monthly", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_plans_code", "edit_plans", ["code"])

    op.create_table(
        "edit_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_organisations.id"),
            nullable=False,
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_workspaces.id")),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(50), server_default="editor"),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("invited_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_memberships_organisation_id", "edit_memberships", ["organisation_id"])
    op.create_index("ix_edit_memberships_workspace_id", "edit_memberships", ["workspace_id"])
    op.create_index("ix_edit_memberships_user_id", "edit_memberships", ["user_id"])

    op.create_table(
        "edit_access_applications",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_organisations.id")),
        sa.Column(
            "applicant_user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("requested_plan_code", sa.String(100), server_default="creator"),
        sa.Column("use_case", sa.Text()),
        sa.Column("expected_monthly_minutes", sa.Integer()),
        sa.Column("country", sa.String(100)),
        sa.Column("website", sa.String(512)),
        sa.Column("organisation_name", sa.String(255), nullable=False),
        sa.Column("business_type", sa.String(100)),
        sa.Column("billing_contact_email", sa.String(255)),
        sa.Column("declarations_accepted", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("state", sa.String(50), server_default="pending_art_city_review"),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("decision_reason", sa.Text()),
        sa.Column("documents_json", postgresql.JSONB()),
        sa.Column("conditions_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_edit_access_applications_organisation_id",
        "edit_access_applications",
        ["organisation_id"],
    )
    op.create_index(
        "ix_edit_access_applications_applicant_user_id",
        "edit_access_applications",
        ["applicant_user_id"],
    )

    op.create_table(
        "edit_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_organisations.id"),
            nullable=False,
        ),
        sa.Column("plan_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_plans.id"), nullable=False),
        sa.Column("billing_method", sa.String(50), server_default="invoice"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("provider_ref", sa.String(255)),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_subscriptions_organisation_id", "edit_subscriptions", ["organisation_id"])

    op.create_table(
        "edit_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_organisations.id"),
            nullable=False,
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_workspaces.id")),
        sa.Column("feature", sa.String(100), nullable=False),
        sa.Column("limit_value", sa.Float(), server_default="0"),
        sa.Column("used_value", sa.Float(), server_default="0"),
        sa.Column("reset_rule", sa.String(50), server_default="monthly"),
        sa.Column("effective_from", sa.DateTime(timezone=True)),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_entitlements_organisation_id", "edit_entitlements", ["organisation_id"])
    op.create_index("ix_edit_entitlements_workspace_id", "edit_entitlements", ["workspace_id"])

    op.create_table(
        "edit_usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_organisations.id"),
            nullable=False,
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_workspaces.id")),
        sa.Column("job_id", sa.String(255)),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Float(), server_default="0"),
        sa.Column("cost_usd", sa.Float(), server_default="0"),
        sa.Column("billing_period", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_usage_records_organisation_id", "edit_usage_records", ["organisation_id"])

    op.create_table(
        "edit_brand_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_workspaces.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_brand_profiles_workspace_id", "edit_brand_profiles", ["workspace_id"])

    op.create_table(
        "edit_brand_profile_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "brand_profile_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_brand_profiles.id"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("status", sa.String(50), server_default="published"),
        sa.Column("rules_json", postgresql.JSONB()),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_edit_brand_profile_versions_brand_profile_id",
        "edit_brand_profile_versions",
        ["brand_profile_id"],
    )

    op.create_table(
        "edit_media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_workspaces.id"),
            nullable=False,
        ),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("proxy_key", sa.String(1024)),
        sa.Column("thumbnail_key", sa.String(1024)),
        sa.Column("waveform_key", sa.String(1024)),
        sa.Column("checksum", sa.String(128), nullable=False),
        sa.Column("content_type", sa.String(255)),
        sa.Column("size_bytes", sa.Integer(), server_default="0"),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("frame_rate", sa.Float()),
        sa.Column("rights_attested", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("rights_notes", sa.Text()),
        sa.Column("rights_status", sa.String(50), server_default="declared"),
        sa.Column("technical_metadata", postgresql.JSONB()),
        sa.Column("soft_deleted", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_media_assets_workspace_id", "edit_media_assets", ["workspace_id"])
    op.create_index("ix_edit_media_assets_checksum", "edit_media_assets", ["checksum"])

    op.create_table(
        "edit_projects",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_workspaces.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("objective", sa.String(100)),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column(
            "brand_profile_version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_brand_profile_versions.id"),
        ),
        sa.Column("source_asset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_media_assets.id")),
        sa.Column("production_project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id")),
        sa.Column("brief_json", postgresql.JSONB()),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_projects_workspace_id", "edit_projects", ["workspace_id"])

    op.create_table(
        "edit_analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_projects.id"),
            nullable=False,
        ),
        sa.Column("asset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_media_assets.id"), nullable=False),
        sa.Column("job_type", sa.String(50), server_default="full"),
        sa.Column("provider", sa.String(100)),
        sa.Column("model", sa.String(255)),
        sa.Column("state", sa.String(50), server_default="queued"),
        sa.Column("cost_usd", sa.Float(), server_default="0"),
        sa.Column("outputs_json", postgresql.JSONB()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_analysis_jobs_project_id", "edit_analysis_jobs", ["project_id"])

    op.create_table(
        "edit_candidate_clips",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_projects.id"),
            nullable=False,
        ),
        sa.Column("source_in", sa.Float(), nullable=False),
        sa.Column("source_out", sa.Float(), nullable=False),
        sa.Column("score", sa.Float(), server_default="0"),
        sa.Column("explanation", sa.Text()),
        sa.Column("risks_json", postgresql.JSONB()),
        sa.Column("user_decision", sa.String(50), server_default="pending"),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_candidate_clips_project_id", "edit_candidate_clips", ["project_id"])

    op.create_table(
        "edit_timeline_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_projects.id"),
            nullable=False,
        ),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=False)),
        sa.Column("version_number", sa.Integer(), server_default="1"),
        sa.Column("name", sa.String(255)),
        sa.Column("edit_plan_json", postgresql.JSONB()),
        sa.Column("transcript_json", postgresql.JSONB()),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_timeline_versions_project_id", "edit_timeline_versions", ["project_id"])

    op.create_table(
        "edit_render_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_projects.id"),
            nullable=False,
        ),
        sa.Column(
            "timeline_version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_timeline_versions.id"),
            nullable=False,
        ),
        sa.Column("preset", sa.String(100), server_default="social_multi"),
        sa.Column("state", sa.String(50), server_default="queued"),
        sa.Column("outputs_json", postgresql.JSONB()),
        sa.Column("qc_json", postgresql.JSONB()),
        sa.Column("cost_usd", sa.Float(), server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_render_jobs_project_id", "edit_render_jobs", ["project_id"])

    op.create_table(
        "edit_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "timeline_version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_timeline_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "approver_user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50)),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("comments", sa.Text()),
        sa.Column("timecode_seconds", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_approvals_timeline_version_id", "edit_approvals", ["timeline_version_id"])

    op.create_table(
        "edit_publications",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_projects.id"),
            nullable=False,
        ),
        sa.Column(
            "timeline_version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_timeline_versions.id"),
            nullable=False,
        ),
        sa.Column("destination", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("caption_text", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("analytics_consent", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_publications_project_id", "edit_publications", ["project_id"])

    op.create_table(
        "edit_publish_connectors",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("edit_workspaces.id"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("credentials_ref", sa.String(255)),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_edit_publish_connectors_workspace_id", "edit_publish_connectors", ["workspace_id"])

    op.create_table(
        "edit_feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("organisation_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("edit_organisations.id")),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("edit_feature_flags")
    op.drop_index("ix_edit_publish_connectors_workspace_id", table_name="edit_publish_connectors")
    op.drop_table("edit_publish_connectors")
    op.drop_index("ix_edit_publications_project_id", table_name="edit_publications")
    op.drop_table("edit_publications")
    op.drop_index("ix_edit_approvals_timeline_version_id", table_name="edit_approvals")
    op.drop_table("edit_approvals")
    op.drop_index("ix_edit_render_jobs_project_id", table_name="edit_render_jobs")
    op.drop_table("edit_render_jobs")
    op.drop_index("ix_edit_timeline_versions_project_id", table_name="edit_timeline_versions")
    op.drop_table("edit_timeline_versions")
    op.drop_index("ix_edit_candidate_clips_project_id", table_name="edit_candidate_clips")
    op.drop_table("edit_candidate_clips")
    op.drop_index("ix_edit_analysis_jobs_project_id", table_name="edit_analysis_jobs")
    op.drop_table("edit_analysis_jobs")
    op.drop_index("ix_edit_projects_workspace_id", table_name="edit_projects")
    op.drop_table("edit_projects")
    op.drop_index("ix_edit_media_assets_checksum", table_name="edit_media_assets")
    op.drop_index("ix_edit_media_assets_workspace_id", table_name="edit_media_assets")
    op.drop_table("edit_media_assets")
    op.drop_index("ix_edit_brand_profile_versions_brand_profile_id", table_name="edit_brand_profile_versions")
    op.drop_table("edit_brand_profile_versions")
    op.drop_index("ix_edit_brand_profiles_workspace_id", table_name="edit_brand_profiles")
    op.drop_table("edit_brand_profiles")
    op.drop_index("ix_edit_usage_records_organisation_id", table_name="edit_usage_records")
    op.drop_table("edit_usage_records")
    op.drop_index("ix_edit_entitlements_workspace_id", table_name="edit_entitlements")
    op.drop_index("ix_edit_entitlements_organisation_id", table_name="edit_entitlements")
    op.drop_table("edit_entitlements")
    op.drop_index("ix_edit_subscriptions_organisation_id", table_name="edit_subscriptions")
    op.drop_table("edit_subscriptions")
    op.drop_index("ix_edit_access_applications_applicant_user_id", table_name="edit_access_applications")
    op.drop_index("ix_edit_access_applications_organisation_id", table_name="edit_access_applications")
    op.drop_table("edit_access_applications")
    op.drop_index("ix_edit_memberships_user_id", table_name="edit_memberships")
    op.drop_index("ix_edit_memberships_workspace_id", table_name="edit_memberships")
    op.drop_index("ix_edit_memberships_organisation_id", table_name="edit_memberships")
    op.drop_table("edit_memberships")
    op.drop_index("ix_edit_plans_code", table_name="edit_plans")
    op.drop_table("edit_plans")
    op.drop_index("ix_edit_workspaces_organisation_id", table_name="edit_workspaces")
    op.drop_table("edit_workspaces")
    op.drop_table("edit_organisations")
    op.drop_column("users", "account_state")
    op.drop_column("users", "email_verified_at")
