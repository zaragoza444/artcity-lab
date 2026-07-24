"""External generation clients — used when production API keys are configured."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import get_settings


@dataclass
class ExternalMedia:
    data: bytes
    content_type: str
    filename: str
    provider: str
    cost: float


def _has_fal() -> bool:
    return bool((get_settings().fal_api_key or "").strip())


def _has_openai() -> bool:
    return bool((get_settings().openai_api_key or "").strip())


def _has_eleven() -> bool:
    return bool((get_settings().elevenlabs_api_key or "").strip())


def external_available(modality: str) -> bool:
    if modality == "image":
        return _has_fal() or _has_openai()
    if modality == "video":
        # FAL native video, or OpenAI DALL·E frames + TTS + ffmpeg
        return _has_fal() or _has_openai()
    if modality == "voice":
        return _has_openai() or _has_eleven()
    if modality in {"music", "audio"}:
        return _has_fal()
    return False


def generate_external(
    *,
    modality: str,
    prompt: str,
    duration_seconds: float = 4.0,
    aspect: str = "16:9",
) -> Optional[ExternalMedia]:
    """Try cloud providers in order; return None so callers can use Art City masters."""
    settings = get_settings()
    if not settings.external_providers_enabled:
        return None
    try:
        if modality == "image":
            return _gen_image(prompt, aspect)
        if modality == "video":
            return _gen_video(prompt, duration_seconds, aspect)
        if modality == "voice":
            return _gen_voice(prompt)
        if modality == "music":
            return _gen_music(prompt, duration_seconds)
        if modality == "audio":
            return _gen_sfx(prompt)
    except Exception as exc:  # noqa: BLE001
        print(f"external_gen failed modality={modality}: {exc}")
        return None
    return None


def _gen_image(prompt: str, aspect: str) -> Optional[ExternalMedia]:
    # Prefer fal FLUX; OpenAI images as secondary
    if _has_fal():
        size = {
            "16:9": "landscape_16_9",
            "9:16": "portrait_16_9",
            "1:1": "square_hd",
        }.get(aspect, "landscape_16_9")
        data = _fal_run(
            "fal-ai/flux/schnell",
            {
                "prompt": prompt[:2000],
                "image_size": size,
                "num_images": 1,
                "enable_safety_checker": True,
            },
        )
        url = _first_image_url(data)
        if url:
            raw, ctype = _download(url)
            ext = "png" if "png" in ctype else "jpg"
            return ExternalMedia(raw, ctype or f"image/{ext}", f"fal-image.{ext}", "fal", 0.04)
    if _has_openai():
        settings = get_settings()
        # Prefer gpt-image-1 (current OpenAI image model); fall back to dall-e-3 for older keys.
        attempts = [
            {
                "model": "gpt-image-1",
                "prompt": prompt[:3900],
                "size": "1024x1024" if aspect == "1:1" else ("1536x1024" if aspect != "9:16" else "1024x1536"),
                "n": 1,
            },
            {
                "model": "dall-e-3",
                "prompt": prompt[:3900],
                "size": {"16:9": "1792x1024", "9:16": "1024x1792", "1:1": "1024x1024"}.get(aspect, "1024x1024"),
                "n": 1,
            },
        ]
        with httpx.Client(timeout=90.0) as client:
            for payload in attempts:
                resp = client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json=payload,
                )
                if resp.status_code >= 400:
                    print(f"openai image {payload['model']} failed: {resp.status_code} {resp.text[:240]}")
                    continue
                body = resp.json()
                row = (body.get("data") or [{}])[0]
                url = row.get("url")
                b64 = row.get("b64_json")
                if url:
                    raw, ctype = _download(url)
                    return ExternalMedia(raw, ctype or "image/png", "openai-image.png", "openai", 0.08)
                if b64:
                    import base64

                    raw = base64.b64decode(b64)
                    return ExternalMedia(raw, "image/png", "openai-image.png", "openai", 0.08)
    return None


def _gen_video(prompt: str, duration_seconds: float, aspect: str) -> Optional[ExternalMedia]:
    if _has_fal():
        # MiniMax / LTX style short clip — soft-fail on queue errors
        payload = {
            "prompt": prompt[:1500],
            "aspect_ratio": aspect if aspect in {"16:9", "9:16", "1:1"} else "16:9",
        }
        data = _fal_run("fal-ai/minimax/video-01-live", payload, timeout=120.0)
        url = None
        if isinstance(data, dict):
            video = data.get("video") or {}
            url = video.get("url") if isinstance(video, dict) else None
            url = url or data.get("video_url") or data.get("url")
        if url:
            raw, ctype = _download(url)
            return ExternalMedia(raw, ctype or "video/mp4", "fal-video.mp4", "fal", 0.35)
    if _has_openai():
        return _gen_video_openai(prompt, duration_seconds, aspect)
    return None


def _as_png(image_bytes: bytes) -> bytes:
    from io import BytesIO

    from PIL import Image

    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _gen_video_openai(prompt: str, duration_seconds: float, aspect: str) -> Optional[ExternalMedia]:
    """Production video without FAL: DALL·E shot frames + OpenAI TTS + ffmpeg MP4."""
    from app.services.video_mux import mux_frames_with_audio

    duration = max(3.0, min(float(duration_seconds or 5.0), 12.0))
    # Keep shot count lean for production latency/cost (Cinema runs multiple cutdowns).
    frame_count = 2 if duration <= 8 else 3
    sizes = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
    width, height = sizes.get(aspect, sizes["16:9"])

    frames: list[bytes] = []
    for i in range(frame_count):
        shot = (
            f"Cinematic film still {i + 1}/{frame_count} for Art City. "
            f"{prompt[:900]}. Photoreal, dramatic lighting, no text overlay."
        )
        img = _gen_image(shot, aspect if aspect in {"16:9", "9:16", "1:1"} else "16:9")
        if not img:
            break
        try:
            frames.append(_as_png(img.data))
        except Exception:
            frames.append(img.data)
    if not frames:
        return None

    narration = (
        f"Art City Studios. {prompt[:280]}"
        if len(prompt) > 40
        else "Art City Studios presents a cinematic story."
    )
    voice = _gen_voice(narration)
    audio: Optional[bytes] = None
    if voice and voice.data and ("wav" in (voice.content_type or "") or voice.filename.endswith(".wav")):
        audio = voice.data
    if not audio:
        from app.services import media_factory

        _, bed = media_factory.make_video_proxy(prompt, duration_seconds=duration)
        audio = bed.data

    muxed = mux_frames_with_audio(
        frames_png=frames,
        audio_wav=audio,
        duration_seconds=duration,
        filename="openai-video.mp4",
        width=width,
        height=height,
    )
    if not muxed:
        return None
    cost = 0.08 * len(frames) + (0.05 if voice else 0.0) + 0.02
    return ExternalMedia(muxed.data, "video/mp4", "openai-video.mp4", "openai", round(cost, 4))


def _gen_voice(prompt: str) -> Optional[ExternalMedia]:
    settings = get_settings()
    text = prompt[:4000]
    if _has_eleven():
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                headers={
                    "xi-api-key": settings.elevenlabs_api_key,
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                },
                json={"text": text, "model_id": "eleven_multilingual_v2"},
            )
            if resp.status_code < 400 and resp.content:
                return ExternalMedia(resp.content, "audio/mpeg", "eleven-voice.mp3", "elevenlabs", 0.06)
    if _has_openai():
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={"model": "tts-1-hd", "voice": "alloy", "input": text, "response_format": "wav"},
            )
            if resp.status_code < 400 and resp.content:
                return ExternalMedia(resp.content, "audio/wav", "openai-voice.wav", "openai", 0.05)
    return None


def _gen_music(prompt: str, duration_seconds: float) -> Optional[ExternalMedia]:
    if not _has_fal():
        return None
    data = _fal_run(
        "fal-ai/stable-audio",
        {
            "prompt": prompt[:1000],
            "seconds_total": max(5, min(int(duration_seconds), 30)),
        },
        timeout=90.0,
    )
    url = None
    if isinstance(data, dict):
        audio = data.get("audio_file") or data.get("audio") or {}
        if isinstance(audio, dict):
            url = audio.get("url")
        url = url or data.get("url")
    if not url:
        return None
    raw, ctype = _download(url)
    return ExternalMedia(raw, ctype or "audio/wav", "fal-music.wav", "fal", 0.1)


def _gen_sfx(prompt: str) -> Optional[ExternalMedia]:
    return _gen_music(f"sound effect, short: {prompt}", 3.0)


def _fal_run(model_id: str, payload: dict, timeout: float = 60.0) -> Optional[dict]:
    settings = get_settings()
    key = settings.fal_api_key.strip()
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=timeout) as client:
        # Sync endpoint first
        resp = client.post(f"https://fal.run/{model_id}", headers=headers, json=payload)
        if resp.status_code < 400:
            return resp.json()
        # Queue fallback
        q = client.post(f"https://queue.fal.run/{model_id}", headers=headers, json=payload)
        if q.status_code >= 400:
            return None
        body = q.json()
        status_url = body.get("status_url") or body.get("response_url")
        request_id = body.get("request_id")
        if not status_url and request_id:
            status_url = f"https://queue.fal.run/{model_id}/requests/{request_id}/status"
        if not status_url:
            return body if "images" in body or "video" in body else None
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = client.get(status_url, headers=headers)
            if st.status_code >= 400:
                return None
            info = st.json()
            status = str(info.get("status") or "").upper()
            if status in {"COMPLETED", "OK", "SUCCESS"}:
                resp_url = info.get("response_url") or status_url.replace("/status", "")
                out = client.get(resp_url, headers=headers)
                if out.status_code < 400:
                    return out.json()
                return info
            if status in {"FAILED", "ERROR"}:
                return None
            time.sleep(1.5)
    return None


def _first_image_url(data: Optional[dict]) -> Optional[str]:
    if not data:
        return None
    images = data.get("images") or []
    if images and isinstance(images[0], dict):
        return images[0].get("url")
    if isinstance(data.get("image"), dict):
        return data["image"].get("url")
    return data.get("image_url") or data.get("url")


def _download(url: str) -> tuple[bytes, str]:
    with httpx.Client(timeout=90.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content, resp.headers.get("content-type") or "application/octet-stream"
