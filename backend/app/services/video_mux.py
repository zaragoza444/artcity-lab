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
    """Loop a still poster under a WAV bed and produce a playable MP4."""
    return mux_frames_with_audio(
        frames_png=[poster_png],
        audio_wav=audio_wav,
        duration_seconds=duration_seconds,
        filename=filename,
        width=width,
        height=height,
        fps=fps,
    )


def mux_frames_with_audio(
    *,
    frames_png: list[bytes],
    audio_wav: bytes,
    duration_seconds: float,
    filename: str = "master.mp4",
    width: int = 1920,
    height: int = 1080,
    fps: float = 24.0,
) -> Optional[MediaFile]:
    """
    Encode a slideshow / multi-shot H.264 MP4 with AAC audio.
    Returns None when ffmpeg is missing.
    """
    if not ffmpeg_available():
        return None
    if not frames_png or not audio_wav:
        return None

    with tempfile.TemporaryDirectory(prefix="artcity-mux-") as tmp:
        root = Path(tmp)
        frames_dir = root / "frames"
        frames_dir.mkdir()
        for i, frame in enumerate(frames_png):
            (frames_dir / f"frame_{i:04d}.png").write_bytes(frame)
        audio = root / "bed.wav"
        out = root / "out.mp4"
        audio.write_bytes(audio_wav)
        hold = max(0.4, duration_seconds / max(1, len(frames_png)))
        # Concat demuxer for variable hold per still
        list_file = root / "frames.txt"
        lines = []
        for i in range(len(frames_png)):
            path = (frames_dir / f"frame_{i:04d}.png").as_posix()
            lines.append(f"file '{path}'")
            lines.append(f"duration {hold:.3f}")
        lines.append(f"file '{(frames_dir / f'frame_{len(frames_png) - 1:04d}.png').as_posix()}'")
        list_file.write_text("\n".join(lines), encoding="utf-8")
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
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
            subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            # Fallback: single-frame still loop
            if len(frames_png) == 1:
                return None
            return mux_frames_with_audio(
                frames_png=[frames_png[0]],
                audio_wav=audio_wav,
                duration_seconds=duration_seconds,
                filename=filename,
                width=width,
                height=height,
                fps=fps,
            )
        if not out.exists() or out.stat().st_size < 32:
            return None
        return MediaFile(
            filename=filename,
            content_type="video/mp4",
            data=out.read_bytes(),
            kind="video",
        )
