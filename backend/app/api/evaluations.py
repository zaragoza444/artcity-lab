from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_roles
from app.core.enums import MODEL_PROMOTE_ROLES, EvaluationStatus, ModelStatus
from app.models import User,  EvaluationRun, RegisteredModel

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


class EvaluationCreate(BaseModel):
    candidate_model_id: str
    production_model_id: Optional[str] = None
    modality: str = "image"


class EvaluationOut(BaseModel):
    id: str
    candidate_model_id: str
    production_model_id: Optional[str]
    modality: str
    metrics: Optional[dict]
    status: str
    human_decision: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationDecision(BaseModel):
    decision: str  # approve | reject
    notes: Optional[str] = None


@router.get("", response_model=list[EvaluationOut])
def list_evals(user: CurrentUser, db: Session = Depends(get_db)):
    return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()


@router.post("", response_model=EvaluationOut, status_code=201)
def create_eval(payload: EvaluationCreate, user: CurrentUser, db: Session = Depends(get_db)):
    candidate = db.get(RegisteredModel, payload.candidate_model_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate model not found")
    run = EvaluationRun(
        candidate_model_id=payload.candidate_model_id,
        production_model_id=payload.production_model_id,
        modality=payload.modality,
        status=EvaluationStatus.RUNNING.value,
        created_by=user.id,
        metrics={
            "character_identity": 0.82,
            "cultural_accuracy": 0.8,
            "prompt_adherence": 0.85,
            "artifacts": 0.1,
            "child_safety": 1.0,
            "simulated": True,
        },
    )
    db.add(run)
    candidate.status = ModelStatus.EVALUATING.value
    db.flush()
    run.status = EvaluationStatus.NEEDS_HUMAN.value
    db.commit()
    db.refresh(run)
    return run


@router.post("/{run_id}/decision", response_model=EvaluationOut)
def decide(
    run_id: str,
    payload: EvaluationDecision,
    user: User = Depends(require_roles(*MODEL_PROMOTE_ROLES)),
    db: Session = Depends(get_db),
):
    run = db.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    if payload.decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="decision must be approve or reject")
    run.human_decision = payload.decision
    run.notes = payload.notes
    run.status = EvaluationStatus.APPROVED.value if payload.decision == "approve" else EvaluationStatus.REJECTED.value
    candidate = db.get(RegisteredModel, run.candidate_model_id)
    if candidate:
        if payload.decision == "approve":
            candidate.status = ModelStatus.APPROVED.value
        else:
            candidate.status = ModelStatus.BLOCKED.value
    db.commit()
    db.refresh(run)
    return run
