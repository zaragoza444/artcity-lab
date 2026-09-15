"""AC Graphic Motion typography — NFC, BiDi, Sorani-safe animation units."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Kurdish Sorani-specific letters commonly required for glyph coverage checks
SORANI_LETTERS = set("ئەپچڕژڤکگڵھۆۊێیوو")


def _err(code: str, message: str, path: str = "") -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def normalize_text(text: str, form: str = "NFC") -> str:
    return unicodedata.normalize(form or "NFC", text)


def grapheme_clusters(text: str) -> list[str]:
    """Approximate grapheme split (extended grapheme clusters lite via NFC + combining marks)."""
    text = normalize_text(text)
    clusters: list[str] = []
    buf = ""
    for ch in text:
        if buf and unicodedata.combining(ch) == 0 and not _is_joiner(ch):
            clusters.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        clusters.append(buf)
    return clusters


def _is_joiner(ch: str) -> bool:
    return ch in {"\u200c", "\u200d", "\u200e", "\u200f"}


def word_units(text: str) -> list[str]:
    """Word-level units for Sorani motion (recommended animation_unit)."""
    text = normalize_text(text)
    # Split on whitespace while preserving RTL content integrity
    return [w for w in re.split(r"(\s+)", text) if w != ""]


def has_sorani_glyphs(text: str) -> bool:
    return any(ch in SORANI_LETTERS or ("\u0600" <= ch <= "\u06FF") for ch in text)


def shape_text(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Deterministic shaping report.
    Real HarfBuzz may be provided by a sidecar; core always applies NFC + BiDi metadata.
    Never raster-generates Kurdish lettering.
    """
    raw = str(payload.get("text") or "")
    form = str(payload.get("normalization") or "NFC")
    normalized = normalize_text(raw, form)
    direction = payload.get("direction") or "rtl"
    unit = payload.get("animation_unit") or "word"
    if unit == "grapheme":
        units = grapheme_clusters(normalized)
    elif unit == "word":
        units = word_units(normalized)
    elif unit == "line":
        units = normalized.splitlines() or [normalized]
    else:
        units = [normalized]

    shaping_engine = payload.get("shaping_engine") or "harfbuzz"
    # Fail closed if caller requests harfbuzz but tries to animate by code points
    if unit not in {"block", "line", "word", "grapheme"}:
        raise ValueError("AGM_RTL_SHAPING_FAILED")

    return {
        "normalized": normalized,
        "direction": direction,
        "unicode_bidi": payload.get("unicode_bidi") or "plaintext",
        "animation_unit": unit,
        "units": units,
        "shaping_engine": shaping_engine,
        "engine_status": "nfc_bidi_ready",
        "contains_arabic_script": has_sorani_glyphs(normalized),
    }


def validate_graph_typography(graph: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for i, node in enumerate(graph.get("nodes") or []):
        if not isinstance(node, dict) or node.get("type") != "text":
            continue
        payload = node.get("payload") or {}
        text = payload.get("text")
        if text is None:
            errors.append(_err("AGM_SCHEMA_INVALID", "text payload.text required", f"nodes[{i}].payload.text"))
            continue
        if not isinstance(text, str):
            errors.append(_err("AGM_SCHEMA_INVALID", "text must be Unicode string", f"nodes[{i}].payload.text"))
            continue
        # Forbid code-point animation unit alias
        unit = payload.get("animation_unit") or "word"
        if unit in {"codepoint", "code_point", "char"}:
            errors.append(
                _err(
                    "AGM_RTL_SHAPING_FAILED",
                    "never naively animate code points; use word/grapheme",
                    f"nodes[{i}].payload.animation_unit",
                )
            )
        engine = payload.get("shaping_engine") or "harfbuzz"
        if engine != "harfbuzz":
            errors.append(
                _err("AGM_RTL_SHAPING_FAILED", "shaping_engine must be harfbuzz in v1", f"nodes[{i}].payload.shaping_engine")
            )
        try:
            shape_text(payload)
        except ValueError:
            errors.append(_err("AGM_RTL_SHAPING_FAILED", "shaping failed", f"nodes[{i}]"))
        # Glyph coverage soft check for Sorani content
        font = payload.get("font") or {}
        if has_sorani_glyphs(text) and font.get("require_sorani_coverage") is True and not font.get("asset_id"):
            errors.append(_err("AGM_FONT_GLYPH_MISSING", "Sorani font asset required", f"nodes[{i}].payload.font"))
    return errors
