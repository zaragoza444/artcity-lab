"""Production Hub — Alembic migration.

Revision ID: 0006_production_hub
Revises: 0005_customer_signup
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_production_hub"
down_revision: Union[str, None] = "0005_customer_signup"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("primary_locale", sa.String(16), server_default="en", nullable=False))
    op.add_column("projects", sa.Column("content_languages", postgresql.JSONB(), server_default="[]", nullable=True))
    op.add_column("projects", sa.Column("timezone", sa.String(64), server_default="Asia/Baghdad", nullable=False))
    op.add_column("projects", sa.Column("currency", sa.String(8), server_default="USD", nullable=False))
    op.add_column(
        "projects",
        sa.Column("production_status", sa.String(50), server_default="pre_production", nullable=False),
    )

    op.create_table(
        "hub_scripts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("entry_mode", sa.String(50), server_default="blank"),
        sa.Column("primary_locale", sa.String(16), server_default="en"),
        sa.Column("content_languages", postgresql.JSONB(), server_default="[]"),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hub_scripts_project_id", "hub_scripts", ["project_id"])

    op.create_table(
        "hub_script_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("script_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_scripts.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("version_label", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_script_versions.id")),
        sa.Column("page_eighths", sa.Integer(), server_default="0"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("script_id", "version_label", name="uq_hub_script_version_label"),
    )
    op.create_index("ix_hub_script_versions_script_id", "hub_script_versions", ["script_id"])
    op.create_index("ix_hub_script_versions_project_id", "hub_script_versions", ["project_id"])

    op.create_table(
        "hub_characters",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("script_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_scripts.id")),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("search_normalized", sa.Text()),
        sa.Column("bible_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hub_characters_project_id", "hub_characters", ["project_id"])

    op.create_table(
        "hub_locations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("script_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_scripts.id")),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("search_normalized", sa.Text()),
        sa.Column("bible_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hub_locations_project_id", "hub_locations", ["project_id"])

    op.create_table(
        "hub_scenes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "script_version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hub_script_versions.id"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("scene_number", sa.String(32), nullable=False),
        sa.Column("int_ext", sa.String(16)),
        sa.Column("location_name", sa.String(255)),
        sa.Column("time_of_day", sa.String(64)),
        sa.Column("heading_display", sa.Text()),
        sa.Column("page_eighths", sa.Integer(), server_default="8"),
        sa.Column("synopsis", sa.Text()),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("location_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_locations.id")),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hub_scenes_script_version_id", "hub_scenes", ["script_version_id"])
    op.create_index("ix_hub_scenes_project_id", "hub_scenes", ["project_id"])

    op.create_table(
        "hub_script_elements",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "script_version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hub_script_versions.id"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("element_type", sa.String(50), nullable=False),
        sa.Column("display_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("search_normalized", sa.Text()),
        sa.Column("scene_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_scenes.id")),
        sa.Column("character_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_characters.id")),
        sa.Column("locale", sa.String(16)),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hub_script_elements_script_version_id", "hub_script_elements", ["script_version_id"])
    op.create_index("ix_hub_script_elements_project_id", "hub_script_elements", ["project_id"])

    op.create_table(
        "hub_breakdown_items",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "script_version_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hub_script_versions.id"),
            nullable=False,
        ),
        sa.Column("scene_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_scenes.id"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("display_text", sa.Text(), nullable=False),
        sa.Column("search_normalized", sa.Text()),
        sa.Column("quantity", sa.Numeric(12, 2)),
        sa.Column("approval_status", sa.String(32), server_default="proposed"),
        sa.Column("source", sa.String(32), server_default="ai"),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hub_breakdown_items_project_id", "hub_breakdown_items", ["project_id"])
    op.create_index("ix_hub_breakdown_items_script_version_id", "hub_breakdown_items", ["script_version_id"])
    op.create_index("ix_hub_breakdown_items_scene_id", "hub_breakdown_items", ["scene_id"])

    op.create_table(
        "hub_domain_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hub_domain_events_project_id", "hub_domain_events", ["project_id"])

    op.create_table(
        "hub_stale_flags",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("caused_by_event_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("hub_domain_events.id")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "resource_type", "resource_id", name="uq_hub_stale_resource"),
    )
    op.create_index("ix_hub_stale_flags_project_id", "hub_stale_flags", ["project_id"])


def downgrade() -> None:
    op.drop_table("hub_stale_flags")
    op.drop_table("hub_domain_events")
    op.drop_table("hub_breakdown_items")
    op.drop_table("hub_script_elements")
    op.drop_table("hub_scenes")
    op.drop_table("hub_locations")
    op.drop_table("hub_characters")
    op.drop_table("hub_script_versions")
    op.drop_table("hub_scripts")
    op.drop_column("projects", "production_status")
    op.drop_column("projects", "currency")
    op.drop_column("projects", "timezone")
    op.drop_column("projects", "content_languages")
    op.drop_column("projects", "primary_locale")
