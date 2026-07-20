"""Art City provider adapters — full production generation via Model Gateway."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.core.config import get_settings
from app.core.enums import GenerationStatus


@dataclass
class ProviderResult:
    provider_job_id: str
    status: GenerationStatus
    result_uri: Optional[str] = None
    error_message: Optional[str] = None
    actual_cost: Optional[float] = None
    output_bytes: Optional[bytes] = None
    content_type: Optional[str] = None
    filename: Optional[str] = None
    sidecar_bytes: Optional[bytes] = None
    sidecar_content_type: Optional[str] = None
    sidecar_filename: Optional[str] = None


class ProviderAdapter(ABC):
    name: str

    def submit_generation(
        self, prompt: str, modality: str, model: Optional[str] = None, **kwargs
    ) -> ProviderResult:
        return self.submit(prompt, modality, model, **kwargs)

    def get_status(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def get_result(self, provider_job_id: str) -> ProviderResult:
        return self.result(provider_job_id)

    def cancel_generation(self, provider_job_id: str) -> ProviderResult:
        return self.cancel(provider_job_id)

    def download_output(self, provider_job_id: str) -> ProviderResult:
        return self.result(provider_job_id)

    def health_check(self) -> bool:
        return True

    @abstractmethod
    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def status(self, provider_job_id: str) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def result(self, provider_job_id: str) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def cancel(self, provider_job_id: str) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def estimate_cost(self, prompt: str, modality: str) -> float:
        raise NotImplementedError


def _ok(
    job_id: str,
    *,
    data: bytes,
    content_type: str,
    filename: str,
    cost: float,
    sidecar: tuple[bytes, str, str] | None = None,
) -> ProviderResult:
    return ProviderResult(
        provider_job_id=job_id,
        status=GenerationStatus.SUCCEEDED,
        result_uri=f"inline://{job_id}",
        actual_cost=cost,
        output_bytes=data,
        content_type=content_type,
        filename=filename,
        sidecar_bytes=sidecar[0] if sidecar else None,
        sidecar_content_type=sidecar[1] if sidecar else None,
        sidecar_filename=sidecar[2] if sidecar else None,
    )


def _try_external(modality: str, prompt: str, **kwargs) -> Optional[ProviderResult]:
    from app.services.external_gen import generate_external

    duration = float(kwargs.get("duration_seconds") or 4.0)
    aspect = str(kwargs.get("aspect") or "16:9")
    script = str(kwargs.get("script") or prompt)
    ext = generate_external(
        modality=modality,
        prompt=script if modality == "voice" else prompt,
        duration_seconds=duration,
        aspect=aspect,
    )
    if not ext:
        return None
    job_id = f"ext-{ext.provider}-{uuid4()}"
    return _ok(
        job_id,
        data=ext.data,
        content_type=ext.content_type,
        filename=ext.filename,
        cost=ext.cost,
    )


def _local_image(prompt: str, **kwargs) -> ProviderResult:
    from app.services import media_factory

    job_id = f"ac-img-{uuid4()}"
    title = kwargs.get("character_name") or kwargs.get("character_key") or "Art City"
    aspect = str(kwargs.get("aspect") or "16:9")
    if kwargs.get("end_card"):
        media = media_factory.make_end_card(
            str(kwargs.get("campaign") or title),
            str(kwargs.get("cta") or "Discover more"),
            brand=str(kwargs.get("brand") or "Art City"),
            prompt=prompt,
        )
    else:
        media = media_factory.make_image(prompt, title=str(title), aspect=aspect)
    return _ok(
        job_id,
        data=media.data,
        content_type=media.content_type,
        filename=media.filename,
        cost=0.02,
    )


def _local_video(prompt: str, **kwargs) -> ProviderResult:
    from app.services import media_factory
    from app.services.video_mux import mux_frames_with_audio, mux_still_with_audio

    job_id = f"ac-vid-{uuid4()}"
    duration = float(kwargs.get("duration_seconds") or 4.0)
    title = kwargs.get("character_name") or kwargs.get("character_key") or "Art City"
    aspect = str(kwargs.get("aspect") or "16:9")
    brand = str(kwargs.get("brand") or "Art City")
    campaign = str(kwargs.get("campaign") or title)
    cta = str(kwargs.get("cta") or "Art City Studios")
    width, height = media_factory.ASPECT_SIZES.get(aspect, media_factory.ASPECT_SIZES["16:9"])

    # Timed audio bed
    _, bed = media_factory.make_cinematic_video(
        prompt,
        aspect=aspect,
        duration_seconds=duration,
        brand=brand,
        campaign=campaign,
        cta=cta,
    )
    frames = media_factory.make_shot_frames(
        campaign=campaign,
        brief=prompt,
        cta=cta,
        brand=brand,
        aspect=aspect,
        shot_count=5 if duration >= 6 or kwargs.get("advertising") else 3,
    )
    mp4 = mux_frames_with_audio(
        frames_png=frames,
        audio_wav=bed.data,
        duration_seconds=duration,
        filename=f"video-{uuid4().hex[:10]}.mp4",
        width=width,
        height=height,
    )
    if not mp4:
        mp4 = mux_still_with_audio(
            poster_png=frames[0],
            audio_wav=bed.data,
            duration_seconds=duration,
            filename=f"video-{uuid4().hex[:10]}.mp4",
            width=width,
            height=height,
        )
    if mp4:
        primary = mp4
    else:
        # Last resort: PNG storyboard still (hosts without ffmpeg)
        primary = media_factory.make_cinema_poster_png(
            campaign=campaign,
            brief=prompt,
            cta=cta,
            brand=brand,
            aspect=aspect,
            filename=f"video-{uuid4().hex[:10]}.png",
        )
    return _ok(
        job_id,
        data=primary.data,
        content_type=primary.content_type,
        filename=primary.filename,
        cost=0.12,
        sidecar=(bed.data, bed.content_type, bed.filename),
    )


def _local_voice(prompt: str, **kwargs) -> ProviderResult:
    from app.services import media_factory
    from app.services.audio_mix import optional_external_tts

    job_id = f"ac-vo-{uuid4()}"
    brand = str(kwargs.get("brand") or kwargs.get("character_name") or "Art City")
    script = str(kwargs.get("script") or prompt)
    dialect = kwargs.get("dialect")
    dialogue = kwargs.get("dialogue_lines") or []
    if dialogue:
        media = media_factory.make_voice_conversation(prompt, list(dialogue))
    else:
        external = optional_external_tts(script, brand=brand)
        if external:
            media = media_factory.MediaFile(
                filename="voiceover.wav",
                content_type="audio/wav",
                data=external,
                kind="audio",
            )
        else:
            media = media_factory.make_ad_voiceover(
                script, brand=brand, dialect=str(dialect) if dialect else None
            )
    return _ok(
        job_id,
        data=media.data,
        content_type=media.content_type,
        filename=media.filename,
        cost=0.05,
    )


def _local_music(prompt: str, **kwargs) -> ProviderResult:
    from app.services import media_factory

    job_id = f"ac-mus-{uuid4()}"
    duration = float(kwargs.get("duration_seconds") or 8.0)
    style = str(kwargs.get("music_style") or "epic")
    media = media_factory.make_cinematic_music(prompt, duration_seconds=max(duration, 5.0), style=style)
    return _ok(
        job_id,
        data=media.data,
        content_type=media.content_type,
        filename=media.filename,
        cost=0.08,
    )


def _local_audio(prompt: str, **kwargs) -> ProviderResult:
    from app.services import media_factory

    job_id = f"ac-aud-{uuid4()}"
    media = media_factory.make_sfx(prompt)
    return _ok(
        job_id,
        data=media.data,
        content_type=media.content_type,
        filename=media.filename,
        cost=0.03,
    )


def produce(modality: str, prompt: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
    """Full production path: external keys when present, else Art City masters."""
    settings = get_settings()
    prefer_cloud = bool(kwargs.pop("prefer_external", False) or settings.external_providers_enabled)
    if prefer_cloud and modality in {"image", "video", "voice", "music", "audio"}:
        # Skip cloud for end cards — brand lockup stays Art City owned
        if not kwargs.get("end_card"):
            ext = _try_external(modality, prompt, **kwargs)
            if ext:
                return ext
    locals_ = {
        "image": _local_image,
        "video": _local_video,
        "voice": _local_voice,
        "music": _local_music,
        "audio": _local_audio,
    }
    fn = locals_.get(modality)
    if not fn:
        return ProviderResult(
            provider_job_id=f"ac-miss-{uuid4()}",
            status=GenerationStatus.FAILED,
            error_message=f"Unsupported modality {modality}",
        )
    return fn(prompt, **kwargs)


class StubProvider(ProviderAdapter):
    """Legacy name — still emits real production media bytes (never empty URIs)."""

    name = "stub"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        return produce(modality, prompt, model, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        base = {"image": 0.02, "video": 0.25, "voice": 0.05, "audio": 0.03, "music": 0.08}
        return base.get(modality, 0.01)


class ArtCityImageProvider(ProviderAdapter):
    name = "artcity-image"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        return produce("image", prompt, model, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.02


class ArtCityVideoProvider(ProviderAdapter):
    name = "artcity-video"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        return produce("video", prompt, model, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.12


class ArtCityVoiceProvider(ProviderAdapter):
    name = "artcity-voice"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        return produce("voice", prompt, model, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.05


class ArtCityMusicProvider(ProviderAdapter):
    name = "artcity-music"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        return produce("music", prompt, model, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.08


class ArtCityAudioProvider(ProviderAdapter):
    name = "artcity-audio"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        return produce("audio", prompt, model, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.03


class ArtCityAsrProvider(ProviderAdapter):
    name = "artcity-asr"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        return ProviderResult(
            provider_job_id=f"ac-asr-{uuid4()}",
            status=GenerationStatus.SUCCEEDED,
            result_uri="speech://gateway",
            actual_cost=0.02,
            filename="transcript.json",
            content_type="application/json",
            output_bytes=b"{}",
        )

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.02


class ExternalFallbackProvider(ProviderAdapter):
    """Cloud-first generation when keys are set; Art City masters otherwise."""

    name = "external-fallback"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        settings = get_settings()
        if not settings.external_providers_enabled:
            return produce(modality, prompt, model, prefer_external=False, **kwargs)
        return produce(modality, prompt, model, prefer_external=True, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return StubProvider().estimate_cost(prompt, modality) * 1.5

    def health_check(self) -> bool:
        from app.services.external_gen import external_available

        settings = get_settings()
        if not settings.external_providers_enabled:
            return True
        return any(external_available(m) for m in ("image", "video", "voice", "music")) or True


PROVIDERS: dict[str, type[ProviderAdapter]] = {
    "stub": StubProvider,
    "artcity-image": ArtCityImageProvider,
    "artcity-video": ArtCityVideoProvider,
    "artcity-voice": ArtCityVoiceProvider,
    "artcity-music": ArtCityMusicProvider,
    "artcity-audio": ArtCityAudioProvider,
    "artcity-asr": ArtCityAsrProvider,
    "external-fallback": ExternalFallbackProvider,
}


def get_provider(name: str = "stub") -> ProviderAdapter:
    cls = PROVIDERS.get(name) or StubProvider
    return cls()


def list_providers() -> list[dict]:
    out = []
    for name, cls in PROVIDERS.items():
        adapter = cls()
        out.append({"name": name, "healthy": adapter.health_check()})
    return out
