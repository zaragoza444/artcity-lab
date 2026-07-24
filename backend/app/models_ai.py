"""AI Core registry and control-plane models."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.enums import (
    AnnotationStatus,
    DatasetStatus,
    EvaluationStatus,
    ModelStatus,
    RightsStatus,
    TrainingJobStatus,
    UserRole,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.VIEWER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), unique=True, index=True)
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    email_verify_token: Mapped[Optional[str]] = mapped_column(String(128))
    phone_verify_code: Mapped[Optional[str]] = mapped_column(String(16))
    account_state: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255))
    detail: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), default="images")
    media_type: Mapped[str] = mapped_column(String(50), default="image")
    language: Mapped[Optional[str]] = mapped_column(String(50))
    dialect: Mapped[Optional[str]] = mapped_column(String(50))
    owner: Mapped[str] = mapped_column(String(255), default="Art City")
    source: Mapped[Optional[str]] = mapped_column(String(255))
    copyright_holder: Mapped[Optional[str]] = mapped_column(String(255))
    licence: Mapped[Optional[str]] = mapped_column(String(255))
    commercial_use: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_training_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    voice_cloning_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[str] = mapped_column(String(50), default="v1")
    status: Mapped[str] = mapped_column(String(50), default=DatasetStatus.RAW.value)
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024))
    checksum: Mapped[Optional[str]] = mapped_column(String(128))
    intended_model_use: Mapped[Optional[str]] = mapped_column(String(255))
    reviewer: Mapped[Optional[str]] = mapped_column(String(255))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RightsRecord(Base):
    __tablename__ = "rights_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    dataset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"))
    asset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("assets.id"))
    copyright_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    performer: Mapped[Optional[str]] = mapped_column(String(255))
    source_organisation: Mapped[Optional[str]] = mapped_column(String(255))
    contract_reference: Mapped[Optional[str]] = mapped_column(String(255))
    commercial_use: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_training: Mapped[bool] = mapped_column(Boolean, default=False)
    fine_tuning: Mapped[bool] = mapped_column(Boolean, default=False)
    voice_cloning: Mapped[bool] = mapped_column(Boolean, default=False)
    image_generation: Mapped[bool] = mapped_column(Boolean, default=False)
    geographic_restrictions: Mapped[Optional[str]] = mapped_column(Text)
    time_restrictions: Mapped[Optional[str]] = mapped_column(Text)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    consent_document_path: Mapped[Optional[str]] = mapped_column(String(1024))
    legal_status: Mapped[str] = mapped_column(String(50), default=RightsStatus.UNKNOWN.value)
    legal_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RegisteredModel(Base):
    __tablename__ = "registered_models"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), default="lora")
    base_model: Mapped[Optional[str]] = mapped_column(String(255))
    source: Mapped[Optional[str]] = mapped_column(String(255))
    licence: Mapped[Optional[str]] = mapped_column(String(255))
    commercial_use: Mapped[bool] = mapped_column(Boolean, default=False)
    owner: Mapped[str] = mapped_column(String(255), default="Art City")
    training_dataset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"))
    evaluation_dataset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"))
    training_method: Mapped[Optional[str]] = mapped_column(String(100))
    framework: Mapped[Optional[str]] = mapped_column(String(100))
    gpu_requirements: Mapped[Optional[str]] = mapped_column(String(255))
    checkpoint_path: Mapped[Optional[str]] = mapped_column(String(1024))
    checksum: Mapped[Optional[str]] = mapped_column(String(128))
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    known_limitations: Mapped[Optional[str]] = mapped_column(Text)
    character_key: Mapped[Optional[str]] = mapped_column(String(100))  # kardokh | kurdiya
    modality: Mapped[str] = mapped_column(String(50), default="image")
    status: Mapped[str] = mapped_column(String(50), default=ModelStatus.DRAFT.value)
    deployment_environment: Mapped[Optional[str]] = mapped_column(String(50))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deprecated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    model_type: Mapped[str] = mapped_column(String(100), default="lora")
    base_model: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"), nullable=False)
    evaluation_dataset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"))
    method: Mapped[str] = mapped_column(String(100), default="lora")
    config_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    epochs: Mapped[int] = mapped_column(Integer, default=1)
    learning_rate: Mapped[float] = mapped_column(Float, default=1e-4)
    batch_size: Mapped[int] = mapped_column(Integer, default=1)
    seed: Mapped[int] = mapped_column(Integer, default=42)
    gpu_type: Mapped[Optional[str]] = mapped_column(String(100))
    gpu_count: Mapped[int] = mapped_column(Integer, default=1)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default=TrainingJobStatus.DRAFT.value)
    checkpoint_path: Mapped[Optional[str]] = mapped_column(String(1024))
    logs_path: Mapped[Optional[str]] = mapped_column(String(1024))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    evaluation_result: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    resulting_model_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("registered_models.id"))
    initiated_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    approved_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    term: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(50), default="ku")
    dialect: Mapped[Optional[str]] = mapped_column(String(50))
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    child_friendly_definition: Mapped[Optional[str]] = mapped_column(Text)
    translation: Mapped[Optional[str]] = mapped_column(Text)
    example_sentence: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), default="terminology")
    source: Mapped[Optional[str]] = mapped_column(String(255))
    licence: Mapped[Optional[str]] = mapped_column(String(255))
    cultural_notes: Mapped[Optional[str]] = mapped_column(Text)
    pronunciation_audio_path: Mapped[Optional[str]] = mapped_column(String(1024))
    related_media: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    approval_status: Mapped[str] = mapped_column(String(50), default="draft")
    reviewer: Mapped[Optional[str]] = mapped_column(String(255))
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AnnotationTask(Base):
    __tablename__ = "annotation_tasks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    dataset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"), nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), default="text")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    labels: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(50), default=AnnotationStatus.PENDING.value)
    assignee_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    comments: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    revision_history: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    dataset_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"))
    source_type: Mapped[str] = mapped_column(String(50), default="upload")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    report: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    operator_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class DatasetFile(Base):
    __tablename__ = "dataset_files"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    dataset_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("datasets.id"), nullable=False, index=True)
    ingestion_run_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("ingestion_runs.id")
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(50), default="other")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[Optional[str]] = mapped_column(String(50))
    dialect: Mapped[Optional[str]] = mapped_column(String(50))
    rights_status: Mapped[str] = mapped_column(String(50), default=RightsStatus.UNKNOWN.value)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    soft_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    candidate_model_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("registered_models.id"))
    production_model_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("registered_models.id"))
    modality: Mapped[str] = mapped_column(String(50), default="image")
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(50), default=EvaluationStatus.PENDING.value)
    human_decision: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RouteRule(Base):
    __tablename__ = "route_rules"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    modality: Mapped[str] = mapped_column(String(50), nullable=False)
    character_key: Mapped[Optional[str]] = mapped_column(String(100))
    model_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("registered_models.id"))
    provider: Mapped[str] = mapped_column(String(100), default="artcity-image")
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
