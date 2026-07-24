"""Art City Edit — media upload, projects, and analysis jobs."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import EditJobStatus, EditProjectStatus, EditVersionReviewStatus
from app.models import User
from app.models_edit import (
    EditAnalysisJob,
    EditCandidateClip,
    EditMediaAsset,
    EditProject,
    EditTimelineVersion,
    EditWorkspace,
)
from app.services.edit_entitlements import assert_entitled, org_is_processable, record_usage, require_workspace_access
from app.services.queue import enqueue_edit_job
from app.services.storage import get_storage


def _safe_filename(filename: str) -> str:
    return (filename or "upload.bin").replace("/", "_").replace("\\", "_").strip() or "upload.bin"


def _probe_duration(file_bytes: bytes, filename: str) -> Optional[float]:
    if not shutil.which("ffprobe"):
        return None
    suffix = Path(filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        path = tmp.name
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout or "{}")
        duration = data.get("format", {}).get("duration")
        return float(duration) if duration is not None else None
    except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None
    finally:
        Path(path).unlink(missing_ok=True)


def upload_source(
    db: Session,
    workspace_id: str,
    user: User,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    rights_attested: bool,
    rights_notes: Optional[str] = None,
) -> EditMediaAsset:
    if not rights_attested:
        raise ValueError("rights_attested is required to upload source media")
    if not file_bytes:
        raise ValueError("Empty file")

    require_workspace_access(db, user, workspace_id)
    workspace = db.get(EditWorkspace, workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")
    if not org_is_processable(db, workspace.organisation_id):
        raise ValueError("Organisation is not processable")
    assert_entitled(db, workspace.organisation_id, feature="storage_gb", amount=0)

    asset_id = str(uuid4())
    safe_name = _safe_filename(filename)
    checksum = hashlib.sha256(file_bytes).hexdigest()
    storage_key = f"edit/{workspace_id}/{asset_id}/master/{safe_name}"
    storage = get_storage()
    storage.upload_bytes(storage_key, file_bytes, content_type or "application/octet-stream")

    duration = _probe_duration(file_bytes, safe_name)
    if duration is None:
        # Text / non-media sources: estimate from size for pacing
        if (content_type or "").startswith("text/") or safe_name.endswith(".txt"):
            duration = max(15.0, min(180.0, len(file_bytes) / 12.0))
        else:
            duration = 30.0
    asset = EditMediaAsset(
        id=asset_id,
        workspace_id=workspace_id,
        owner_user_id=user.id,
        filename=safe_name,
        storage_key=storage_key,
        checksum=checksum,
        content_type=content_type or "application/octet-stream",
        size_bytes=len(file_bytes),
        duration_seconds=duration,
        rights_attested=True,
        rights_notes=rights_notes,
        rights_status="declared",
        technical_metadata={"uploaded_by": user.id},
    )
    db.add(asset)
    db.flush()
    create_proxy(db, asset, file_bytes)
    record_usage(
        db,
        workspace.organisation_id,
        metric="storage_gb",
        quantity=round(len(file_bytes) / (1024**3), 6),
        workspace_id=workspace_id,
    )
    db.flush()
    return asset


def create_proxy(db: Session, asset: EditMediaAsset, file_bytes: Optional[bytes] = None) -> EditMediaAsset:
    """Create an H.264 proxy when ffmpeg is available; otherwise master passthrough."""
    storage = get_storage()
    if file_bytes is None:
        try:
            file_bytes, _ = storage.get_object(asset.storage_key)
        except Exception:
            file_bytes = b""

    ct = (asset.content_type or "").lower()
    is_av = ct.startswith("video/") or ct.startswith("audio/") or asset.filename.lower().endswith(
        (".mp4", ".mov", ".mkv", ".webm", ".wav", ".mp3", ".m4a")
    )

    if is_av and file_bytes and shutil.which("ffmpeg"):
        suffix = Path(asset.filename).suffix or ".bin"
        with tempfile.TemporaryDirectory(prefix="artcity-proxy-") as tmp:
            root = Path(tmp)
            src = root / f"src{suffix}"
            out = root / "proxy.mp4"
            src.write_bytes(file_bytes)
            cmd = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(src),
                "-vf",
                "scale=1280:-2",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(out),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=180)
                if out.exists() and out.stat().st_size > 32:
                    proxy_key = f"edit/{asset.workspace_id}/{asset.id}/proxy/proxy.mp4"
                    storage.upload_bytes(proxy_key, out.read_bytes(), "video/mp4")
                    asset.proxy_key = proxy_key
                    asset.technical_metadata = {
                        **(asset.technical_metadata or {}),
                        "proxy_mode": "ffmpeg_h264",
                        "ffmpeg_available": True,
                    }
                    db.add(asset)
                    db.flush()
                    return asset
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
                pass

    asset.proxy_key = asset.storage_key
    asset.technical_metadata = {
        **(asset.technical_metadata or {}),
        "proxy_mode": "master_passthrough",
        "ffmpeg_available": bool(shutil.which("ffmpeg")),
    }
    db.add(asset)
    db.flush()
    return asset


# Back-compat alias for older imports/tests
create_proxy_stub = create_proxy


def create_project(
    db: Session,
    workspace_id: str,
    user: User,
    title: str,
    source_asset_id: str,
    brand_profile_version_id: Optional[str] = None,
    production_project_id: Optional[str] = None,
    brief: Optional[dict[str, Any]] = None,
) -> EditProject:
    require_workspace_access(db, user, workspace_id)
    asset = db.get(EditMediaAsset, source_asset_id)
    if not asset or asset.workspace_id != workspace_id:
        raise ValueError("Source asset not found in workspace")
    if not asset.rights_attested:
        raise ValueError("Source asset lacks rights attestation")

    project = EditProject(
        id=str(uuid4()),
        workspace_id=workspace_id,
        title=title.strip() or "Untitled Edit",
        status=EditProjectStatus.DRAFT.value,
        brand_profile_version_id=brand_profile_version_id,
        source_asset_id=source_asset_id,
        production_project_id=production_project_id,
        brief_json=brief or {},
        created_by=user.id,
    )
    db.add(project)
    db.flush()
    return project


def start_analysis(db: Session, project_id: str, user: User) -> EditAnalysisJob:
    project = db.get(EditProject, project_id)
    if not project:
        raise ValueError("Project not found")
    require_workspace_access(db, user, project.workspace_id)
    if not project.source_asset_id:
        raise ValueError("Project has no source asset")

    workspace = db.get(EditWorkspace, project.workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")
    assert_entitled(db, workspace.organisation_id, feature="processing_minutes", amount=1)

    settings = get_settings()
    model_name = "openai-whisper-1" if (settings.openai_api_key or "").strip() else "artcity-analysis-v1"
    job = EditAnalysisJob(
        id=str(uuid4()),
        project_id=project.id,
        asset_id=project.source_asset_id,
        job_type="full",
        provider="artcity-edit",
        model=model_name,
        state=EditJobStatus.QUEUED.value,
        outputs_json={},
    )
    db.add(job)
    project.status = EditProjectStatus.ANALYSING.value
    db.add(project)
    db.flush()
    try:
        enqueue_edit_job("analysis", job.id)
    except Exception:
        pass
    # Inline like Model Gateway so production works without a separate worker.
    process_analysis_job(db, job.id)
    db.refresh(job)
    return job


def _whisper_transcript(file_bytes: bytes, filename: str) -> Optional[dict[str, Any]]:
    settings = get_settings()
    key = (settings.openai_api_key or "").strip()
    if not key or not file_bytes:
        return None
    suffix = Path(filename).suffix.lower() or ".mp3"
    if suffix in {".txt", ".json", ".md", ".csv"}:
        return None
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                data={"model": "whisper-1", "response_format": "verbose_json"},
                files={"file": (filename or f"audio{suffix}", file_bytes)},
            )
            if resp.status_code >= 400:
                return None
            body = resp.json()
    except Exception:
        return None

    segments = []
    for i, seg in enumerate(body.get("segments") or []):
        segments.append(
            {
                "id": f"seg_{i}",
                "start": round(float(seg.get("start") or 0), 3),
                "end": round(float(seg.get("end") or 0), 3),
                "text": str(seg.get("text") or "").strip(),
                "speaker": "Speaker A",
            }
        )
    text = str(body.get("text") or "").strip()
    if not segments and text:
        segments = [{"id": "seg_0", "start": 0.0, "end": 5.0, "text": text, "speaker": "Speaker A"}]
    if not segments:
        return None
    return {
        "schema_version": "1.0",
        "language": body.get("language") or "und",
        "engine": "openai-whisper-1",
        "segments": segments,
    }


def _text_transcript(file_bytes: bytes, duration: float) -> dict[str, Any]:
    text = file_bytes.decode("utf-8", errors="ignore").strip() or "Art City Edit source."
    chunks = [c.strip() for c in text.replace("\r", "\n").split("\n") if c.strip()] or [text]
    duration = max(duration or 30.0, 10.0)
    seg_len = duration / max(len(chunks), 1)
    segments = []
    t = 0.0
    for i, chunk in enumerate(chunks[:24]):
        end = min(t + seg_len, duration)
        segments.append(
            {
                "id": f"seg_{i}",
                "start": round(t, 3),
                "end": round(end, 3),
                "text": chunk[:500],
                "speaker": "Narrator",
            }
        )
        t = end
    return {"schema_version": "1.0", "language": "und", "engine": "text-source", "segments": segments}


def _pacing_transcript(duration: float) -> dict[str, Any]:
    duration = max(duration or 60.0, 10.0)
    seg_len = max(duration / 8.0, 2.0)
    segments = []
    t = 0.0
    idx = 0
    while t < duration and idx < 24:
        end = min(t + seg_len, duration)
        segments.append(
            {
                "id": f"seg_{idx}",
                "start": round(t, 3),
                "end": round(end, 3),
                "text": f"Beat {idx + 1} — keep pacing and visual interest.",
                "speaker": "Editor",
            }
        )
        t = end
        idx += 1
    return {"schema_version": "1.0", "language": "und", "engine": "pacing", "segments": segments}


def _generate_candidates(project_id: str, duration: float, transcript: dict[str, Any]) -> list[EditCandidateClip]:
    duration = max(duration or 60.0, 15.0)
    segs = list(transcript.get("segments") or [])
    candidates: list[EditCandidateClip] = []
    if segs:
        # Merge pairs of segments into candidate windows
        i = 0
        rank = 1
        while i < len(segs) and rank <= 8:
            a = segs[i]
            b = segs[i + 1] if i + 1 < len(segs) else a
            start = float(a.get("start") or 0)
            end = float(b.get("end") or start + 8)
            if end - start < 4:
                end = min(start + 8, duration)
            score = round(0.95 - (rank - 1) * 0.06, 3)
            text = f"{a.get('text') or ''} {b.get('text') or ''}".strip()
            candidates.append(
                EditCandidateClip(
                    id=str(uuid4()),
                    project_id=project_id,
                    source_in=round(start, 3),
                    source_out=round(end, 3),
                    score=score,
                    explanation=f"Speech/pacing candidate #{rank}: {text[:160]}",
                    risks_json=["verify_music_rights"] if rank == 1 else [],
                    user_decision="pending",
                    metadata_json={"rank": rank, "engine": transcript.get("engine"), "stub": False},
                )
            )
            i += 2
            rank += 1
        return candidates

    count = min(6, max(3, int(duration // 30) + 2))
    clip_len = min(45.0, max(8.0, duration / (count + 1)))
    for i in range(count):
        start = min(i * (duration / count), max(duration - clip_len, 0))
        end = min(start + clip_len, duration)
        candidates.append(
            EditCandidateClip(
                id=str(uuid4()),
                project_id=project_id,
                source_in=round(start, 3),
                source_out=round(end, 3),
                score=round(0.9 - (i * 0.07), 3),
                explanation=f"High-engagement moment candidate #{i + 1} based on pacing.",
                risks_json=[],
                user_decision="pending",
                metadata_json={"rank": i + 1, "stub": False},
            )
        )
    return candidates


def process_analysis_job(db: Session, job_id: str) -> EditAnalysisJob:
    job = db.get(EditAnalysisJob, job_id)
    if not job:
        raise ValueError("Analysis job not found")
    if job.state in {EditJobStatus.SUCCEEDED.value, EditJobStatus.RUNNING.value}:
        return job

    project = db.get(EditProject, job.project_id)
    if not project:
        job.state = EditJobStatus.FAILED.value
        job.error_message = "Project missing"
        db.add(job)
        db.flush()
        return job

    workspace = db.get(EditWorkspace, project.workspace_id)
    if not workspace:
        job.state = EditJobStatus.FAILED.value
        job.error_message = "Workspace missing"
        db.add(job)
        db.flush()
        return job

    try:
        assert_entitled(db, workspace.organisation_id, feature="processing_minutes", amount=1)
    except ValueError as exc:
        job.state = EditJobStatus.BLOCKED_BY_ENTITLEMENT.value
        job.error_message = str(exc)
        db.add(job)
        project.status = EditProjectStatus.FAILED.value
        db.add(project)
        db.flush()
        return job

    job.state = EditJobStatus.RUNNING.value
    db.add(job)
    db.flush()

    try:
        asset = db.get(EditMediaAsset, job.asset_id)
        duration = float(asset.duration_seconds) if asset and asset.duration_seconds else 30.0
        storage = get_storage()
        file_bytes = b""
        if asset and asset.storage_key:
            try:
                file_bytes, _ = storage.get_object(asset.storage_key)
            except Exception:
                file_bytes = b""

        transcript = None
        if asset and (
            (asset.content_type or "").startswith("text/")
            or asset.filename.lower().endswith((".txt", ".md", ".json"))
        ):
            transcript = _text_transcript(file_bytes, duration)
        else:
            transcript = _whisper_transcript(file_bytes, asset.filename if asset else "audio.wav")
        if not transcript:
            transcript = _pacing_transcript(duration)

        candidates = _generate_candidates(project.id, duration, transcript)
        for c in candidates:
            db.add(c)

        edit_plan = {
            "schema_version": "1.0",
            "objective": (project.brief_json or {}).get("objective") or "engagement",
            "source_asset_id": job.asset_id,
            "engine": transcript.get("engine"),
            "clips": [
                {
                    "candidate_id": c.id,
                    "source_in": c.source_in,
                    "source_out": c.source_out,
                    "score": c.score,
                }
                for c in candidates
            ],
            "captions": {"enabled": True, "burn_in": False},
            "ratios": ["9:16", "16:9"],
        }

        version = EditTimelineVersion(
            id=str(uuid4()),
            project_id=project.id,
            version_number=1,
            name="Analysis draft",
            edit_plan_json=edit_plan,
            transcript_json=transcript,
            status=EditVersionReviewStatus.DRAFT.value,
            created_by=project.created_by,
        )
        db.add(version)

        minutes = max(duration / 60.0, 0.1)
        job.cost_usd = round(minutes * 0.05, 4)
        job.outputs_json = {
            "candidate_count": len(candidates),
            "timeline_version_id": version.id,
            "duration_seconds": duration,
            "transcript_segments": len(transcript.get("segments") or []),
            "engine": transcript.get("engine"),
        }
        job.state = EditJobStatus.SUCCEEDED.value
        project.status = EditProjectStatus.CANDIDATES_READY.value
        db.add(job)
        db.add(project)
        record_usage(
            db,
            workspace.organisation_id,
            metric="processing_minutes",
            quantity=round(minutes, 3),
            cost_usd=job.cost_usd,
            workspace_id=workspace.id,
            job_id=job.id,
        )
        db.flush()
        return job
    except Exception as exc:  # noqa: BLE001
        job.state = EditJobStatus.FAILED.value
        job.error_message = str(exc)
        project.status = EditProjectStatus.FAILED.value
        db.add(job)
        db.add(project)
        db.flush()
        return job


def decide_candidate(db: Session, candidate_id: str, decision: str) -> EditCandidateClip:
    candidate = db.get(EditCandidateClip, candidate_id)
    if not candidate:
        raise ValueError("Candidate not found")
    decision = decision.lower().strip()
    if decision not in {"pin", "reject", "pending"}:
        raise ValueError("decision must be pin|reject|pending")
    candidate.user_decision = decision
    db.add(candidate)
    db.flush()
    return candidate


def list_projects(db: Session, workspace_id: str) -> list[EditProject]:
    return (
        db.query(EditProject)
        .filter(EditProject.workspace_id == workspace_id)
        .order_by(EditProject.created_at.desc())
        .all()
    )


def get_project(db: Session, project_id: str) -> EditProject:
    project = db.get(EditProject, project_id)
    if not project:
        raise ValueError("Project not found")
    return project
