"""Hard backend rules for training rights."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import DatasetStatus, RightsStatus
from app.models import Dataset, RightsRecord


def assert_dataset_rights_for_training(db: Session, dataset_id: str) -> Dataset:
    """Validate AI-training rights before promoting a dataset to training_ready."""
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.ai_training_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset AI-training permission is not granted",
        )
    rights = (
        db.query(RightsRecord)
        .filter(RightsRecord.dataset_id == dataset_id)
        .order_by(RightsRecord.created_at.desc())
        .first()
    )
    if not rights or not rights.ai_training:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No approved AI-training rights record for dataset",
        )
    if rights.legal_status in {
        RightsStatus.BLOCKED.value,
        RightsStatus.EXPIRED.value,
        RightsStatus.UNKNOWN.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rights legal_status blocks training: {rights.legal_status}",
        )
    if rights.legal_status != RightsStatus.APPROVED_FOR_TRAINING.value and not (
        rights.ai_training and rights.legal_status == RightsStatus.APPROVED_FOR_COMMERCIAL_USE.value
    ):
        if rights.legal_status != RightsStatus.APPROVED_FOR_TRAINING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rights must be approved_for_training",
            )
    return dataset


def assert_dataset_trainable(db: Session, dataset_id: str) -> Dataset:
    dataset = assert_dataset_rights_for_training(db, dataset_id)
    if dataset.status != DatasetStatus.TRAINING_READY.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset status must be training_ready",
        )
    return dataset
