"""World advertising delivery presets for Art City Cinema packages."""

from __future__ import annotations

from typing import Any


# Platform-facing specs layered on Cinema channel roles.
DELIVERY_PRESETS: dict[str, dict[str, Any]] = {
    "broadcast_tv": {
        "label": "Broadcast / TV",
        "channel": "broadcast",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "fps": 25.0,
        "codec": "h264",
        "audio": "aac_stereo",
        "loudness_lufs": -23.0,
        "max_duration_seconds": 60,
        "captions": "burn_in_optional",
    },
    "youtube": {
        "label": "YouTube",
        "channel": "broadcast",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "fps": 24.0,
        "codec": "h264",
        "audio": "aac_stereo",
        "loudness_lufs": -14.0,
        "max_duration_seconds": 60,
        "captions": "sidecar_vtt",
    },
    "meta_feed": {
        "label": "Meta Feed",
        "channel": "social_square",
        "aspect": "1:1",
        "width": 1080,
        "height": 1080,
        "fps": 30.0,
        "codec": "h264",
        "audio": "aac_stereo",
        "loudness_lufs": -14.0,
        "max_duration_seconds": 15,
        "captions": "burn_in_recommended",
    },
    "meta_stories": {
        "label": "Meta / TikTok Stories",
        "channel": "social_vertical",
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "fps": 30.0,
        "codec": "h264",
        "audio": "aac_stereo",
        "loudness_lufs": -14.0,
        "max_duration_seconds": 15,
        "captions": "burn_in_recommended",
    },
    "ctv": {
        "label": "CTV / Connected TV",
        "channel": "broadcast",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "fps": 24.0,
        "codec": "h264",
        "audio": "aac_stereo",
        "loudness_lufs": -24.0,
        "max_duration_seconds": 30,
        "captions": "sidecar_vtt",
    },
}


VARIANT_LABELS = {
    "A": "Control — primary brief",
    "B": "Alt CTA emphasis",
    "C": "Alt music / emotional beat",
}


def resolve_delivery_targets(targets: list[str] | None) -> list[dict[str, Any]]:
    if not targets:
        return [dict(v, id=k) for k, v in DELIVERY_PRESETS.items() if k in {"youtube", "meta_stories", "broadcast_tv"}]
    out: list[dict[str, Any]] = []
    for t in targets:
        preset = DELIVERY_PRESETS.get(t)
        if preset:
            out.append(dict(preset, id=t))
    return out or resolve_delivery_targets(None)


def variant_brief(base_brief: str, base_cta: str, variant: str) -> tuple[str, str]:
    if variant == "B":
        return (
            f"{base_brief} Emphasize the call to action and brand payoff.",
            f"{base_cta} — now",
        )
    if variant == "C":
        return (
            f"{base_brief} Softer emotional open, stronger human beat before brand.",
            base_cta,
        )
    return base_brief, base_cta


def variant_music_style(base: str, variant: str) -> str:
    if variant == "C":
        return {"epic": "warm", "warm": "soft", "pulse": "warm", "soft": "warm"}.get(base, "warm")
    return base
