"""Art City Production Hub — pre-production canonical models (AC Script first)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class HubScript(Base):
    __tablename__ = "hub_scripts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    entry_mode: Mapped[str] = mapped_column(String(50), default="blank")
    primary_locale: Mapped[str] = mapped_column(String(16), default="en")
    content_languages: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    current_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    updated_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HubScriptVersion(Base):
    __tablename__ = "hub_script_versions"
    __table_args__ = (UniqueConstraint("script_id", "version_label", name="uq_hub_script_version_label"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    script_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_scripts.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    version_label: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft|revision|shooting|locked
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    parent_version_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_script_versions.id"))
    page_eighths: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HubScriptElement(Base):
    __tablename__ = "hub_script_elements"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    script_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("hub_script_versions.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    element_type: Mapped[str] = mapped_column(String(50), nullable=False)
    display_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    search_normalized: Mapped[Optional[str]] = mapped_column(Text)
    scene_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_scenes.id"))
    character_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_characters.id"))
    locale: Mapped[Optional[str]] = mapped_column(String(16))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HubScene(Base):
    __tablename__ = "hub_scenes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    script_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("hub_script_versions.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    scene_number: Mapped[str] = mapped_column(String(32), nullable=False)
    int_ext: Mapped[Optional[str]] = mapped_column(String(16))
    location_name: Mapped[Optional[str]] = mapped_column(String(255))
    time_of_day: Mapped[Optional[str]] = mapped_column(String(64))
    heading_display: Mapped[Optional[str]] = mapped_column(Text)
    page_eighths: Mapped[int] = mapped_column(Integer, default=8)
    synopsis: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    location_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_locations.id"))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HubCharacter(Base):
    __tablename__ = "hub_characters"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    script_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_scripts.id"))
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    search_normalized: Mapped[Optional[str]] = mapped_column(Text)
    bible_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HubLocation(Base):
    __tablename__ = "hub_locations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    script_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_scripts.id"))
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    search_normalized: Mapped[Optional[str]] = mapped_column(Text)
    bible_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HubBreakdownItem(Base):
    __tablename__ = "hub_breakdown_items"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    script_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("hub_script_versions.id"), nullable=False, index=True
    )
    scene_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_scenes.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    display_text: Mapped[str] = mapped_column(Text, nullable=False)
    search_normalized: Mapped[Optional[str]] = mapped_column(Text)
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    approval_status: Mapped[str] = mapped_column(String(32), default="proposed")  # proposed|approved|rejected
    source: Mapped[str] = mapped_column(String(32), default="ai")  # ai|human
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    updated_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HubDomainEvent(Base):
    __tablename__ = "hub_domain_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HubStaleFlag(Base):
    __tablename__ = "hub_stale_flags"
    __table_args__ = (
        UniqueConstraint("project_id", "resource_type", "resource_id", name="uq_hub_stale_resource"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    caused_by_event_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("hub_domain_events.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
