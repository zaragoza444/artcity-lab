"""MSG graph validation pipeline (spec §9)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Asset
from app.services import agm_brand, agm_typography

NODE_TYPES = {
    "text",
    "image",
    "video",
    "logo",
    "shape",
    "svg",
    "group",
    "camera",
    "particle",
    "chart",
    "map",
    "precomp",
}

FPS_ALLOWED = {23.976, 24, 25, 29.97, 30, 50, 59.94, 60}
SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "contracts" / "ac-graphic-motion" / "motion-scene-graph.schema.json"
)


def _err(code: str, message: str, path: str = "") -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _is_uuid(value: str) -> bool:
    try:
        UUID(str(value))
        return True
    except Exception:
        return False


def load_schema() -> dict[str, Any]:
    if SCHEMA_PATH.exists():
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return {}


def validate_schema_shape(graph: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(graph, dict):
        return [_err("AGM_SCHEMA_INVALID", "Graph must be an object")]
    if graph.get("schema_version") != "1.0.0":
        errors.append(_err("AGM_SCHEMA_INVALID", "schema_version must be 1.0.0", "schema_version"))
    for key in ("scene_id", "project_id", "name", "locale", "direction", "canvas", "nodes"):
        if key not in graph:
            errors.append(_err("AGM_SCHEMA_INVALID", f"Missing required field {key}", key))
    canvas = graph.get("canvas") or {}
    if isinstance(canvas, dict):
        for k in ("width", "height", "fps", "duration_ms"):
            if k not in canvas:
                errors.append(_err("AGM_SCHEMA_INVALID", f"canvas.{k} required", f"canvas.{k}"))
        w = canvas.get("width")
        h = canvas.get("height")
        if isinstance(w, int) and not (1 <= w <= 16384):
            errors.append(_err("AGM_SCHEMA_INVALID", "canvas.width out of range", "canvas.width"))
        if isinstance(h, int) and not (1 <= h <= 16384):
            errors.append(_err("AGM_SCHEMA_INVALID", "canvas.height out of range", "canvas.height"))
        fps = canvas.get("fps")
        if fps is not None and float(fps) not in FPS_ALLOWED:
            errors.append(_err("AGM_SCHEMA_INVALID", "unsupported fps", "canvas.fps"))
        dur = canvas.get("duration_ms")
        if isinstance(dur, int) and not (1 <= dur <= 3_600_000):
            errors.append(_err("AGM_SCHEMA_INVALID", "duration_ms out of range", "canvas.duration_ms"))
    direction = graph.get("direction")
    if direction not in (None, "rtl", "ltr", "auto"):
        errors.append(_err("AGM_SCHEMA_INVALID", "direction must be rtl|ltr|auto", "direction"))
    nodes = graph.get("nodes")
    if nodes is not None and not isinstance(nodes, list):
        errors.append(_err("AGM_SCHEMA_INVALID", "nodes must be an array", "nodes"))
    return errors


def validate_graph_integrity(graph: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    nodes = graph.get("nodes") or []
    ids: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(_err("AGM_SCHEMA_INVALID", "node must be object", f"nodes[{i}]"))
            continue
        nid = str(node.get("id") or "")
        if not nid:
            errors.append(_err("AGM_SCHEMA_INVALID", "node.id required", f"nodes[{i}].id"))
            continue
        if nid in ids:
            errors.append(_err("AGM_GRAPH_DUPLICATE_NODE", f"duplicate node id {nid}", f"nodes[{i}].id"))
        ids.add(nid)
        by_id[nid] = node
        ntype = node.get("type")
        if ntype not in NODE_TYPES:
            errors.append(_err("AGM_SCHEMA_INVALID", f"unsupported node type {ntype}", f"nodes[{i}].type"))

    # parent cycles
    for nid, node in by_id.items():
        seen: set[str] = set()
        cur = nid
        while True:
            parent = by_id.get(cur, {}).get("parent_id")
            if not parent:
                break
            parent = str(parent)
            if parent not in by_id:
                errors.append(_err("AGM_SCHEMA_INVALID", f"missing parent {parent}", f"nodes.{nid}.parent_id"))
                break
            if parent in seen or parent == nid:
                errors.append(_err("AGM_GRAPH_PARENT_CYCLE", f"parent cycle at {nid}", f"nodes.{nid}.parent_id"))
                break
            seen.add(parent)
            cur = parent
    return errors


def validate_timeline(graph: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    canvas = graph.get("canvas") or {}
    duration = int(canvas.get("duration_ms") or 0)
    for i, node in enumerate(graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        start = node.get("start_ms", 0)
        end = node.get("end_ms", duration)
        try:
            start_i = int(start)
            end_i = int(end)
        except Exception:
            errors.append(_err("AGM_TIMELINE_OUT_OF_RANGE", "start/end must be int", f"nodes[{i}]"))
            continue
        if not (0 <= start_i < end_i <= duration):
            errors.append(
                _err(
                    "AGM_TIMELINE_OUT_OF_RANGE",
                    f"0 ≤ start < end ≤ duration_ms failed ({start_i},{end_i},{duration})",
                    f"nodes[{i}]",
                )
            )
    return errors


def validate_animations(graph: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for i, node in enumerate(graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        for j, track in enumerate(node.get("animations") or []):
            if not isinstance(track, dict):
                errors.append(_err("AGM_SCHEMA_INVALID", "animation track must be object", f"nodes[{i}].animations[{j}]"))
                continue
            prop = track.get("property")
            if not prop:
                errors.append(_err("AGM_SCHEMA_INVALID", "animation.property required", f"nodes[{i}].animations[{j}]"))
            keys = track.get("keyframes") or []
            times: list[int] = []
            for k, kf in enumerate(keys):
                if not isinstance(kf, dict) or "time_ms" not in kf or "value" not in kf:
                    errors.append(
                        _err("AGM_SCHEMA_INVALID", "keyframe needs time_ms+value", f"nodes[{i}].animations[{j}].keyframes[{k}]")
                    )
                    continue
                times.append(int(kf["time_ms"]))
            if times != sorted(times):
                errors.append(
                    _err("AGM_SCHEMA_INVALID", "keyframes must be sorted by time_ms", f"nodes[{i}].animations[{j}]")
                )
    return errors


def validate_assets(db: Optional[Session], graph: dict[str, Any], *, strict: bool = False) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    project_id = str(graph.get("project_id") or "")
    for i, node in enumerate(graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        ntype = node.get("type")
        payload = node.get("payload") or {}
        if ntype in {"image", "video", "logo"}:
            asset_id = payload.get("asset_id") or (payload.get("font") or {}).get("asset_id")
            # logo/image/video should reference asset_id when present
            ref = payload.get("asset_id")
            if ref:
                if not _is_uuid(str(ref)):
                    errors.append(_err("AGM_ASSET_NOT_FOUND", "invalid asset uuid", f"nodes[{i}].payload.asset_id"))
                elif db is not None and strict:
                    asset = db.get(Asset, str(ref))
                    if not asset or asset.soft_deleted:
                        errors.append(_err("AGM_ASSET_NOT_FOUND", f"asset {ref} not found", f"nodes[{i}].payload.asset_id"))
                    elif project_id and asset.project_id != project_id:
                        errors.append(_err("AGM_ASSET_FORBIDDEN", "asset not in project", f"nodes[{i}].payload.asset_id"))
        if ntype == "text":
            font = payload.get("font") or {}
            fa = font.get("asset_id")
            if fa and not _is_uuid(str(fa)) and strict:
                errors.append(_err("AGM_ASSET_NOT_FOUND", "font asset uuid invalid", f"nodes[{i}].payload.font.asset_id"))
    return errors


def validate_output_profile(profile: Optional[dict[str, Any]]) -> list[dict[str, str]]:
    if not profile:
        return []
    errors: list[dict[str, str]] = []
    container = (profile.get("container") or "mp4").lower()
    codec = (profile.get("codec") or "h264").lower()
    allowed_containers = {"mp4", "mov", "webm", "png_sequence", "exr_sequence"}
    allowed_codecs = {"h264", "h265", "prores422", "prores4444", "vp9", "av1", "png", "exr"}
    if container not in allowed_containers:
        errors.append(_err("AGM_RENDER_PROFILE_INVALID", f"unsupported container {container}", "profile.container"))
    if codec not in allowed_codecs:
        errors.append(_err("AGM_RENDER_PROFILE_INVALID", f"unsupported codec {codec}", "profile.codec"))
    alpha = bool(profile.get("alpha"))
    if alpha and codec not in {"prores4444", "vp9", "png", "exr"}:
        errors.append(_err("AGM_RENDER_PROFILE_INVALID", "alpha requires compatible codec", "profile.alpha"))
    return errors


def validate_graph(
    graph: dict[str, Any],
    *,
    db: Optional[Session] = None,
    profile: Optional[dict[str, Any]] = None,
    strict_assets: bool = False,
) -> dict[str, Any]:
    g = copy.deepcopy(graph) if isinstance(graph, dict) else {}
    errors: list[dict[str, str]] = []
    errors.extend(validate_schema_shape(g))
    if not any(e["code"] == "AGM_SCHEMA_INVALID" and e["path"] == "nodes" for e in errors):
        errors.extend(validate_graph_integrity(g))
        errors.extend(validate_timeline(g))
        errors.extend(validate_animations(g))
        errors.extend(validate_assets(db, g, strict=strict_assets))
        errors.extend(agm_typography.validate_graph_typography(g))
        errors.extend(agm_brand.validate_graph_brand(g))
        errors.extend(validate_output_profile(profile))
    # complexity limits
    nodes = g.get("nodes") or []
    if len(nodes) > 500:
        errors.append(_err("AGM_SCHEMA_INVALID", "graph exceeds 500 nodes", "nodes"))
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "error_codes": sorted({e["code"] for e in errors}),
        "schema_version": g.get("schema_version"),
    }
