from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    CharacterCreate,
    CharacterOut,
    GenerationJobOut,
    GenerationSubmit,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    ScriptCreate,
    ScriptOut,
)
from app.api.studio import _enrich_job
from app.core.db import get_db
from app.core.deps import CurrentUser
from app.models import Character, GenerationJob, Project, Script
from app.services.gateway import enqueue_generation

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(user: CurrentUser, db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, user: CurrentUser, db: Session = Depends(get_db)) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        budget_limit=payload.budget_limit,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str, payload: ProjectUpdate, user: CurrentUser, db: Session = Depends(get_db)
) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/characters", response_model=list[CharacterOut])
def list_characters(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[Character]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Character).filter(Character.project_id == project_id).all()


@router.post(
    "/{project_id}/characters",
    response_model=CharacterOut,
    status_code=status.HTTP_201_CREATED,
)
def create_character(
    project_id: str, payload: CharacterCreate, user: CurrentUser, db: Session = Depends(get_db)
) -> Character:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    character = Character(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        identity_rules=payload.identity_rules or {},
        costume_notes=payload.costume_notes,
        voice_profile=payload.voice_profile or {},
        reference_paths=payload.reference_paths or [],
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@router.get("/{project_id}/scripts", response_model=list[ScriptOut])
def list_scripts(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[Script]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Script).filter(Script.project_id == project_id).all()


@router.post(
    "/{project_id}/scripts",
    response_model=ScriptOut,
    status_code=status.HTTP_201_CREATED,
)
def create_script(
    project_id: str, payload: ScriptCreate, user: CurrentUser, db: Session = Depends(get_db)
) -> Script:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    script = Script(
        project_id=project_id,
        title=payload.title,
        body=payload.body,
        language=payload.language,
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.post(
    "/{project_id}/generations",
    response_model=GenerationJobOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_generation(
    project_id: str, payload: GenerationSubmit, user: CurrentUser, db: Session = Depends(get_db)
) -> GenerationJobOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    character_key = None
    if payload.character_name:
        key = payload.character_name.strip().lower()
        if "kardokh" in key:
            character_key = "kardokh"
        elif "kurdiya" in key:
            character_key = "kurdiya"
    job = enqueue_generation(
        db,
        project_id=project_id,
        modality=payload.modality,
        prompt=payload.prompt,
        model=payload.model,
        character_key=character_key,
        character_name=payload.character_name,
        duration_seconds=payload.duration_seconds,
        dialogue_lines=payload.dialogue_lines,
        prefer_external=payload.provider == "external-fallback",
        requested_by=user.id,
    )
    return _enrich_job(job)


@router.get("/{project_id}/generations", response_model=list[GenerationJobOut])
def list_generations(project_id: str, user: CurrentUser, db: Session = Depends(get_db)) -> list[GenerationJobOut]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    jobs = (
        db.query(GenerationJob)
        .filter(GenerationJob.project_id == project_id)
        .order_by(GenerationJob.created_at.desc())
        .all()
    )
    return [_enrich_job(j) for j in jobs]
