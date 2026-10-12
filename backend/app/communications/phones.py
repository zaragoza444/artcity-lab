"""E.164 normalization. Iraqi trunk prefixes are accepted only when the library validates them."""

from __future__ import annotations

import re

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

_DIGITS = re.compile(r"\D+")


def digits_only(value: str | None) -> str:
    return _DIGITS.sub("", value or "")


def phones_equal(left: str | None, right: str | None) -> bool:
    return digits_only(left) == digits_only(right) and bool(digits_only(left))


def mask_phone(e164: str | None) -> str:
    raw = e164 or ""
    if len(raw) < 6:
        return "•••"
    return raw[:4] + "•" * max(2, len(raw) - 6) + raw[-2:]


def normalize_phone(raw: str | None) -> tuple[str | None, str | None, str]:
    """Return (e164, country_iso, error_code). error_code is empty when valid."""
    text = (raw or "").strip()
    if not text:
        return None, None, "required_field_missing"
    if text[0] in "=@\t\r" or text.startswith("="):
        return None, None, "bad_format"
    if text.startswith("-"):
        return None, None, "bad_format"
    candidate = text
    if candidate.startswith("00"):
        candidate = "+" + candidate[2:]
    region = None
    if candidate.startswith("0") and not candidate.startswith("+"):
        region = "IQ"
    try:
        parsed = phonenumbers.parse(candidate, region)
    except NumberParseException:
        return None, None, "invalid_phone"
    if not phonenumbers.is_valid_number(parsed):
        return None, None, "invalid_phone"
    e164 = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    iso = phonenumbers.region_code_for_number(parsed) or ""
    return e164, iso or None, ""


def csv_safe(value: str | None) -> str:
    text = "" if value is None else str(value)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        if text.startswith("+") and text[1:].isdigit():
            return text
        return "'" + text
    return text
