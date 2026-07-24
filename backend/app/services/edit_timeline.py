"""Art City Edit — timeline versions, transcript edits, and review."""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import EditProjectStatus, EditVersionReviewStatus
from app.models import User
from app.models_edit import EditApproval, EditCandidateClip, EditProject, EditTimelineVersion
from app.services.edit_entitlements import require_workspace_access


def create_timeline_from_candidates(
    db: Session,
    project_id: str,
    user: User,
    candidate_ids: list[str],
) -> EditTimelineVersion:
    project = db.get(EditProject, project_id)
    if not project:
        raise ValueError("Project not found")
    require_workspace_access(db, user, project.workspace_id)

    if not candidate_ids:
        raise ValueError("candidate_ids required")

    candidates = (
        db.query(EditCandidateClip)
        .filter(
            EditCandidateClip.project_id == project_id,
            EditCandidateClip.id.in_(candidate_ids),
        )
        .all()
    )
    by_id = {c.id: c for c in candidates}
    ordered = [by_id[cid] for cid in candidate_ids if cid in by_id]
    if not ordered:
        raise ValueError("No matching candidates")

    parent = (
        db.query(EditTimelineVersion)
        .filter(EditTimelineVersion.project_id == project_id)
        .order_by(EditTimelineVersion.version_number.desc())
        .first()
    )
    version_number = (parent.version_number + 1) if parent else 1
    if parent:
        parent.status = EditVersionReviewStatus.SUPERSEDED.value
        db.add(parent)

    clips = []
    cursor = 0.0
    for c in ordered:
        dur = max(float(c.source_out) - float(c.source_in), 0.01)
        clips.append(
            {
                "candidate_id": c.id,
                "source_in": c.source_in,
                "source_out": c.source_out,
                "timeline_in": round(cursor, 3),
                "timeline_out": round(cursor + dur, 3),
                "score": c.score,
            }
        )
        cursor += dur

    edit_plan = {
        "schema_version": "1.0",
        "objective": (project.brief_json or {}).get("objective") or "engagement",
        "source_asset_id": project.source_asset_id,
        "clips": clips,
        "captions": {"enabled": True, "burn_in": False},
        "ratios": ["9:16", "16:9", "4:5", "1:1"],
    }

    version = EditTimelineVersion(
        id=str(uuid4()),
        project_id=project_id,
        parent_version_id=parent.id if parent else None,
        version_number=version_number,
        name=f"Version {version_number}",
        edit_plan_json=edit_plan,
        transcript_json=(parent.transcript_json if parent else {"schema_version": "1.0", "segments": []}),
        status=EditVersionReviewStatus.DRAFT.value,
        created_by=user.id,
    )
    db.add(version)
    project.status = EditProjectStatus.EDITING.value
    db.add(project)
    db.flush()
    return version


def update_edit_plan(db: Session, version_id: str, edit_plan: dict[str, Any]) -> EditTimelineVersion:
    version = db.get(EditTimelineVersion, version_id)
    if not version:
        raise ValueError("Timeline version not found")
    if version.status == EditVersionReviewStatus.APPROVED.value:
        raise ValueError("Cannot edit an approved timeline version")
    plan = dict(edit_plan or {})
    if "schema_version" not in plan:
        plan["schema_version"] = "1.0"
    version.edit_plan_json = plan
    if version.status == EditVersionReviewStatus.READY_FOR_REVIEW.value:
        version.status = EditVersionReviewStatus.DRAFT.value
    db.add(version)
    db.flush()
    return version


def apply_transcript_removal(
    db: Session,
    version_id: str,
    remove_ranges: list[dict[str, float]],
) -> EditTimelineVersion:
    version = db.get(EditTimelineVersion, version_id)
    if not version:
        raise ValueError("Timeline version not found")

    transcript = dict(version.transcript_json or {})
    segments = list(transcript.get("segments") or [])
    ranges = [
        (float(r["start"]), float(r["end"]))
        for r in remove_ranges
        if "start" in r and "end" in r and float(r["end"]) > float(r["start"])
    ]

    def overlaps(seg_start: float, seg_end: float) -> bool:
        for rs, re in ranges:
            if seg_start < re and seg_end > rs:
                return True
        return False

    kept = []
    for seg in segments:
        try:
            s = float(seg.get("start", 0))
            e = float(seg.get("end", 0))
        except (TypeError, ValueError):
            kept.append(seg)
            continue
        if not overlaps(s, e):
            kept.append(seg)
            continue
        # Split around removal ranges when partially overlapping
        pieces = [(s, e)]
        for rs, re in sorted(ranges):
            next_pieces = []
            for ps, pe in pieces:
                if pe <= rs or ps >= re:
                    next_pieces.append((ps, pe))
                    continue
                if ps < rs:
                    next_pieces.append((ps, rs))
                if pe > re:
                    next_pieces.append((re, pe))
            pieces = next_pieces
        for i, (ps, pe) in enumerate(pieces):
            if pe - ps < 0.05:
                continue
            piece = dict(seg)
            piece["start"] = round(ps, 3)
            piece["end"] = round(pe, 3)
            piece["id"] = f"{seg.get('id', 'seg')}_keep_{i}"
            kept.append(piece)

    transcript["segments"] = kept
    transcript["schema_version"] = transcript.get("schema_version") or "1.0"
    version.transcript_json = transcript

    # Mirror removals into edit plan if present
    plan = dict(version.edit_plan_json or {})
    plan["transcript_removals"] = [{"start": a, "end": b} for a, b in ranges]
    plan["schema_version"] = plan.get("schema_version") or "1.0"
    version.edit_plan_json = plan
    db.add(version)
    db.flush()
    return version


def submit_for_review(db: Session, version_id: str, user: User) -> EditTimelineVersion:
    version = db.get(EditTimelineVersion, version_id)
    if not version:
        raise ValueError("Timeline version not found")
    project = db.get(EditProject, version.project_id)
    if not project:
        raise ValueError("Project not found")
    require_workspace_access(db, user, project.workspace_id)
    version.status = EditVersionReviewStatus.READY_FOR_REVIEW.value
    project.status = EditProjectStatus.HUMAN_REVIEW.value
    db.add(version)
    db.add(project)
    db.flush()
    return version


def decide_version(
    db: Session,
    version_id: str,
    user: User,
    decision: str,
    comments: Optional[str] = None,
    timecode: Optional[float] = None,
) -> EditTimelineVersion:
    version = db.get(EditTimelineVersion, version_id)
    if not version:
        raise ValueError("Timeline version not found")
    project = db.get(EditProject, version.project_id)
    if not project:
        raise ValueError("Project not found")
    membership = require_workspace_access(db, user, project.workspace_id)

    decision = decision.lower().strip()
    if decision not in {"approve", "reject", "request_changes"}:
        raise ValueError("decision must be approve|reject|request_changes")

    approval = EditApproval(
        id=str(uuid4()),
        timeline_version_id=version.id,
        approver_user_id=user.id,
        role=membership.role,
        decision=decision,
        comments=comments,
        timecode_seconds=timecode,
    )
    db.add(approval)

    if decision == "approve":
        version.status = EditVersionReviewStatus.APPROVED.value
        project.status = EditProjectStatus.APPROVED.value
    elif decision == "reject":
        version.status = EditVersionReviewStatus.CHANGES_REQUESTED.value
        project.status = EditProjectStatus.EDITING.value
    else:
        version.status = EditVersionReviewStatus.CHANGES_REQUESTED.value
        project.status = EditProjectStatus.EDITING.value

    db.add(version)
    db.add(project)
    db.flush()
    return version
