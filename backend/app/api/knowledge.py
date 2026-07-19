from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser
from app.models import KnowledgeEntry

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class KnowledgeCreate(BaseModel):
    term: str = Field(..., min_length=1)
    language: str = "ku"
    dialect: Optional[str] = None
    definition: str
    child_friendly_definition: Optional[str] = None
    translation: Optional[str] = None
    example_sentence: Optional[str] = None
    category: str = "terminology"
    source: Optional[str] = None
    licence: Optional[str] = None
    cultural_notes: Optional[str] = None


class KnowledgeOut(BaseModel):
    id: str
    term: str
    language: str
    dialect: Optional[str]
    definition: str
    child_friendly_definition: Optional[str]
    translation: Optional[str]
    example_sentence: Optional[str]
    category: str
    approval_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[KnowledgeOut])
def list_entries(
    user: CurrentUser,
    q: Optional[str] = Query(None),
    dialect: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(KnowledgeEntry)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (KnowledgeEntry.term.ilike(like))
            | (KnowledgeEntry.definition.ilike(like))
            | (KnowledgeEntry.translation.ilike(like))
        )
    if dialect:
        query = query.filter(KnowledgeEntry.dialect == dialect)
    return query.order_by(KnowledgeEntry.term.asc()).limit(200).all()


@router.post("", response_model=KnowledgeOut, status_code=201)
def create_entry(payload: KnowledgeCreate, user: CurrentUser, db: Session = Depends(get_db)):
    entry = KnowledgeEntry(**payload.model_dump(), created_by=user.id, approval_status="draft")
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/query", response_model=list[KnowledgeOut])
def query_for_prompts(
    user: CurrentUser,
    terms: str = Query(..., description="Comma-separated terms"),
    db: Session = Depends(get_db),
):
    parts = [t.strip() for t in terms.split(",") if t.strip()]
    if not parts:
        return []
    results: list[KnowledgeEntry] = []
    for term in parts:
        hit = (
            db.query(KnowledgeEntry)
            .filter(KnowledgeEntry.term.ilike(term), KnowledgeEntry.approval_status == "approved")
            .first()
        )
        if hit:
            results.append(hit)
    return results


@router.patch("/{entry_id}/approve", response_model=KnowledgeOut)
def approve_entry(entry_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    entry = db.get(KnowledgeEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.approval_status = "approved"
    entry.reviewer = user.email
    db.commit()
    db.refresh(entry)
    return entry
