from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, client_ip, require_roles
from app.core.enums import (
    DATASET_UPLOAD_ROLES,
    MODEL_PROMOTE_ROLES,
    RIGHTS_APPROVE_ROLES,
    TRAINING_ROLES,
    DatasetStatus,
    ModelStatus,
    RightsStatus,
    TrainingJobStatus,
    UserRole,
)
from app.models import Dataset, RegisteredModel, RightsRecord, TrainingJob, User
from app.services.audit import write_audit
from app.services.rights_gate import assert_dataset_trainable

router = APIRouter(tags=["registries"])


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "images"
    media_type: str = "image"
    language: Optional[str] = None
    dialect: Optional[str] = None
    owner: str = "Art City"
    source: Optional[str] = None
    copyright_holder: Optional[str] = None
    licence: Optional[str] = None
    commercial_use: bool = False
    ai_training_permission: bool = False
    voice_cloning_permission: bool = False
    version: str = "v1"
    intended_model_use: Optional[str] = None


class DatasetOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str
    media_type: str
    language: Optional[str]
    dialect: Optional[str]
    owner: str
    licence: Optional[str]
    commercial_use: bool
    ai_training_permission: bool
    voice_cloning_permission: bool
    record_count: int
    size_bytes: int
    version: str
    status: str
    storage_path: Optional[str]
    checksum: Optional[str]
    intended_model_use: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetStatusUpdate(BaseModel):
    status: str


class RightsCreate(BaseModel):
    dataset_id: Optional[str] = None
    asset_id: Optional[str] = None
    copyright_owner: str
    performer: Optional[str] = None
    source_organisation: Optional[str] = None
    contract_reference: Optional[str] = None
    commercial_use: bool = False
    ai_training: bool = False
    fine_tuning: bool = False
    voice_cloning: bool = False
    image_generation: bool = False
    legal_status: str = RightsStatus.UNKNOWN.value
    legal_notes: Optional[str] = None


class RightsOut(BaseModel):
    id: str
    dataset_id: Optional[str]
    asset_id: Optional[str]
    copyright_owner: str
    commercial_use: bool
    ai_training: bool
    fine_tuning: bool
    voice_cloning: bool
    image_generation: bool
    legal_status: str
    legal_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelCreate(BaseModel):
    name: str
    version: str
    model_type: str = "lora"
    base_model: Optional[str] = None
    licence: Optional[str] = None
    commercial_use: bool = False
    training_dataset_id: Optional[str] = None
    character_key: Optional[str] = None
    modality: str = "image"
    checkpoint_path: Optional[str] = None
    checksum: Optional[str] = None


class ModelOut(BaseModel):
    id: str
    name: str
    version: str
    model_type: str
    base_model: Optional[str]
    licence: Optional[str]
    commercial_use: bool
    owner: str
    training_dataset_id: Optional[str]
    character_key: Optional[str]
    modality: str
    status: str
    checkpoint_path: Optional[str]
    checksum: Optional[str]
    quality_score: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelStatusUpdate(BaseModel):
    status: str


class TrainingCreate(BaseModel):
    base_model: str
    dataset_id: str
    evaluation_dataset_id: Optional[str] = None
    method: str = "lora"
    epochs: int = 1
    learning_rate: float = 1e-4
    batch_size: int = 1
    seed: int = 42
    gpu_type: Optional[str] = "cloud-a10"
    estimated_cost: Optional[float] = None
    model_name: Optional[str] = None
    character_key: Optional[str] = None


class TrainingOut(BaseModel):
    id: str
    model_type: str
    base_model: str
    dataset_id: str
    status: str
    epochs: int
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    resulting_model_id: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/api/datasets", response_model=list[DatasetOut])
def list_datasets(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.post("/api/datasets", response_model=DatasetOut, status_code=201)
def create_dataset(
    payload: DatasetCreate,
    request: Request,
    user: User = Depends(require_roles(*DATASET_UPLOAD_ROLES)),
    db: Session = Depends(get_db),
):
    ds = Dataset(**payload.model_dump(), created_by=user.id, status=DatasetStatus.RAW.value)
    db.add(ds)
    write_audit(
        db,
        action="dataset_create",
        resource_type="dataset",
        user_id=user.id,
        detail={"name": payload.name},
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(ds)
    return ds


@router.patch("/api/datasets/{dataset_id}/status", response_model=DatasetOut)
def update_dataset_status(
    dataset_id: str,
    payload: DatasetStatusUpdate,
    user: User = Depends(require_roles(*RIGHTS_APPROVE_ROLES, UserRole.AI_OPERATOR)),
    db: Session = Depends(get_db),
):
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if payload.status == DatasetStatus.TRAINING_READY.value:
        if not ds.ai_training_permission:
            raise HTTPException(status_code=400, detail="AI-training permission required")
    ds.status = payload.status
    db.commit()
    db.refresh(ds)
    return ds


@router.get("/api/rights", response_model=list[RightsOut])
def list_rights(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(RightsRecord).order_by(RightsRecord.created_at.desc()).all()


@router.post("/api/rights", response_model=RightsOut, status_code=201)
def create_rights(
    payload: RightsCreate,
    request: Request,
    user: User = Depends(require_roles(*RIGHTS_APPROVE_ROLES)),
    db: Session = Depends(get_db),
):
    rec = RightsRecord(**payload.model_dump(), created_by=user.id)
    db.add(rec)
    if payload.dataset_id and payload.ai_training:
        ds = db.get(Dataset, payload.dataset_id)
        if ds:
            ds.ai_training_permission = True
    write_audit(
        db,
        action="rights_create",
        resource_type="rights",
        user_id=user.id,
        detail=payload.model_dump(),
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/api/models/registry", response_model=list[ModelOut])
def list_registry_models(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(RegisteredModel).order_by(RegisteredModel.created_at.desc()).all()


@router.post("/api/models/registry", response_model=ModelOut, status_code=201)
def register_model(
    payload: ModelCreate,
    user: User = Depends(require_roles(*MODEL_PROMOTE_ROLES, UserRole.AI_OPERATOR)),
    db: Session = Depends(get_db),
):
    model = RegisteredModel(**payload.model_dump(), created_by=user.id, owner="Art City")
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.patch("/api/models/registry/{model_id}/status", response_model=ModelOut)
def promote_model(
    model_id: str,
    payload: ModelStatusUpdate,
    user: User = Depends(require_roles(*MODEL_PROMOTE_ROLES)),
    db: Session = Depends(get_db),
):
    model = db.get(RegisteredModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if payload.status == ModelStatus.PRODUCTION.value and not model.checksum:
        raise HTTPException(status_code=400, detail="Checksum required for production")
    model.status = payload.status
    if payload.status in {ModelStatus.APPROVED.value, ModelStatus.PRODUCTION.value, ModelStatus.STAGING.value}:
        from datetime import timezone

        model.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(model)
    return model


@router.get("/api/training", response_model=list[TrainingOut])
def list_training(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).all()


@router.post("/api/training", response_model=TrainingOut, status_code=201)
def create_training(
    payload: TrainingCreate,
    user: User = Depends(require_roles(*TRAINING_ROLES)),
    db: Session = Depends(get_db),
):
    assert_dataset_trainable(db, payload.dataset_id)
    job = TrainingJob(
        model_type=payload.method,
        base_model=payload.base_model,
        dataset_id=payload.dataset_id,
        evaluation_dataset_id=payload.evaluation_dataset_id,
        method=payload.method,
        epochs=payload.epochs,
        learning_rate=payload.learning_rate,
        batch_size=payload.batch_size,
        seed=payload.seed,
        gpu_type=payload.gpu_type,
        estimated_cost=payload.estimated_cost,
        status=TrainingJobStatus.PENDING_APPROVAL.value,
        initiated_by=user.id,
        config_json={"model_name": payload.model_name, "character_key": payload.character_key},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.post("/api/training/{job_id}/approve", response_model=TrainingOut)
def approve_training(
    job_id: str,
    user: User = Depends(require_roles(*TRAINING_ROLES)),
    db: Session = Depends(get_db),
):
    job = db.get(TrainingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    assert_dataset_trainable(db, job.dataset_id)
    # Simulated training run (no GPU) — creates registered model draft
    from datetime import timezone
    from hashlib import sha256

    job.status = TrainingJobStatus.RUNNING.value
    job.approved_by = user.id
    job.started_at = datetime.now(timezone.utc)
    db.flush()

    cfg = job.config_json or {}
    name = cfg.get("model_name") or f"AC-ADAPTER-{job.id[:8]}"
    character_key = cfg.get("character_key")
    checksum = sha256(f"{name}:{job.dataset_id}:{job.seed}".encode()).hexdigest()
    model = RegisteredModel(
        name=name,
        version="v1",
        model_type="lora",
        base_model=job.base_model,
        training_dataset_id=job.dataset_id,
        evaluation_dataset_id=job.evaluation_dataset_id,
        training_method=job.method,
        character_key=character_key,
        modality="image",
        status=ModelStatus.EVALUATING.value,
        checkpoint_path=f"models/{name}/checkpoint.safetensors",
        checksum=checksum,
        commercial_use=True,
        owner="Art City",
        created_by=user.id,
    )
    db.add(model)
    db.flush()
    job.resulting_model_id = model.id
    job.status = TrainingJobStatus.SUCCEEDED.value
    job.ended_at = datetime.now(timezone.utc)
    job.actual_cost = job.estimated_cost or 12.0
    job.checkpoint_path = model.checkpoint_path
    job.evaluation_result = {"simulated": True, "checksum": checksum}
    db.commit()
    db.refresh(job)
    return job
