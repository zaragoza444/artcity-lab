from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.enums import AssetType, GenerationStatus, MediaModality, ReviewDecision, UserRole


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active")
    budget_limit: Mapped[Optional[float]] = mapped_column(Float)
    primary_locale: Mapped[str] = mapped_column(String(16), default="en")
    content_languages: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Baghdad")
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    production_status: Mapped[str] = mapped_column(String(50), default="pre_production")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    characters: Mapped[list["Character"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    scripts: Mapped[list["Script"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    assets: Mapped[list["Asset"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    generation_jobs: Mapped[list["GenerationJob"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    cost_records: Mapped[list["CostRecord"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    identity_rules: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    costume_notes: Mapped[Optional[str]] = mapped_column(Text)
    voice_profile: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    reference_paths: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="characters")


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="ku")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="scripts")
    scenes: Mapped[list["Scene"]] = relationship(back_populates="script", cascade="all, delete-orphan")


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    script_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("scripts.id"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    script: Mapped["Script"] = relationship(back_populates="scenes")
    shots: Mapped[list["Shot"]] = relationship(back_populates="scene", cascade="all, delete-orphan")


class Shot(Base):
    __tablename__ = "shots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    scene_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("scenes.id"), nullable=False)
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    camera_movement: Mapped[Optional[str]] = mapped_column(String(255))
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scene: Mapped["Scene"] = relationship(back_populates="shots")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), default=AssetType.OTHER.value)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024))
    checksum: Mapped[Optional[str]] = mapped_column(String(128))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    soft_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="assets")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    modality: Mapped[str] = mapped_column(String(50), default=MediaModality.IMAGE.value)
    provider: Mapped[str] = mapped_column(String(100), default="stub")
    model: Mapped[Optional[str]] = mapped_column(String(255))
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    registered_model_id: Mapped[Optional[str]] = mapped_column(String(36))
    dataset_id: Mapped[Optional[str]] = mapped_column(String(36))
    character_key: Mapped[Optional[str]] = mapped_column(String(100))
    requested_by: Mapped[Optional[str]] = mapped_column(String(36))
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default=GenerationStatus.PENDING.value)
    result_uri: Mapped[Optional[str]] = mapped_column(String(1024))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float)
    provider_job_id: Mapped[Optional[str]] = mapped_column(String(255))
    params_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="generation_jobs")
    reviews: Mapped[list["Review"]] = relationship(back_populates="generation_job", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    generation_job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("generation_jobs.id"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(50), default=ReviewDecision.REQUEST_CHANGES.value)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewer_role: Mapped[str] = mapped_column(String(50), default=UserRole.REVIEWER.value)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    generation_job: Mapped["GenerationJob"] = relationship(back_populates="reviews")


class CostRecord(Base):
    __tablename__ = "cost_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    generation_job_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("generation_jobs.id")
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="cost_records")


# AI Core models (re-export)
from app.models_ai import (  # noqa: E402
    AnnotationTask,
    AuditLog,
    Dataset,
    DatasetFile,
    EvaluationRun,
    IngestionRun,
    KnowledgeEntry,
    RegisteredModel,
    RightsRecord,
    RouteRule,
    TrainingJob,
    User,
)

__all__ = [
    "Project",
    "Character",
    "Script",
    "Scene",
    "Shot",
    "Asset",
    "GenerationJob",
    "Review",
    "CostRecord",
    "User",
    "AuditLog",
    "Dataset",
    "DatasetFile",
    "RightsRecord",
    "RegisteredModel",
    "TrainingJob",
    "KnowledgeEntry",
    "AnnotationTask",
    "IngestionRun",
    "EvaluationRun",
    "RouteRule",
]
