"""Vertical Drama IP Factory — domain models (Sprints 0–4)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class VdProject(Base):
    __tablename__ = "vd_projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    logline: Mapped[Optional[str]] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50), default="idea")  # idea|generate|import
    production_mode: Mapped[str] = mapped_column(String(50), default="ai_native")
    primary_locale: Mapped[str] = mapped_column(String(16), default="en")
    content_languages: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    format_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="active")
    row_version: Mapped[int] = mapped_column(Integer, default=1)
    current_ip_title_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    updated_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    soft_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdIpTitle(Base):
    __tablename__ = "vd_ip_titles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    logline: Mapped[Optional[str]] = mapped_column(Text)
    genre: Mapped[Optional[str]] = mapped_column(String(128))
    audience: Mapped[Optional[str]] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(16), default="en")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    row_version: Mapped[int] = mapped_column(Integer, default=1)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdRightsRecord(Base):
    __tablename__ = "vd_rights_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    ip_title_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_ip_titles.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    territory: Mapped[str] = mapped_column(String(64), default="IQ")
    window: Mapped[Optional[str]] = mapped_column(String(128))
    rights_type: Mapped[str] = mapped_column(String(64), default="original")
    status: Mapped[str] = mapped_column(String(50), default="declared")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    blocks_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdContributor(Base):
    __tablename__ = "vd_contributors"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    ip_title_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_ip_titles.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="creator")
    contribution: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdProvenanceEntry(Base):
    __tablename__ = "vd_provenance_entries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    ip_title_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_ip_titles.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdCharacter(Base):
    __tablename__ = "vd_characters"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="en")
    bible_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    identity_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdCharacterVariant(Base):
    __tablename__ = "vd_character_variants"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    character_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_characters.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id"))
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdCanonFact(Base):
    __tablename__ = "vd_canon_facts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="world")
    entity_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    fact_key: Mapped[str] = mapped_column(String(128), nullable=False)
    fact_value: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft|approved|locked|superseded
    superseded_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    approved_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdLocation(Base):
    __tablename__ = "vd_locations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="en")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdProp(Base):
    __tablename__ = "vd_props"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdWardrobeItem(Base):
    __tablename__ = "vd_wardrobe_items"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    character_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_characters.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdStoryBible(Base):
    __tablename__ = "vd_story_bibles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="Story Bible")
    current_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdStoryBibleVersion(Base):
    __tablename__ = "vd_story_bible_versions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    story_bible_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_story_bibles.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    version_label: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    sections_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    approved_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdSeason(Base):
    __tablename__ = "vd_seasons"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    season_number: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(255), default="Season 1")
    target_episode_count: Mapped[int] = mapped_column(Integer, default=10)
    target_episode_seconds: Mapped[int] = mapped_column(Integer, default=90)
    story_bible_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_story_bible_versions.id"))
    arc_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdEpisode(Base):
    __tablename__ = "vd_episodes"
    __table_args__ = (UniqueConstraint("season_id", "episode_number", name="uq_vd_episode_number"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    season_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_seasons.id"), nullable=False, index=True)
    vd_project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_projects.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    hook: Mapped[Optional[str]] = mapped_column(Text)
    key_beat: Mapped[Optional[str]] = mapped_column(Text)
    reveal: Mapped[Optional[str]] = mapped_column(Text)
    cliffhanger: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="planned")
    current_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    stale: Mapped[bool] = mapped_column(Boolean, default=False)
    stale_reason: Mapped[Optional[str]] = mapped_column(Text)
    hub_script_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdEpisodeVersion(Base):
    __tablename__ = "vd_episode_versions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    version_label: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    outline_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    screenplay_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdEpisodeBeat(Base):
    __tablename__ = "vd_episode_beats"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    beat_type: Mapped[str] = mapped_column(String(64), default="turn")
    display_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdScene(Base):
    __tablename__ = "vd_scenes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    scene_number: Mapped[int] = mapped_column(Integer, default=1)
    heading: Mapped[str] = mapped_column(String(255), default="")
    synopsis: Mapped[Optional[str]] = mapped_column(Text)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=8)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdShot(Base):
    __tablename__ = "vd_shots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    scene_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_scenes.id"), nullable=False, index=True)
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    shot_number: Mapped[int] = mapped_column(Integer, default=1)
    framing: Mapped[str] = mapped_column(String(64), default="MCU")
    action: Mapped[Optional[str]] = mapped_column(Text)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=3)
    aspect: Mapped[str] = mapped_column(String(16), default="9:16")
    character_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_characters.id"))
    selected_asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id"))
    status: Mapped[str] = mapped_column(String(50), default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdGenerationJob(Base):
    __tablename__ = "vd_generation_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    shot_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_shots.id"), index=True)
    episode_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"))
    workflow_key: Mapped[str] = mapped_column(String(128), nullable=False)
    capability: Mapped[str] = mapped_column(String(64), default="image")
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    provider: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(255))
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    result_asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id"))
    gateway_job_id: Mapped[Optional[str]] = mapped_column(String(64))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    provenance_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VdQcRun(Base):
    __tablename__ = "vd_qc_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    blocking_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    findings_json: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdSubtitleTrack(Base):
    __tablename__ = "vd_subtitle_tracks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    source_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    kind: Mapped[str] = mapped_column(String(32), default="subtitle")  # subtitle|dub|adaptation
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdAssembly(Base):
    __tablename__ = "vd_episode_assemblies"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    manifest_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    edit_asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdDeliveryPackage(Base):
    __tablename__ = "vd_delivery_packages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vd_episodes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    manifest_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id"))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VdDomainEvent(Base):
    __tablename__ = "vd_domain_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
