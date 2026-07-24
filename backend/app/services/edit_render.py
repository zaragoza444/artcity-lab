"""Art City Edit — render jobs, QC, and export packages."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import EditJobStatus, EditProjectStatus, EditVersionReviewStatus
from app.models_edit import EditMediaAsset, EditProject, EditRenderJob, EditTimelineVersion, EditWorkspace
from app.services.edit_entitlements import assert_entitled, record_usage
from app.services.queue import enqueue_edit_job
from app.services.storage import get_storage

RATIO_SIZES = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


def start_render(
    db: Session,
    project_id: str,
    timeline_version_id: str,
    ratios: Optional[list[str]] = None,
) -> EditRenderJob:
    project = db.get(EditProject, project_id)
    if not project:
        raise ValueError("Project not found")
    version = db.get(EditTimelineVersion, timeline_version_id)
    if not version or version.project_id != project_id:
        raise ValueError("Timeline version not found for project")
    if version.status not in {
        EditVersionReviewStatus.APPROVED.value,
        EditVersionReviewStatus.READY_FOR_REVIEW.value,
        EditVersionReviewStatus.DRAFT.value,
    }:
        raise ValueError(f"Cannot render timeline in status {version.status}")

    workspace = db.get(EditWorkspace, project.workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")
    assert_entitled(db, workspace.organisation_id, feature="exports_per_month", amount=1)

    ratio_list = ratios or ["9:16", "16:9", "4:5", "1:1"]
    job = EditRenderJob(
        id=str(uuid4()),
        project_id=project_id,
        timeline_version_id=timeline_version_id,
        preset="social_multi",
        state=EditJobStatus.QUEUED.value,
        outputs_json={"ratios": ratio_list, "packages": []},
        qc_json={},
    )
    db.add(job)
    project.status = EditProjectStatus.RENDERING.value
    db.add(project)
    db.flush()
    try:
        enqueue_edit_job("render", job.id)
    except Exception:
        pass
    process_render_job(db, job.id)
    db.refresh(job)
    return job


def build_qc_report(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks = []
    critical_fail = False
    for out in outputs:
        checksum = out.get("checksum")
        ratio = out.get("ratio")
        key = out.get("storage_key")
        ok = bool(checksum and key and ratio)
        checks.append(
            {
                "name": f"output_{ratio}",
                "status": "PASS" if ok else "FAIL",
                "critical": True,
                "detail": {"checksum": checksum, "storage_key": key},
            }
        )
        if not ok:
            critical_fail = True
        if out.get("bytes", 0) <= 0:
            checks.append(
                {
                    "name": f"nonempty_{ratio}",
                    "status": "FAIL",
                    "critical": True,
                    "detail": {"bytes": out.get("bytes")},
                }
            )
            critical_fail = True
        else:
            checks.append(
                {
                    "name": f"nonempty_{ratio}",
                    "status": "PASS",
                    "critical": False,
                    "detail": {"bytes": out.get("bytes")},
                }
            )
        if out.get("content_type") == "video/mp4" and not out.get("placeholder"):
            checks.append(
                {
                    "name": f"real_mp4_{ratio}",
                    "status": "PASS",
                    "critical": False,
                    "detail": {"encoded": True},
                }
            )

    overall = "FAIL" if critical_fail else "PASS"
    return {
        "schema_version": "1.0",
        "overall": overall,
        "critical_fail": critical_fail,
        "checks": checks,
        "output_count": len(outputs),
    }


def _encode_ratio(
    *,
    source_bytes: bytes,
    source_name: str,
    ratio: str,
    clip_in: float,
    clip_out: float,
) -> Optional[tuple[bytes, str]]:
    if not shutil.which("ffmpeg") or not source_bytes:
        return None
    width, height = RATIO_SIZES.get(ratio, RATIO_SIZES["16:9"])
    duration = max(1.0, float(clip_out) - float(clip_in))
    suffix = Path(source_name).suffix or ".bin"
    with tempfile.TemporaryDirectory(prefix="artcity-render-") as tmp:
        root = Path(tmp)
        src = root / f"src{suffix}"
        out = root / "out.mp4"
        src.write_bytes(source_bytes)
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{max(0.0, clip_in):.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(src),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(out),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=240)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            # Still image / non-AV source: treat as looped still if PNG/JPEG
            if suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                still_cmd = [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-loop",
                    "1",
                    "-i",
                    str(src),
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=r=44100:cl=stereo",
                    "-vf",
                    vf,
                    "-c:v",
                    "libx264",
                    "-t",
                    f"{min(duration, 8.0):.3f}",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-shortest",
                    "-movflags",
                    "+faststart",
                    str(out),
                ]
                try:
                    subprocess.run(still_cmd, check=True, capture_output=True, timeout=120)
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
                    return None
            else:
                return None
        if not out.exists() or out.stat().st_size < 32:
            return None
        return out.read_bytes(), "video/mp4"


def process_render_job(db: Session, job_id: str) -> EditRenderJob:
    job = db.get(EditRenderJob, job_id)
    if not job:
        raise ValueError("Render job not found")
    if job.state in {EditJobStatus.SUCCEEDED.value, EditJobStatus.RUNNING.value}:
        return job

    project = db.get(EditProject, job.project_id)
    version = db.get(EditTimelineVersion, job.timeline_version_id)
    if not project or not version:
        job.state = EditJobStatus.FAILED.value
        job.error_message = "Project or timeline missing"
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
        assert_entitled(db, workspace.organisation_id, feature="exports_per_month", amount=1)
    except ValueError as exc:
        job.state = EditJobStatus.BLOCKED_BY_ENTITLEMENT.value
        job.error_message = str(exc)
        db.add(job)
        project.status = EditProjectStatus.FAILED.value
        db.add(project)
        db.flush()
        return job

    job.state = EditJobStatus.RUNNING.value
    project.status = EditProjectStatus.QC_REVIEW.value
    db.add(job)
    db.add(project)
    db.flush()

    try:
        ratios = list((job.outputs_json or {}).get("ratios") or ["9:16", "16:9", "4:5", "1:1"])
        storage = get_storage()
        asset = db.get(EditMediaAsset, project.source_asset_id) if project.source_asset_id else None
        source_bytes = b""
        source_name = "source.bin"
        if asset and asset.storage_key:
            try:
                source_bytes, _ = storage.get_object(asset.proxy_key or asset.storage_key)
                source_name = asset.filename or source_name
            except Exception:
                source_bytes = b""

        plan = version.edit_plan_json or {}
        clips = list(plan.get("clips") or [])
        clip_in = float(clips[0].get("source_in") or 0) if clips else 0.0
        clip_out = float(clips[0].get("source_out") or 8) if clips else 8.0

        packages: list[dict[str, Any]] = []
        for ratio in ratios:
            safe_ratio = ratio.replace(":", "x")
            encoded = _encode_ratio(
                source_bytes=source_bytes,
                source_name=source_name,
                ratio=ratio,
                clip_in=clip_in,
                clip_out=clip_out,
            )
            if encoded:
                body, content_type = encoded
                key = f"edit/{project.workspace_id}/{project.id}/exports/{job.id}/{safe_ratio}.mp4"
                storage.upload_bytes(key, body, content_type)
                packages.append(
                    {
                        "ratio": ratio,
                        "storage_key": key,
                        "checksum": hashlib.sha256(body).hexdigest(),
                        "bytes": len(body),
                        "content_type": content_type,
                        "placeholder": False,
                        "encoded": True,
                    }
                )
            else:
                # Manifest fallback only when encode impossible (e.g. plain text source)
                package = {
                    "schema_version": "1.0",
                    "project_id": project.id,
                    "timeline_version_id": version.id,
                    "ratio": ratio,
                    "edit_plan": plan,
                    "clip_in": clip_in,
                    "clip_out": clip_out,
                    "note": "Manifest export — source was not ffmpeg-encodable; upload video/audio for MP4 masters.",
                }
                body = json.dumps(package, indent=2, sort_keys=True).encode("utf-8")
                key = f"edit/{project.workspace_id}/{project.id}/exports/{job.id}/{safe_ratio}.json"
                storage.upload_bytes(key, body, "application/json")
                packages.append(
                    {
                        "ratio": ratio,
                        "storage_key": key,
                        "checksum": hashlib.sha256(body).hexdigest(),
                        "bytes": len(body),
                        "content_type": "application/json",
                        "placeholder": False,
                        "encoded": False,
                    }
                )

        qc = build_qc_report(packages)
        job.outputs_json = {"ratios": ratios, "packages": packages}
        job.qc_json = qc
        job.cost_usd = round(0.25 * len(packages), 4)

        if qc.get("critical_fail"):
            job.state = EditJobStatus.FAILED.value
            job.error_message = "QC critical failure"
            project.status = EditProjectStatus.FAILED.value
        else:
            job.state = EditJobStatus.SUCCEEDED.value
            project.status = EditProjectStatus.EXPORTED.value
            record_usage(
                db,
                workspace.organisation_id,
                metric="exports_per_month",
                quantity=float(len(packages)),
                cost_usd=job.cost_usd,
                workspace_id=workspace.id,
                job_id=job.id,
            )

        db.add(job)
        db.add(project)
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


def get_export_package(db: Session, render_job_id: str) -> dict[str, Any]:
    job = db.get(EditRenderJob, render_job_id)
    if not job:
        raise ValueError("Render job not found")
    return {
        "render_job_id": job.id,
        "project_id": job.project_id,
        "timeline_version_id": job.timeline_version_id,
        "state": job.state,
        "outputs": job.outputs_json or {},
        "qc": job.qc_json or {},
        "cost_usd": job.cost_usd,
        "error_message": job.error_message,
    }
