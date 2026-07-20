"""Data Lab dataset file inventory.

Revision ID: 0003_data_lab_files
Revises: 0002_ai_core
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_data_lab_files"
down_revision: Union[str, None] = "0002_ai_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dataset_files",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column(
            "ingestion_run_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("ingestion_runs.id"),
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("checksum", sa.String(128), nullable=False),
        sa.Column("content_type", sa.String(255)),
        sa.Column("media_type", sa.String(50), server_default="other"),
        sa.Column("size_bytes", sa.Integer(), server_default="0"),
        sa.Column("language", sa.String(50)),
        sa.Column("dialect", sa.String(50)),
        sa.Column("rights_status", sa.String(50), server_default="unknown"),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("soft_deleted", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_dataset_files_dataset_id", "dataset_files", ["dataset_id"])
    op.create_index("ix_dataset_files_checksum", "dataset_files", ["dataset_id", "checksum"])


def downgrade() -> None:
    op.drop_index("ix_dataset_files_checksum", table_name="dataset_files")
    op.drop_index("ix_dataset_files_dataset_id", table_name="dataset_files")
    op.drop_table("dataset_files")
