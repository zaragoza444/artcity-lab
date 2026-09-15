"""Brand DNA checks for AC Graphic Motion — protected logos and locked brand rules."""

from __future__ import annotations

from typing import Any


def _err(code: str, message: str, path: str = "") -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def validate_graph_brand(graph: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    brand = graph.get("brand_context") or {}
    locked_logos = set(str(x) for x in (brand.get("protected_logo_asset_ids") or []))
    approved_fonts = set(str(x) for x in (brand.get("approved_font_asset_ids") or []))
    approved_colors = set(str(x).lower() for x in (brand.get("approved_colors") or []))

    for i, node in enumerate(graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        ntype = node.get("type")
        payload = node.get("payload") or {}
        if ntype == "logo":
            asset_id = str(payload.get("asset_id") or "")
            preserve = bool(payload.get("preserve_exact_pixels", True))
            if preserve:
                # Forbidden mutation flags
                if payload.get("recolor") or payload.get("generative_redraw") or payload.get("geometry_rewrite"):
                    errors.append(
                        _err(
                            "AGM_BRAND_LOGO_MUTATION",
                            "protected logo forbids recolor/redraw/geometry rewrite",
                            f"nodes[{i}].payload",
                        )
                    )
                for eff in node.get("effects") or []:
                    if isinstance(eff, dict) and eff.get("destructive"):
                        errors.append(
                            _err(
                                "AGM_BRAND_LOGO_MUTATION",
                                "destructive effect on protected logo",
                                f"nodes[{i}].effects",
                            )
                        )
            if locked_logos and asset_id and asset_id not in locked_logos and brand.get("enforce_logo_allowlist"):
                errors.append(_err("AGM_BRAND_LOGO_MUTATION", "logo not in Brand DNA allowlist", f"nodes[{i}]"))
        if ntype == "text" and approved_fonts:
            font_id = str((payload.get("font") or {}).get("asset_id") or "")
            if font_id and font_id not in approved_fonts and brand.get("enforce_font_allowlist"):
                errors.append(_err("AGM_FONT_GLYPH_MISSING", "font not approved in Brand DNA", f"nodes[{i}].payload.font"))
        if approved_colors and brand.get("enforce_palette"):
            fill = str(payload.get("fill") or "").lower()
            if fill and fill not in approved_colors and ntype in {"text", "shape"}:
                errors.append(_err("AGM_SCHEMA_INVALID", "color not in Brand DNA palette", f"nodes[{i}].payload.fill"))
    return errors


def assert_no_logo_mutation(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, str]]:
    """Compare protected logo nodes across patch revisions."""
    errors: list[dict[str, str]] = []
    before_logos = {
        n["id"]: n
        for n in (before.get("nodes") or [])
        if isinstance(n, dict) and n.get("type") == "logo" and (n.get("payload") or {}).get("preserve_exact_pixels", True)
    }
    after_by_id = {n["id"]: n for n in (after.get("nodes") or []) if isinstance(n, dict) and "id" in n}
    for lid, node in before_logos.items():
        nxt = after_by_id.get(lid)
        if nxt is None:
            continue
        bp = node.get("payload") or {}
        ap = nxt.get("payload") or {}
        for key in ("asset_id", "preserve_exact_pixels"):
            if bp.get(key) != ap.get(key):
                errors.append(
                    _err("AGM_BRAND_LOGO_MUTATION", f"protected logo field {key} changed", f"nodes.{lid}.payload.{key}")
                )
        # geometry rewrite via transform scale extremes
        bt = node.get("transform") or {}
        at = nxt.get("transform") or {}
        if bp.get("preserve_exact_pixels") and (
            at.get("destructive_crop") or ap.get("recolor") or ap.get("generative_redraw")
        ):
            errors.append(_err("AGM_BRAND_LOGO_MUTATION", "protected logo mutated", f"nodes.{lid}"))
        if "scale" in at and "scale" in bt and at["scale"] != bt["scale"] and bp.get("lock_scale"):
            errors.append(_err("AGM_BRAND_LOGO_MUTATION", "logo scale locked by Brand DNA", f"nodes.{lid}.transform"))
    return errors
