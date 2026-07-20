"""Encode Art City Cinema masters: poster frames + WAV → H.264/AAC MP4 via ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.services.media_factory import MediaFile


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def mux_still_with_audio(
    *,
    poster_png: bytes,
    audio_wav: bytes,
    duration_seconds: float,
    filename: str = "master.mp4",
    width: int = 1920,
    height: int = 1080,
    fps: float = 24.0,
) -> Optional[MediaFile]:
    """
    Loop a still poster under a WAV bed and produce a playable MP4.
    Returns None when ffmpeg is not installed (SVG/WAV pack still ships).
    """
    if not ffmpeg_available():
        return None
    if not poster_png or not audio_wav:
        return None

    with tempfile.TemporaryDirectory(prefix="artcity-mux-") as tmp:
        root = Path(tmp)
        poster = root / "poster.png"
        audio = root / "bed.wav"
        out = root / "out.mp4"
        poster.write_bytes(poster_png)
        audio.write_bytes(audio_wav)
        # Scale/pad to exact delivery size; stillimage + AAC for social/broadcast preview masters.
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-i",
            str(poster),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(fps),
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x05070b",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-t",
            f"{max(1.0, duration_seconds):.3f}",
            "-movflags",
            "+faststart",
            str(out),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return None
        if not out.exists() or out.stat().st_size < 32:
            return None
        return MediaFile(
            filename=filename,
            content_type="video/mp4",
            data=out.read_bytes(),
            kind="video",
        )
