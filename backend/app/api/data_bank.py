"""Project Data Bank APIs — browse, upload, sync, seed."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser
from app.core.ids import load_project, require_uuid
from app.services import data_bank as bank

router = APIRouter(tags=["data-bank"])


class DataBankSeedOut(BaseModel):
    project: dict
    seed_job_id: str
    seed_status: str
    seed_media_url: Optional[str] = None
    sync: dict
    summary: dict


class DataBankSyncOut(BaseModel):
    created: int
    skipped: int
    jobs_scanned: int


class DataBankSummaryOut(BaseModel):
    project_id: str
    total: int
    by_type: dict
    by_source: dict


class DataBankHubOut(BaseModel):
    projects_with_assets: int
    total_assets: int
    bank_project_id: Optional[str] = None
    projects: list[dict]


class DataBankAssetOut(BaseModel):
    id: str
    project_id: str
    asset_type: str
    name: str
    storage_path: Optional[str] = None
    checksum: Optional[str] = None
    metadata_json: Optional[dict] = None
    soft_deleted: bool
    created_at: object
    media_url: Optional[str] = None
    source: Optional[str] = None
    tags: list = Field(default_factory=list)
    prompt: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None


@router.get("/api/data-bank", response_model=DataBankHubOut)
def data_bank_hub(user: CurrentUser, db: Session = Depends(get_db)) -> DataBankHubOut:
    return DataBankHubOut(**bank.hub_overview(db))


@router.post(
    "/api/data-bank/seed",
    response_model=DataBankSeedOut,
    status_code=status.HTTP_201_CREATED,
)
def seed_data_bank(user: CurrentUser, db: Session = Depends(get_db)) -> DataBankSeedOut:
    result = bank.seed_data_bank(db, requested_by=user.id)
    return DataBankSeedOut(**result)


@router.get("/api/projects/{project_id}/data-bank/summary", response_model=DataBankSummaryOut)
def project_data_bank_summary(
    project_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> DataBankSummaryOut:
    project = load_project(db, project_id)
    return DataBankSummaryOut(**bank.bank_summary(db, project.id))


@router.get("/api/projects/{project_id}/data-bank", response_model=list[DataBankAssetOut])
def list_project_data_bank(
    project_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    asset_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 200,
) -> list[DataBankAssetOut]:
    project = load_project(db, project_id)
    rows = bank.list_bank_assets(
        db, project.id, q=q, asset_type=asset_type, source=source, limit=limit
    )
    return [DataBankAssetOut(**r) for r in rows]


@router.post(
    "/api/projects/{project_id}/data-bank/upload",
    response_model=DataBankAssetOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_data_bank(
    project_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
) -> DataBankAssetOut:
    project = load_project(db, project_id)
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(raw) > 80 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 80MB)")
    tag_list: list[str] = ["data-bank"]
    if tags:
        try:
            parsed = json.loads(tags)
            if isinstance(parsed, list):
                tag_list.extend(str(t) for t in parsed)
            else:
                tag_list.extend(t.strip() for t in tags.split(",") if t.strip())
        except json.JSONDecodeError:
            tag_list.extend(t.strip() for t in tags.split(",") if t.strip())
    asset = bank.upload_to_bank(
        db,
        project_id=project.id,
        filename=file.filename or "upload.bin",
        data=raw,
        content_type=file.content_type or "application/octet-stream",
        name=name,
        tags=list(dict.fromkeys(tag_list)),
        notes=notes,
    )
    return DataBankAssetOut(**bank.enrich_asset(asset))


@router.post(
    "/api/projects/{project_id}/data-bank/sync",
    response_model=DataBankSyncOut,
)
def sync_project_data_bank(
    project_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> DataBankSyncOut:
    project = load_project(db, project_id)
    return DataBankSyncOut(**bank.sync_generations_into_bank(db, project.id))


@router.delete(
    "/api/projects/{project_id}/data-bank/{asset_id}",
    response_model=DataBankAssetOut,
)
def delete_project_data_bank_asset(
    project_id: str, asset_id: str, user: CurrentUser, db: Session = Depends(get_db)
) -> DataBankAssetOut:
    project = load_project(db, project_id)
    require_uuid(asset_id, "asset_id")
    try:
        asset = bank.soft_delete_bank_asset(db, project.id, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DataBankAssetOut(**bank.enrich_asset(asset))
