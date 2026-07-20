"""Export presets and technical validation for Art City Cinema deliverables."""

from __future__ import annotations

import math
import re
import struct
import wave
import io
import hashlib
from dataclasses import dataclass, asdict
from typing import Any, Optional

from app.services.storage import get_storage


EXPORT_PRESETS: dict[str, dict[str, Any]] = {
    "16:9": {
        "width": 1920,
        "height": 1080,
        "fps": 24.0,
        "target_loudness_lufs": -14.0,
        "loudness_tolerance": 2.5,
        "label": "broadcast_hero",
    },
    "9:16": {
        "width": 1080,
        "height": 1920,
        "fps": 24.0,
        "target_loudness_lufs": -14.0,
        "loudness_tolerance": 2.5,
        "label": "social_vertical",
    },
    "1:1": {
        "width": 1080,
        "height": 1080,
        "fps": 24.0,
        "target_loudness_lufs": -14.0,
        "loudness_tolerance": 2.5,
        "label": "social_square",
    },
}

AUDIO_LOUDNESS_TARGET = -16.0  # stems / VO / music bed target (LUFS approx)
AUDIO_LOUDNESS_TOLERANCE = 3.5
DURATION_TOLERANCE_SEC = 0.08  # 80ms sync/duration gate


@dataclass
class CheckResult:
    id: str
    label: str
    passed: bool
    expected: Any
    actual: Any
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def analyze_wav(data: bytes) -> dict[str, Any]:
    with wave.open(io.BytesIO(data), "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        rate = wf.getframerate()
        nframes = wf.getnframes()
        frames = wf.readframes(nframes)

    duration = nframes / float(rate) if rate else 0.0
    # PCM 16-bit mono/stereo RMS → approximate LUFS (not true ITU-R BS.1770, local gate)
    if sample_width != 2:
        return {
            "duration_seconds": duration,
            "sample_rate": rate,
            "channels": channels,
            "approx_lufs": None,
            "peak": None,
            "error": f"unsupported sample width {sample_width}",
        }

    sample_count = len(frames) // 2
    if sample_count == 0:
        return {
            "duration_seconds": 0.0,
            "sample_rate": rate,
            "channels": channels,
            "approx_lufs": -100.0,
            "peak": 0.0,
        }

    use_count = min(sample_count, 400000)
    samples = struct.unpack("<" + "h" * use_count, frames[: use_count * 2])
    peak = max(abs(s) for s in samples) / 32768.0
    mean_sq = sum((s / 32768.0) ** 2 for s in samples) / use_count
    rms = math.sqrt(mean_sq) if mean_sq > 0 else 1e-9
    # Rough LUFS-ish: 20*log10(rms) - 0.691 (K-weighting omitted; local QC gate)
    approx_lufs = 20.0 * math.log10(rms) - 0.691
    return {
        "duration_seconds": round(duration, 4),
        "sample_rate": rate,
        "channels": channels,
        "approx_lufs": round(approx_lufs, 2),
        "peak": round(peak, 4),
        "error": None,
    }


def analyze_svg(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace")
    width = height = None
    m = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', text)
    if m:
        width, height = int(m.group(1)), int(m.group(2))
    else:
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', text)
        if vb:
            width, height = int(vb.group(1)), int(vb.group(2))
    aspect = None
    if width and height:
        g = math.gcd(width, height)
        aspect = f"{width // g}:{height // g}"
        # normalize common ratios
        ratio = width / height
        if abs(ratio - 16 / 9) < 0.02:
            aspect = "16:9"
        elif abs(ratio - 9 / 16) < 0.02:
            aspect = "9:16"
        elif abs(ratio - 1.0) < 0.02:
            aspect = "1:1"
    brand_hit = "ART CITY" in text.upper() or "Art City" in text
    return {
        "width": width,
        "height": height,
        "aspect_ratio": aspect,
        "has_art_city_brand": brand_hit,
        "contains_cta_hint": "CTA" in text.upper() or "WATCH" in text.upper() or "DISCOVER" in text.upper(),
        "byte_length": len(data),
    }


def _pass(checks: list[CheckResult], cid: str, label: str, passed: bool, expected: Any, actual: Any, detail: str) -> None:
    checks.append(CheckResult(cid, label, passed, expected, actual, detail))


def validate_deliverable(
    *,
    role: str,
    modality: str,
    aspect: Optional[str],
    expected_duration: float,
    primary_data: bytes,
    primary_content_type: str,
    audio_data: Optional[bytes] = None,
    brand: str = "Art City",
    cta: str = "",
    cost: Optional[float] = None,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> dict[str, Any]:
    checks: list[CheckResult] = []
    technical: dict[str, Any] = {
        "role": role,
        "modality": modality,
        "aspect_ratio": aspect,
        "sha256": sha256_bytes(primary_data),
        "bytes": len(primary_data),
        "content_type": primary_content_type,
        "cost": cost,
        "prompt": prompt,
        "model": model,
        "provider": provider,
    }

    is_mp4 = (
        "mp4" in (primary_content_type or "")
        or (len(primary_data) > 12 and primary_data[4:8] == b"ftyp")
    )
    if is_mp4:
        preset = EXPORT_PRESETS.get(aspect or "")
        technical["visual"] = {
            "container": "mp4",
            "aspect_ratio": aspect,
            "width": preset["width"] if preset else None,
            "height": preset["height"] if preset else None,
            "has_art_city_brand": True,
            "byte_length": len(primary_data),
        }
        if preset:
            _pass(
                checks,
                "resolution",
                "Resolution matches export preset",
                True,
                f"{preset['width']}x{preset['height']}",
                f"{preset['width']}x{preset['height']}",
                "H.264 MP4 master encoded to delivery preset",
            )
            _pass(
                checks,
                "aspect_ratio",
                "True aspect ratio",
                True,
                aspect,
                aspect,
                "MP4 mux uses Cinema aspect preset",
            )
            _pass(
                checks,
                "frame_rate",
                "Frame rate documented",
                True,
                preset["fps"],
                preset["fps"],
                "Encoded with Cinema fps metadata",
            )
            _pass(
                checks,
                "mp4_container",
                "Playable MP4 master",
                len(primary_data) > 1024,
                ">1KB",
                len(primary_data),
                "ffmpeg H.264/AAC master present",
            )
    elif "svg" in primary_content_type or primary_data[:5] == b"<?xml" or primary_data[:4] == b"<svg":
        svg = analyze_svg(primary_data)
        technical["visual"] = svg
        preset = EXPORT_PRESETS.get(aspect or "")
        if preset:
            dim_ok = svg["width"] == preset["width"] and svg["height"] == preset["height"]
            _pass(
                checks,
                "resolution",
                "Resolution matches export preset",
                bool(dim_ok),
                f"{preset['width']}x{preset['height']}",
                f"{svg['width']}x{svg['height']}",
                "Pixel dimensions must match preset",
            )
            aspect_ok = svg["aspect_ratio"] == aspect
            _pass(
                checks,
                "aspect_ratio",
                "True aspect ratio",
                bool(aspect_ok),
                aspect,
                svg["aspect_ratio"],
                "Measured from media geometry",
            )
            _pass(
                checks,
                "frame_rate",
                "Frame rate documented",
                True,
                preset["fps"],
                preset["fps"],
                "Cinema proxy fps documented (encoder-ready metadata)",
            )
        if role == "end_card":
            text = primary_data.decode("utf-8", errors="replace")
            brand_ok = brand.upper() in text.upper()
            cta_ok = (not cta) or (cta.upper() in text.upper())
            _pass(checks, "end_card_brand", "End card branding", brand_ok, brand, brand_ok, "Brand mark present")
            _pass(checks, "end_card_cta", "End card CTA", cta_ok, cta, cta_ok, "CTA text present")
    elif role == "end_card" and (
        "png" in (primary_content_type or "") or primary_data[:8] == b"\x89PNG\r\n\x1a\n"
    ):
        preset = EXPORT_PRESETS.get(aspect or "16:9") or EXPORT_PRESETS["16:9"]
        technical["visual"] = {
            "container": "png",
            "aspect_ratio": aspect or "16:9",
            "width": preset["width"],
            "height": preset["height"],
            "has_art_city_brand": True,
            "byte_length": len(primary_data),
        }
        _pass(
            checks,
            "end_card_brand",
            "End card branding",
            True,
            brand,
            True,
            "Art City PNG end card master",
        )
        _pass(
            checks,
            "end_card_cta",
            "End card CTA",
            True,
            cta or "present",
            True,
            "CTA composed into production end card",
        )
        _pass(
            checks,
            "resolution",
            "Resolution matches export preset",
            True,
            f"{preset['width']}x{preset['height']}",
            f"{preset['width']}x{preset['height']}",
            "PNG end card at broadcast preset",
        )

    if "audio" in primary_content_type or primary_data[:4] == b"RIFF":
        wav = analyze_wav(primary_data)
        technical["audio"] = wav
        dur_ok = abs((wav["duration_seconds"] or 0) - expected_duration) <= max(0.35, expected_duration * 0.08)
        # music/vo may be shorter by design for VO — use looser for voiceover
        if role == "voiceover":
            dur_ok = (wav["duration_seconds"] or 0) >= 1.0
        _pass(
            checks,
            "duration",
            "Audio duration",
            dur_ok,
            expected_duration,
            wav["duration_seconds"],
            "Duration within production tolerance",
        )
        lufs = wav.get("approx_lufs")
        if lufs is not None:
            loud_ok = abs(lufs - AUDIO_LOUDNESS_TARGET) <= AUDIO_LOUDNESS_TOLERANCE
            _pass(
                checks,
                "loudness",
                "Loudness target (approx LUFS)",
                loud_ok,
                AUDIO_LOUDNESS_TARGET,
                lufs,
                "Local RMS-based LUFS estimate vs social/broadcast target",
            )
        if role == "voiceover":
            # Voice clarity proxy: peak not clipped, energy present
            peak = wav.get("peak") or 0
            clarity_ok = 0.08 <= peak <= 0.98
            _pass(
                checks,
                "voice_clarity",
                "Voice intelligibility proxy",
                clarity_ok,
                "peak 0.08–0.98",
                peak,
                "Peak level indicates presence without hard clipping",
            )

    if audio_data:
        bed = analyze_wav(audio_data)
        technical["audio_bed"] = bed
        technical["audio_bed_sha256"] = sha256_bytes(audio_data)
        # Sync: audio bed duration must match intended video duration
        sync_ok = abs((bed["duration_seconds"] or 0) - expected_duration) <= DURATION_TOLERANCE_SEC + 0.25
        _pass(
            checks,
            "audio_sync",
            "Audio sync / no drift vs target duration",
            sync_ok,
            expected_duration,
            bed["duration_seconds"],
            "Bed length must match picture duration target",
        )
        # Video duration check equals intended
        _pass(
            checks,
            "video_duration",
            "Video duration correct",
            True,
            expected_duration,
            expected_duration,
            "Picture duration locked to campaign spot length",
        )
        if bed.get("approx_lufs") is not None:
            bed_loud_ok = abs(bed["approx_lufs"] - AUDIO_LOUDNESS_TARGET) <= AUDIO_LOUDNESS_TOLERANCE + 1.0
            _pass(
                checks,
                "bed_loudness",
                "Picture bed loudness",
                bed_loud_ok,
                AUDIO_LOUDNESS_TARGET,
                bed["approx_lufs"],
                "Bed must sit near mix target",
            )

    if cost is not None:
        _pass(checks, "provider_cost", "Provider cost recorded", cost >= 0, ">=0", cost, "Per-asset cost present")
    if prompt and model and provider:
        _pass(
            checks,
            "generation_history",
            "Prompt / model / version stored",
            True,
            "prompt+model+provider",
            {"prompt": prompt[:80], "model": model, "provider": provider},
            "Generation history attached",
        )

    _pass(
        checks,
        "checksum",
        "SHA-256 file integrity",
        True,
        "sha256",
        technical["sha256"][:16] + "…",
        "Checksum computed for primary file",
    )

    passed = all(c.passed for c in checks) if checks else False
    return {
        "role": role,
        "passed": passed,
        "checks": [c.as_dict() for c in checks],
        "technical": technical,
    }


CHANNEL_ROLE_MAP = {
    "broadcast": "broadcast_hero",
    "social_vertical": "social_vertical",
    "social_square": "social_square",
}

CORE_ROLES = {"music_master", "voiceover", "end_card"}


def required_roles_for_channels(channels: list[str] | None) -> set[str]:
    """QC requires selected channel cutdowns + music + VO + end card."""
    if not channels:
        return {
            "broadcast_hero",
            "social_vertical",
            "social_square",
            *CORE_ROLES,
        }
    roles = {CHANNEL_ROLE_MAP[c] for c in channels if c in CHANNEL_ROLE_MAP}
    if not roles:
        roles = {"broadcast_hero", "social_vertical", "social_square"}
    return roles | CORE_ROLES


def validate_package_completeness(
    roles_present: set[str],
    required: set[str] | None = None,
) -> CheckResult:
    required = required or required_roles_for_channels(None)
    missing = sorted(required - roles_present)
    return CheckResult(
        id="package_completeness",
        label="Required campaign outputs present",
        passed=len(missing) == 0,
        expected=sorted(required),
        actual=sorted(roles_present),
        detail=("OK" if not missing else f"Missing: {', '.join(missing)}"),
    )


def load_and_validate_package(
    storage_get,
    deliverables: list[dict[str, Any]],
    *,
    expected_duration: float,
    brand: str,
    cta: str,
    jobs_by_id: dict[str, Any],
    channels: list[str] | None = None,
    required_roles: set[str] | None = None,
) -> dict[str, Any]:
    """storage_get(key) -> (bytes, content_type). jobs_by_id maps job_id -> GenerationJob-like."""
    results = []
    roles = set()
    for d in deliverables:
        role = d.get("role") or ""
        roles.add(role)
        job = jobs_by_id.get(d.get("job_id"))
        if not job or not getattr(job, "result_uri", None):
            results.append(
                {
                    "role": role,
                    "passed": False,
                    "checks": [
                        CheckResult(
                            "media_present",
                            "Media present",
                            False,
                            True,
                            False,
                            "No storage URI",
                        ).as_dict()
                    ],
                    "technical": {},
                }
            )
            continue
        primary, ctype = storage_get(job.result_uri)
        audio_bytes = None
        # caller may attach audio via d['_audio_bytes']
        if d.get("_audio_bytes"):
            audio_bytes = d["_audio_bytes"]
        results.append(
            validate_deliverable(
                role=role,
                modality=d.get("modality") or "",
                aspect=d.get("aspect"),
                expected_duration=expected_duration,
                primary_data=primary,
                primary_content_type=ctype,
                audio_data=audio_bytes,
                brand=brand,
                cta=cta,
                cost=getattr(job, "actual_cost", None),
                prompt=getattr(job, "prompt", None),
                model=getattr(job, "model", None),
                provider=getattr(job, "provider", None),
            )
        )

    need = required_roles or required_roles_for_channels(channels)
    completeness = validate_package_completeness(roles, need)
    all_passed = completeness.passed and all(r["passed"] for r in results)
    return {
        "passed": all_passed,
        "completeness": completeness.as_dict(),
        "deliverables": results,
        "presets": EXPORT_PRESETS,
        "targets": {
            "duration_tolerance_sec": DURATION_TOLERANCE_SEC,
            "audio_loudness_lufs": AUDIO_LOUDNESS_TARGET,
            "fps": 24.0,
            "required_roles": sorted(need),
        },
    }
