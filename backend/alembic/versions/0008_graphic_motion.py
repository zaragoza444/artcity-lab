"""Alembic 0008 — AC Graphic Motion MSG tables.

Revision ID: 0008_graphic_motion
Revises: 0007_vertical_drama
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_graphic_motion"
down_revision: Union[str, None] = "0007_vertical_drama"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "agm_scenes",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("locale", sa.String(32), server_default="ckb-IQ"),
        sa.Column("direction", sa.String(8), server_default="rtl"),
        sa.Column("head_revision_id", UUID),
        sa.Column("content_hash", sa.String(128)),
        sa.Column("etag", sa.String(128)),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("soft_deleted", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agm_scenes_project_id", "agm_scenes", ["project_id"])
    op.create_index("ix_agm_scenes_idempotency_key", "agm_scenes", ["idempotency_key"])

    op.create_table(
        "agm_revisions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scene_id", UUID, sa.ForeignKey("agm_scenes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("graph_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("parent_revision_id", UUID, sa.ForeignKey("agm_revisions.id")),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("scene_id", "revision_no", name="uq_agm_revision_no"),
    )
    op.create_index("ix_agm_revisions_scene_id", "agm_revisions", ["scene_id"])
    op.create_index("ix_agm_revisions_project_id", "agm_revisions", ["project_id"])

    op.create_table(
        "agm_jobs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scene_id", UUID, sa.ForeignKey("agm_scenes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("revision_id", UUID, sa.ForeignKey("agm_revisions.id"), nullable=False),
        sa.Column("job_kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), server_default="queued"),
        sa.Column("progress", sa.Float(), server_default="0"),
        sa.Column("profile_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("request_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("outputs_json", postgresql.JSONB(), server_default="[]"),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("acx_quote_id", sa.String(64)),
        sa.Column("acx_reservation_id", UUID),
        sa.Column("parent_job_id", UUID, sa.ForeignKey("agm_jobs.id")),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agm_jobs_scene_id", "agm_jobs", ["scene_id"])
    op.create_index("ix_agm_jobs_project_id", "agm_jobs", ["project_id"])
    op.create_index("ix_agm_jobs_revision_id", "agm_jobs", ["revision_id"])

    op.create_table(
        "agm_acx_reservations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("job_id", UUID, sa.ForeignKey("agm_jobs.id"), nullable=False, unique=True),
        sa.Column("quote_id", sa.String(64), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("reserved_amount", sa.Float(), server_default="0"),
        sa.Column("settled_amount", sa.Float(), server_default="0"),
        sa.Column("status", sa.String(32), server_default="reserved"),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agm_acx_reservations_job_id", "agm_acx_reservations", ["job_id"], unique=True)
    op.create_index("ix_agm_acx_reservations_quote_id", "agm_acx_reservations", ["quote_id"])


def downgrade() -> None:
    op.drop_table("agm_acx_reservations")
    op.drop_table("agm_jobs")
    op.drop_table("agm_revisions")
    op.drop_table("agm_scenes")
