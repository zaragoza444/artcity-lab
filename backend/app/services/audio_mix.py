"""Mix music + VO with ducking for Cinema masters (LUFS-targeted WAV)."""

from __future__ import annotations

import io
import math
import struct
import wave
from typing import Optional

from app.services.media_factory import MediaFile, _normalize_to_lufs, _wav_bytes


def _read_wav_mono(data: bytes) -> tuple[list[float], int]:
    with wave.open(io.BytesIO(data), "rb") as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())
    if width != 2:
        return [], rate
    samples = struct.unpack("<" + "h" * (len(frames) // 2), frames)
    if channels == 1:
        floats = [s / 32768.0 for s in samples]
    else:
        floats = []
        for i in range(0, len(samples), channels):
            floats.append(sum(samples[i : i + channels]) / channels / 32768.0)
    return floats, rate


def mix_music_and_voice(
    music_wav: bytes,
    voice_wav: bytes,
    *,
    duration_seconds: float,
    duck_db: float = -10.0,
    filename: str = "mix_master.wav",
) -> MediaFile:
    music, rate_m = _read_wav_mono(music_wav)
    voice, rate_v = _read_wav_mono(voice_wav)
    rate = rate_m or rate_v or 22050
    target = int(duration_seconds * rate)

    def fit(samples: list[float]) -> list[float]:
        if len(samples) >= target:
            return samples[:target]
        return samples + [0.0] * (target - len(samples))

    music = fit(music)
    voice = fit(voice)
    duck = 10 ** (duck_db / 20.0)
    # Simple envelope: when |voice| > threshold, duck music
    out: list[float] = []
    window = max(1, int(0.02 * rate))
    for i in range(target):
        # local voice energy
        start = max(0, i - window)
        energy = sum(abs(voice[j]) for j in range(start, i + 1)) / (i - start + 1)
        gain = duck if energy > 0.02 else 1.0
        # Smooth gain toward duck
        sample = music[i] * gain + voice[i]
        out.append(max(-1.0, min(1.0, sample)))
    out = _normalize_to_lufs(out, -14.0)
    return MediaFile(
        filename=filename,
        content_type="audio/wav",
        data=_wav_bytes(out, sample_rate=rate),
        kind="audio",
    )


def optional_external_tts(script: str, *, brand: str = "Art City") -> Optional[bytes]:
    """Try OpenAI TTS when OPENAI_API_KEY is configured; else None."""
    from app.core.config import get_settings

    settings = get_settings()
    key = (settings.openai_api_key or "").strip()
    if not key or not script.strip():
        return None
    try:
        import httpx

        # OpenAI audio/speech — fails soft if network/model unavailable
        resp = httpx.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": script[:4000],
                "response_format": "wav",
            },
            timeout=45.0,
        )
        if resp.status_code >= 400:
            return None
        return resp.content
    except Exception:
        return None
