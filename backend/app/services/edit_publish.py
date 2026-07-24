"""Art City Edit — publish connectors and publications."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import EditProjectStatus, EditVersionReviewStatus
from app.models import User
from app.models_edit import (
    EditProject,
    EditPublication,
    EditPublishConnector,
    EditTimelineVersion,
    EditWorkspace,
)
from app.services.audit import write_audit
from app.services.edit_entitlements import require_workspace_access


def _require_publishing_enabled() -> None:
    if not get_settings().edit_feature_publishing:
        raise ValueError("Publishing feature is disabled (edit_feature_publishing)")


def list_connectors(db: Session, workspace_id: str) -> list[EditPublishConnector]:
    _require_publishing_enabled()
    return (
        db.query(EditPublishConnector)
        .filter(EditPublishConnector.workspace_id == workspace_id)
        .order_by(EditPublishConnector.created_at.desc())
        .all()
    )


def create_connector(
    db: Session,
    workspace_id: str,
    user: User,
    provider: str,
    display_name: str,
    credentials_ref: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> EditPublishConnector:
    _require_publishing_enabled()
    require_workspace_access(db, user, workspace_id, roles=["owner", "admin", "editor"])
    workspace = db.get(EditWorkspace, workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")

    connector = EditPublishConnector(
        id=str(uuid4()),
        workspace_id=workspace_id,
        provider=provider.strip().lower(),
        display_name=display_name.strip() or provider,
        status="active",
        credentials_ref=credentials_ref,
        metadata_json=metadata or {},
    )
    db.add(connector)
    db.flush()
    write_audit(
        db,
        action="edit.connector.created",
        resource_type="edit_publish_connector",
        resource_id=connector.id,
        user_id=user.id,
        detail={"workspace_id": workspace_id, "provider": connector.provider},
    )
    db.flush()
    return connector


def publish_version(
    db: Session,
    project_id: str,
    timeline_version_id: str,
    user: User,
    destination: str,
    caption_text: Optional[str] = None,
    analytics_consent: bool = False,
    metadata: Optional[dict[str, Any]] = None,
    connector_id: Optional[str] = None,
) -> EditPublication:
    _require_publishing_enabled()
    project = db.get(EditProject, project_id)
    if not project:
        raise ValueError("Project not found")
    require_workspace_access(db, user, project.workspace_id, roles=["owner", "admin", "editor"])

    version = db.get(EditTimelineVersion, timeline_version_id)
    if not version or version.project_id != project_id:
        raise ValueError("Timeline version not found for project")
    if version.status != EditVersionReviewStatus.APPROVED.value:
        raise ValueError("Only approved timeline versions may be published")

    if connector_id:
        connector = db.get(EditPublishConnector, connector_id)
        if not connector or connector.workspace_id != project.workspace_id:
            raise ValueError("Connector not found in workspace")
        if connector.status != "active":
            raise ValueError("Connector is not active")

    publication = EditPublication(
        id=str(uuid4()),
        project_id=project_id,
        timeline_version_id=timeline_version_id,
        destination=destination.strip().lower(),
        external_id=f"stub-{uuid4().hex[:12]}",
        caption_text=caption_text,
        metadata_json={
            **(metadata or {}),
            "connector_id": connector_id,
            "stub": True,
        },
        analytics_consent=analytics_consent,
        published_at=datetime.now(timezone.utc),
    )
    db.add(publication)
    project.status = EditProjectStatus.PUBLISHED.value
    db.add(project)
    db.flush()
    write_audit(
        db,
        action="edit.publication.created",
        resource_type="edit_publication",
        resource_id=publication.id,
        user_id=user.id,
        detail={
            "project_id": project_id,
            "destination": publication.destination,
            "timeline_version_id": timeline_version_id,
        },
    )
    db.flush()
    return publication
