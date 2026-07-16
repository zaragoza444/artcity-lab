"""Initial MVP schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("budget_limit", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "characters",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("identity_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("costume_notes", sa.Text(), nullable=True),
        sa.Column("voice_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reference_paths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scripts",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="ku"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("soft_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("modality", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("result_uri", sa.String(length=1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("actual_cost", sa.Float(), nullable=True),
        sa.Column("provider_job_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scenes",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("script_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cost_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("generation_job_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["generation_job_id"], ["generation_jobs.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("generation_job_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewer_role", sa.String(length=50), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["generation_job_id"], ["generation_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "shots",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scene_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shot_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("camera_movement", sa.String(length=255), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("shots")
    op.drop_table("reviews")
    op.drop_table("cost_records")
    op.drop_table("scenes")
    op.drop_table("generation_jobs")
    op.drop_table("assets")
    op.drop_table("scripts")
    op.drop_table("characters")
    op.drop_table("projects")
