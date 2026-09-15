"""AC Graphic Motion — MSG scenes, revisions, jobs, ACX reservations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AgmScene(Base):
    __tablename__ = "agm_scenes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    locale: Mapped[str] = mapped_column(String(32), default="ckb-IQ")
    direction: Mapped[str] = mapped_column(String(8), default="rtl")
    head_revision_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(128))
    etag: Mapped[Optional[str]] = mapped_column(String(128))
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    soft_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AgmRevision(Base):
    __tablename__ = "agm_revisions"
    __table_args__ = (UniqueConstraint("scene_id", "revision_no", name="uq_agm_revision_no"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    scene_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("agm_scenes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    graph_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    parent_revision_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("agm_revisions.id"))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgmJob(Base):
    __tablename__ = "agm_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    scene_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("agm_scenes.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False, index=True)
    revision_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("agm_revisions.id"), nullable=False, index=True)
    job_kind: Mapped[str] = mapped_column(String(32), nullable=False)  # preview|render
    status: Mapped[str] = mapped_column(String(32), default="queued")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    profile_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    request_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    outputs_json: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    error_code: Mapped[Optional[str]] = mapped_column(String(64))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    acx_quote_id: Mapped[Optional[str]] = mapped_column(String(64))
    acx_reservation_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False))
    parent_job_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("agm_jobs.id"))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AgmAcxReservation(Base):
    __tablename__ = "agm_acx_reservations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("agm_jobs.id"), nullable=False, unique=True, index=True)
    quote_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    reserved_amount: Mapped[float] = mapped_column(Float, default=0.0)
    settled_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="reserved")  # reserved|settled|reversed
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
