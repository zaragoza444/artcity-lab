from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.schemas import PublicationCreate, PublicationOut
from app.core.db import get_db
from app.core.ids import load_project, require_uuid
from app.services.publishing import (
    create_publication,
    find_publication_asset,
    get_publication,
    list_publications,
    publish_publication,
)
from app.services.storage import get_storage

router = APIRouter(tags=["publishing"], dependencies=[Depends(get_current_user)])


@router.post(
    "/api/projects/{project_id}/publications",
    response_model=PublicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_project_publication(
    project_id: str, payload: PublicationCreate, db: Session = Depends(get_db)
) -> PublicationOut:
    project = load_project(db, project_id)
    try:
        pub = create_publication(
            db,
            project_id=project.id,
            cinema_package_id=payload.cinema_package_id,
            channel=payload.channel,
            auto_approve_missing=payload.auto_approve_missing,
            publisher_note=payload.publisher_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PublicationOut.model_validate(pub)


@router.get("/api/projects/{project_id}/publications", response_model=list[PublicationOut])
def list_project_publications(project_id: str, db: Session = Depends(get_db)) -> list[PublicationOut]:
    project = load_project(db, project_id)
    return [PublicationOut.model_validate(p) for p in list_publications(db, project.id)]


@router.get(
    "/api/projects/{project_id}/publications/{publication_id}",
    response_model=PublicationOut,
)
def get_project_publication(
    project_id: str, publication_id: str, db: Session = Depends(get_db)
) -> PublicationOut:
    project = load_project(db, project_id)
    require_uuid(publication_id, "publication_id")
    try:
        return PublicationOut.model_validate(get_publication(db, project.id, publication_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/api/projects/{project_id}/publications/{publication_id}/publish",
    response_model=PublicationOut,
)
def finalize_publication(
    project_id: str, publication_id: str, db: Session = Depends(get_db)
) -> PublicationOut:
    project = load_project(db, project_id)
    require_uuid(publication_id, "publication_id")
    try:
        return PublicationOut.model_validate(publish_publication(db, project.id, publication_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/publications/{project_id}/{publication_id}/manifest")
def get_manifest(project_id: str, publication_id: str, db: Session = Depends(get_db)) -> Response:
    project = load_project(db, project_id)
    require_uuid(publication_id, "publication_id")
    try:
        asset = find_publication_asset(db, project.id, publication_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    key = (asset.metadata_json or {}).get("manifest_key")
    if not key:
        raise HTTPException(status_code=404, detail="Manifest missing")
    data, content_type = get_storage().get_object(key)
    return Response(content=data, media_type=content_type)


@router.get("/api/publications/{project_id}/{publication_id}/report")
def get_report(project_id: str, publication_id: str, db: Session = Depends(get_db)) -> Response:
    project = load_project(db, project_id)
    require_uuid(publication_id, "publication_id")
    try:
        asset = find_publication_asset(db, project.id, publication_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    key = (asset.metadata_json or {}).get("report_key")
    if not key:
        raise HTTPException(status_code=404, detail="Report missing")
    data, content_type = get_storage().get_object(key)
    return Response(content=data, media_type=content_type)


@router.get("/api/publications/{project_id}/{publication_id}/masters/{filename}")
def get_master_file(
    project_id: str, publication_id: str, filename: str, db: Session = Depends(get_db)
) -> Response:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    project = load_project(db, project_id)
    require_uuid(publication_id, "publication_id")
    try:
        asset = find_publication_asset(db, project.id, publication_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    root = (asset.metadata_json or {}).get("delivery_root")
    if not root:
        raise HTTPException(status_code=404, detail="Delivery root missing")
    key = f"{root}/masters/{filename}"
    try:
        data, content_type = get_storage().get_object(key)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Master file not found") from exc
    return Response(content=data, media_type=content_type)
