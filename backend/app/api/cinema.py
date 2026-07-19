from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.schemas import CinemaPackageCreate, CinemaPackageOut
from app.core.db import get_db
from app.core.deps import CurrentUser, get_current_user
from app.core.ids import load_project, require_uuid
from app.services.cinema import (
    build_cinematic_package,
    get_cinematic_package,
    list_cinematic_packages,
    revalidate_package,
)
from app.services.packaging import build_campaign_zip

router = APIRouter(
    prefix="/api/projects",
    tags=["cinema"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/{project_id}/cinema/packages",
    response_model=CinemaPackageOut,
    status_code=status.HTTP_201_CREATED,
)
def create_cinema_package(
    project_id: str,
    payload: CinemaPackageCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> CinemaPackageOut:
    project = load_project(db, project_id)
    try:
        package = build_cinematic_package(
            db,
            project_id=project.id,
            campaign=payload.campaign,
            brief=payload.brief,
            cta=payload.cta,
            brand=payload.brand,
            voiceover_script=payload.voiceover_script,
            music_style=payload.music_style,
            duration_seconds=payload.duration_seconds,
            initiated_by=payload.initiated_by or user.email,
            dialect=payload.dialect,
            character_key=payload.character_key,
            character_name=payload.character_name,
            channels=payload.channels,
            requested_by=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CinemaPackageOut.model_validate(package)


@router.get("/{project_id}/cinema/packages", response_model=list[CinemaPackageOut])
def get_cinema_packages(project_id: str, db: Session = Depends(get_db)) -> list[CinemaPackageOut]:
    project = load_project(db, project_id)
    return [CinemaPackageOut.model_validate(p) for p in list_cinematic_packages(db, project.id)]


@router.get("/{project_id}/cinema/packages/{package_id}", response_model=CinemaPackageOut)
def get_package(project_id: str, package_id: str, db: Session = Depends(get_db)) -> CinemaPackageOut:
    project = load_project(db, project_id)
    require_uuid(package_id, "package_id")
    try:
        return CinemaPackageOut.model_validate(get_cinematic_package(db, project.id, package_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/{project_id}/cinema/packages/{package_id}/validate",
    response_model=CinemaPackageOut,
)
def validate_package(
    project_id: str, package_id: str, db: Session = Depends(get_db)
) -> CinemaPackageOut:
    project = load_project(db, project_id)
    require_uuid(package_id, "package_id")
    try:
        return CinemaPackageOut.model_validate(revalidate_package(db, project.id, package_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/cinema/packages/{package_id}/manifest")
def package_manifest(project_id: str, package_id: str, db: Session = Depends(get_db)) -> Response:
    project = load_project(db, project_id)
    require_uuid(package_id, "package_id")
    try:
        pkg = get_cinematic_package(db, project.id, package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    import json

    data = json.dumps(pkg.get("campaign_manifest") or {}, indent=2).encode("utf-8")
    return Response(content=data, media_type="application/json")


@router.get("/{project_id}/cinema/packages/{package_id}/validation")
def package_validation(project_id: str, package_id: str, db: Session = Depends(get_db)) -> Response:
    project = load_project(db, project_id)
    require_uuid(package_id, "package_id")
    try:
        pkg = get_cinematic_package(db, project.id, package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    import json

    data = json.dumps(pkg.get("validation") or {}, indent=2).encode("utf-8")
    return Response(content=data, media_type="application/json")


@router.get("/{project_id}/cinema/packages/{package_id}/zip")
def package_zip(project_id: str, package_id: str, db: Session = Depends(get_db)) -> Response:
    project = load_project(db, project_id)
    require_uuid(package_id, "package_id")
    try:
        payload = build_campaign_zip(db, project.id, package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    filename = f"art-city-cinema-{package_id[:8]}.zip"
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
