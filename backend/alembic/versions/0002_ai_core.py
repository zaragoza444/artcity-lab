"""Art City AI Core tables, auth, generation provenance.

Revision ID: 0002_ai_core
Revises: 0001_initial
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_ai_core"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("totp_enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("detail", postgresql.JSONB()),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100)),
        sa.Column("media_type", sa.String(50)),
        sa.Column("language", sa.String(50)),
        sa.Column("dialect", sa.String(50)),
        sa.Column("owner", sa.String(255)),
        sa.Column("source", sa.String(255)),
        sa.Column("copyright_holder", sa.String(255)),
        sa.Column("licence", sa.String(255)),
        sa.Column("commercial_use", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("ai_training_permission", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("voice_cloning_permission", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("record_count", sa.Integer(), server_default="0"),
        sa.Column("size_bytes", sa.Integer(), server_default="0"),
        sa.Column("version", sa.String(50)),
        sa.Column("status", sa.String(50)),
        sa.Column("storage_path", sa.String(1024)),
        sa.Column("checksum", sa.String(128)),
        sa.Column("intended_model_use", sa.String(255)),
        sa.Column("reviewer", sa.String(255)),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "rights_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id")),
        sa.Column("asset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("assets.id")),
        sa.Column("copyright_owner", sa.String(255), nullable=False),
        sa.Column("performer", sa.String(255)),
        sa.Column("source_organisation", sa.String(255)),
        sa.Column("contract_reference", sa.String(255)),
        sa.Column("commercial_use", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("ai_training", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("fine_tuning", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("voice_cloning", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("image_generation", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("geographic_restrictions", sa.Text()),
        sa.Column("time_restrictions", sa.Text()),
        sa.Column("expiry_date", sa.DateTime(timezone=True)),
        sa.Column("consent_document_path", sa.String(1024)),
        sa.Column("legal_status", sa.String(50)),
        sa.Column("legal_notes", sa.Text()),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "registered_models",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("model_type", sa.String(100)),
        sa.Column("base_model", sa.String(255)),
        sa.Column("source", sa.String(255)),
        sa.Column("licence", sa.String(255)),
        sa.Column("commercial_use", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("owner", sa.String(255)),
        sa.Column("training_dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id")),
        sa.Column("evaluation_dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id")),
        sa.Column("training_method", sa.String(100)),
        sa.Column("framework", sa.String(100)),
        sa.Column("gpu_requirements", sa.String(255)),
        sa.Column("checkpoint_path", sa.String(1024)),
        sa.Column("checksum", sa.String(128)),
        sa.Column("quality_score", sa.Float()),
        sa.Column("known_limitations", sa.Text()),
        sa.Column("character_key", sa.String(100)),
        sa.Column("modality", sa.String(50)),
        sa.Column("status", sa.String(50)),
        sa.Column("deployment_environment", sa.String(50)),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("deprecated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "training_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("model_type", sa.String(100)),
        sa.Column("base_model", sa.String(255), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("evaluation_dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id")),
        sa.Column("method", sa.String(100)),
        sa.Column("config_json", postgresql.JSONB()),
        sa.Column("epochs", sa.Integer()),
        sa.Column("learning_rate", sa.Float()),
        sa.Column("batch_size", sa.Integer()),
        sa.Column("seed", sa.Integer()),
        sa.Column("gpu_type", sa.String(100)),
        sa.Column("gpu_count", sa.Integer()),
        sa.Column("estimated_cost", sa.Float()),
        sa.Column("actual_cost", sa.Float()),
        sa.Column("status", sa.String(50)),
        sa.Column("checkpoint_path", sa.String(1024)),
        sa.Column("logs_path", sa.String(1024)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("evaluation_result", postgresql.JSONB()),
        sa.Column("resulting_model_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("registered_models.id")),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("approved_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "knowledge_entries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("term", sa.String(255), nullable=False),
        sa.Column("language", sa.String(50)),
        sa.Column("dialect", sa.String(50)),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("child_friendly_definition", sa.Text()),
        sa.Column("translation", sa.Text()),
        sa.Column("example_sentence", sa.Text()),
        sa.Column("category", sa.String(100)),
        sa.Column("source", sa.String(255)),
        sa.Column("licence", sa.String(255)),
        sa.Column("cultural_notes", sa.Text()),
        sa.Column("pronunciation_audio_path", sa.String(1024)),
        sa.Column("related_media", postgresql.JSONB()),
        sa.Column("approval_status", sa.String(50)),
        sa.Column("reviewer", sa.String(255)),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_knowledge_entries_term", "knowledge_entries", ["term"])

    op.create_table(
        "annotation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("media_type", sa.String(50)),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column("labels", postgresql.JSONB()),
        sa.Column("status", sa.String(50)),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("comments", postgresql.JSONB()),
        sa.Column("revision_history", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id")),
        sa.Column("source_type", sa.String(50)),
        sa.Column("status", sa.String(50)),
        sa.Column("report", postgresql.JSONB()),
        sa.Column("operator_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("candidate_model_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("registered_models.id")),
        sa.Column("production_model_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("registered_models.id")),
        sa.Column("modality", sa.String(50)),
        sa.Column("metrics", postgresql.JSONB()),
        sa.Column("status", sa.String(50)),
        sa.Column("human_decision", sa.String(50)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "route_rules",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("modality", sa.String(50), nullable=False),
        sa.Column("character_key", sa.String(100)),
        sa.Column("model_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("registered_models.id")),
        sa.Column("provider", sa.String(100)),
        sa.Column("priority", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.add_column("generation_jobs", sa.Column("model_version", sa.String(50)))
    op.add_column("generation_jobs", sa.Column("registered_model_id", sa.String(36)))
    op.add_column("generation_jobs", sa.Column("dataset_id", sa.String(36)))
    op.add_column("generation_jobs", sa.Column("character_key", sa.String(100)))
    op.add_column("generation_jobs", sa.Column("requested_by", sa.String(36)))
    op.add_column("generation_jobs", sa.Column("params_json", postgresql.JSONB()))


def downgrade() -> None:
    op.drop_column("generation_jobs", "params_json")
    op.drop_column("generation_jobs", "requested_by")
    op.drop_column("generation_jobs", "character_key")
    op.drop_column("generation_jobs", "dataset_id")
    op.drop_column("generation_jobs", "registered_model_id")
    op.drop_column("generation_jobs", "model_version")
    for table in [
        "route_rules",
        "evaluation_runs",
        "ingestion_runs",
        "annotation_tasks",
        "knowledge_entries",
        "training_jobs",
        "registered_models",
        "rights_records",
        "datasets",
        "audit_logs",
        "users",
    ]:
        op.drop_table(table)
