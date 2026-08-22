"""Kurdish / Unicode normalization for search — never mutates display_text."""

from __future__ import annotations

import re
import unicodedata


_VARIANT_MAP = str.maketrans(
    {
        "ي": "ی",  # Arabic yeh → Kurdish yeh for search
        "ك": "ک",  # Arabic kaf → Kurdish kaf for search
        "ة": "ە",
    }
)


def normalize_for_search(text: str) -> str:
    if not text:
        return ""
    value = unicodedata.normalize("NFC", text)
    value = value.translate(_VARIANT_MAP)
    value = value.replace("\u0640", "")  # tatweel
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return value


def estimate_page_eighths(element_texts: list[str]) -> int:
    """Rough screenplay page estimate in eighths (1 page = 8)."""
    chars = sum(len(t or "") for t in element_texts)
    # ~1800 chars ≈ 1 page for mixed bilingual; clamp
    pages = max(chars / 1800.0, 0.125)
    return max(1, int(round(pages * 8)))
