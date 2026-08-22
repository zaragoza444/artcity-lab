"""Vertical Drama IP Factory schema.

Revision ID: 0007_vertical_drama
Revises: 0006_production_hub
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_vertical_drama"
down_revision: Union[str, None] = "0006_production_hub"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=False)


def _pk() -> sa.Column:
    return sa.Column("id", UUID, primary_key=True)


def _ts() -> list:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.create_table(
        "vd_projects",
        _pk(),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("logline", sa.Text()),
        sa.Column("source_type", sa.String(50), server_default="idea"),
        sa.Column("production_mode", sa.String(50), server_default="ai_native"),
        sa.Column("primary_locale", sa.String(16), server_default="en"),
        sa.Column("content_languages", postgresql.JSONB(), server_default="[]"),
        sa.Column("format_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("row_version", sa.Integer(), server_default="1"),
        sa.Column("current_ip_title_id", UUID),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("updated_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("soft_deleted", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_projects_project_id", "vd_projects", ["project_id"], unique=True)

    op.create_table(
        "vd_ip_titles",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("logline", sa.Text()),
        sa.Column("genre", sa.String(128)),
        sa.Column("audience", sa.String(255)),
        sa.Column("language", sa.String(16), server_default="en"),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("row_version", sa.Integer(), server_default="1"),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_ip_titles_vd_project_id", "vd_ip_titles", ["vd_project_id"])
    op.create_index("ix_vd_ip_titles_project_id", "vd_ip_titles", ["project_id"])

    op.create_table(
        "vd_rights_records",
        _pk(),
        sa.Column("ip_title_id", UUID, sa.ForeignKey("vd_ip_titles.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("territory", sa.String(64), server_default="IQ"),
        sa.Column("window", sa.String(128)),
        sa.Column("rights_type", sa.String(64), server_default="original"),
        sa.Column("status", sa.String(50), server_default="declared"),
        sa.Column("notes", sa.Text()),
        sa.Column("blocks_delivery", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_rights_ip_title_id", "vd_rights_records", ["ip_title_id"])

    op.create_table(
        "vd_contributors",
        _pk(),
        sa.Column("ip_title_id", UUID, sa.ForeignKey("vd_ip_titles.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(64), server_default="creator"),
        sa.Column("contribution", sa.Text()),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "vd_provenance_entries",
        _pk(),
        sa.Column("ip_title_id", UUID, sa.ForeignKey("vd_ip_titles.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "vd_characters",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("locale", sa.String(16), server_default="en"),
        sa.Column("bible_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("identity_locked", sa.Boolean(), server_default=sa.false()),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_characters_vd_project_id", "vd_characters", ["vd_project_id"])

    op.create_table(
        "vd_character_variants",
        _pk(),
        sa.Column("character_id", UUID, sa.ForeignKey("vd_characters.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("asset_id", UUID, sa.ForeignKey("assets.id")),
        sa.Column("approved", sa.Boolean(), server_default=sa.false()),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "vd_canon_facts",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("entity_type", sa.String(64), server_default="world"),
        sa.Column("entity_id", UUID),
        sa.Column("fact_key", sa.String(128), nullable=False),
        sa.Column("fact_value", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("superseded_by", UUID),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("approved_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_canon_facts_vd_project_id", "vd_canon_facts", ["vd_project_id"])

    op.create_table(
        "vd_locations",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("locale", sa.String(16), server_default="en"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_props",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_wardrobe_items",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("character_id", UUID, sa.ForeignKey("vd_characters.id")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "vd_story_bibles",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(255), server_default="Story Bible"),
        sa.Column("current_version_id", UUID),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_story_bible_versions",
        _pk(),
        sa.Column("story_bible_id", UUID, sa.ForeignKey("vd_story_bibles.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("version_label", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("sections_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("approved_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "vd_seasons",
        _pk(),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("season_number", sa.Integer(), server_default="1"),
        sa.Column("title", sa.String(255), server_default="Season 1"),
        sa.Column("target_episode_count", sa.Integer(), server_default="10"),
        sa.Column("target_episode_seconds", sa.Integer(), server_default="90"),
        sa.Column("story_bible_version_id", UUID, sa.ForeignKey("vd_story_bible_versions.id")),
        sa.Column("arc_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "vd_episodes",
        _pk(),
        sa.Column("season_id", UUID, sa.ForeignKey("vd_seasons.id"), nullable=False),
        sa.Column("vd_project_id", UUID, sa.ForeignKey("vd_projects.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("hook", sa.Text()),
        sa.Column("key_beat", sa.Text()),
        sa.Column("reveal", sa.Text()),
        sa.Column("cliffhanger", sa.Text()),
        sa.Column("status", sa.String(50), server_default="planned"),
        sa.Column("current_version_id", UUID),
        sa.Column("stale", sa.Boolean(), server_default=sa.false()),
        sa.Column("stale_reason", sa.Text()),
        sa.Column("hub_script_version_id", UUID),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("season_id", "episode_number", name="uq_vd_episode_number"),
    )
    op.create_index("ix_vd_episodes_season_id", "vd_episodes", ["season_id"])

    op.create_table(
        "vd_episode_versions",
        _pk(),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("version_label", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("outline_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("screenplay_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_episode_beats",
        _pk(),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0"),
        sa.Column("beat_type", sa.String(64), server_default="turn"),
        sa.Column("display_text", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "vd_scenes",
        _pk(),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("scene_number", sa.Integer(), server_default="1"),
        sa.Column("heading", sa.String(255), server_default=""),
        sa.Column("synopsis", sa.Text()),
        sa.Column("duration_seconds", sa.Integer(), server_default="8"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_shots",
        _pk(),
        sa.Column("scene_id", UUID, sa.ForeignKey("vd_scenes.id"), nullable=False),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("shot_number", sa.Integer(), server_default="1"),
        sa.Column("framing", sa.String(64), server_default="MCU"),
        sa.Column("action", sa.Text()),
        sa.Column("duration_seconds", sa.Integer(), server_default="3"),
        sa.Column("aspect", sa.String(16), server_default="9:16"),
        sa.Column("character_id", UUID, sa.ForeignKey("vd_characters.id")),
        sa.Column("selected_asset_id", UUID, sa.ForeignKey("assets.id")),
        sa.Column("status", sa.String(50), server_default="planned"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_shots_scene_id", "vd_shots", ["scene_id"])

    op.create_table(
        "vd_generation_jobs",
        _pk(),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("shot_id", UUID, sa.ForeignKey("vd_shots.id")),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id")),
        sa.Column("workflow_key", sa.String(128), nullable=False),
        sa.Column("capability", sa.String(64), server_default="image"),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("status", sa.String(50), server_default="queued"),
        sa.Column("provider", sa.String(100)),
        sa.Column("model", sa.String(255)),
        sa.Column("prompt", sa.Text()),
        sa.Column("cost", sa.Numeric(12, 4)),
        sa.Column("result_asset_id", UUID, sa.ForeignKey("assets.id")),
        sa.Column("gateway_job_id", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("provenance_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_generation_jobs_idempotency_key", "vd_generation_jobs", ["idempotency_key"])

    op.create_table(
        "vd_qc_runs",
        _pk(),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("passed", sa.Boolean(), server_default=sa.false()),
        sa.Column("blocking_count", sa.Integer(), server_default="0"),
        sa.Column("warning_count", sa.Integer(), server_default="0"),
        sa.Column("findings_json", postgresql.JSONB(), server_default="[]"),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_subtitle_tracks",
        _pk(),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("source_version_id", UUID),
        sa.Column("kind", sa.String(32), server_default="subtitle"),
        sa.Column("body", sa.Text(), server_default=""),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_episode_assemblies",
        _pk(),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("edit_asset_id", UUID, sa.ForeignKey("assets.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_delivery_packages",
        _pk(),
        sa.Column("episode_id", UUID, sa.ForeignKey("vd_episodes.id"), nullable=False),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("manifest_json", postgresql.JSONB(), server_default="{}"),
        sa.Column("asset_id", UUID, sa.ForeignKey("assets.id")),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "vd_domain_events",
        _pk(),
        sa.Column("project_id", UUID, sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", UUID, nullable=False),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vd_domain_events_project_id", "vd_domain_events", ["project_id"])


def downgrade() -> None:
    for table in [
        "vd_domain_events",
        "vd_delivery_packages",
        "vd_episode_assemblies",
        "vd_subtitle_tracks",
        "vd_qc_runs",
        "vd_generation_jobs",
        "vd_shots",
        "vd_scenes",
        "vd_episode_beats",
        "vd_episode_versions",
        "vd_episodes",
        "vd_seasons",
        "vd_story_bible_versions",
        "vd_story_bibles",
        "vd_wardrobe_items",
        "vd_props",
        "vd_locations",
        "vd_canon_facts",
        "vd_character_variants",
        "vd_characters",
        "vd_provenance_entries",
        "vd_contributors",
        "vd_rights_records",
        "vd_ip_titles",
        "vd_projects",
    ]:
        op.drop_table(table)
