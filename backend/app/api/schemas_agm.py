"""Pydantic schemas for AC Graphic Motion API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SceneCreateIn(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=160)
    graph: Optional[dict[str, Any]] = None
    locale: str = "ckb-IQ"
    direction: Literal["rtl", "ltr", "auto"] = "rtl"


class ValidateIn(BaseModel):
    graph: Optional[dict[str, Any]] = None
    revision_id: Optional[str] = None
    profile: Optional[dict[str, Any]] = None


class PreviewIn(BaseModel):
    revision_id: Optional[str] = None
    mode: Literal["still", "range", "full"] = "still"
    at_ms: int = 0
    start_ms: int = 0
    end_ms: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Literal["png", "jpeg", "mp4", "webm"] = "png"
    quote_id: Optional[str] = None


class RenderIn(BaseModel):
    revision_id: Optional[str] = None
    profile: Optional[dict[str, Any]] = None
    quote_id: Optional[str] = None


class QuoteIn(BaseModel):
    job_kind: Literal["preview", "render"] = "preview"
    duration_ms: int = 8000
    profile: Optional[dict[str, Any]] = None


class RevisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scene_id: str
    project_id: str
    revision_no: int
    content_hash: str
    parent_revision_id: Optional[str] = None
    graph: dict[str, Any]
    created_at: Optional[datetime] = None


class SceneOut(BaseModel):
    id: str
    project_id: str
    name: str
    locale: str
    direction: str
    head_revision_id: Optional[str] = None
    etag: Optional[str] = None
    content_hash: Optional[str] = None
    soft_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    revision: Optional[RevisionOut] = None


class JobOut(BaseModel):
    id: str
    scene_id: str
    project_id: str
    revision_id: str
    job_kind: str
    status: str
    progress: float
    profile: Optional[dict[str, Any]] = None
    request: Optional[dict[str, Any]] = None
    outputs: Optional[list[Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    acx_quote_id: Optional[str] = None
    parent_job_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
