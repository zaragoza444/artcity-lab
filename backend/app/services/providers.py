"""Art City provider adapters — Model Gateway standard interface."""

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


class StubProvider(ProviderAdapter):
    """Local stub for workflows without GPU keys."""

    name = "stub"
    _jobs: dict[str, ProviderResult] = {}

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        job_id = f"stub-{uuid4()}"
        result = ProviderResult(
            provider_job_id=job_id,
            status=GenerationStatus.SUCCEEDED,
            result_uri=f"stub://{modality}/{job_id}",
            actual_cost=self.estimate_cost(prompt, modality),
        )
        self._jobs[job_id] = result
        return result

    def status(self, provider_job_id: str) -> ProviderResult:
        return self._jobs.get(
            provider_job_id,
            ProviderResult(
                provider_job_id=provider_job_id,
                status=GenerationStatus.FAILED,
                error_message="not found",
            ),
        )

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        result = ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)
        self._jobs[provider_job_id] = result
        return result

    def estimate_cost(self, prompt: str, modality: str) -> float:
        base = {"image": 0.02, "video": 0.25, "voice": 0.05, "audio": 0.03, "music": 0.08}
        return base.get(modality, 0.01) + min(len(prompt) / 10000, 0.05)


class ArtCityImageProvider(ProviderAdapter):
    """Art City-controlled image worker (local media factory until GPU workers attach)."""

    name = "artcity-image"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        from app.services import media_factory

        job_id = f"ac-img-{uuid4()}"
        title = kwargs.get("character_name") or kwargs.get("character_key") or "Art City"
        if kwargs.get("end_card"):
            media = media_factory.make_end_card(
                str(kwargs.get("campaign") or title),
                str(kwargs.get("cta") or "Discover more"),
                brand=str(kwargs.get("brand") or "Art City"),
                prompt=prompt,
            )
        else:
            media = media_factory.make_image(prompt, title=str(title))
        return ProviderResult(
            provider_job_id=job_id,
            status=GenerationStatus.SUCCEEDED,
            result_uri=f"inline://{job_id}",
            actual_cost=self.estimate_cost(prompt, modality),
            output_bytes=media.data,
            content_type=media.content_type,
            filename=media.filename,
        )

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.015

    def health_check(self) -> bool:
        return True


class ArtCityVideoProvider(ProviderAdapter):
    name = "artcity-video"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        from app.services import media_factory

        job_id = f"ac-vid-{uuid4()}"
        duration = float(kwargs.get("duration_seconds") or 4.0)
        title = kwargs.get("character_name") or kwargs.get("character_key") or "Art City"
        aspect = str(kwargs.get("aspect") or "16:9")
        brand = str(kwargs.get("brand") or "Art City")
        campaign = str(kwargs.get("campaign") or title)
        cta = str(kwargs.get("cta") or "Art City Studios")
        if duration >= 6 or kwargs.get("advertising"):
            visual, bed = media_factory.make_cinematic_video(
                prompt,
                aspect=aspect,
                duration_seconds=duration,
                brand=brand,
                campaign=campaign,
                cta=cta,
            )
        else:
            visual, bed = media_factory.make_video_proxy(prompt, duration_seconds=duration)
        return ProviderResult(
            provider_job_id=job_id,
            status=GenerationStatus.SUCCEEDED,
            result_uri=f"inline://{job_id}",
            actual_cost=self.estimate_cost(prompt, modality),
            output_bytes=visual.data,
            content_type=visual.content_type,
            filename=visual.filename,
            sidecar_bytes=bed.data,
            sidecar_content_type=bed.content_type,
            sidecar_filename=bed.filename,
        )

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
        from app.services import media_factory

        job_id = f"ac-vo-{uuid4()}"
        brand = str(kwargs.get("brand") or kwargs.get("character_name") or "Art City")
        script = str(kwargs.get("script") or prompt)
        dialogue = kwargs.get("dialogue_lines") or []
        if dialogue:
            media = media_factory.make_voice_conversation(prompt, list(dialogue))
        else:
            media = media_factory.make_ad_voiceover(script, brand=brand)
        return ProviderResult(
            provider_job_id=job_id,
            status=GenerationStatus.SUCCEEDED,
            result_uri=f"inline://{job_id}",
            actual_cost=self.estimate_cost(prompt, modality),
            output_bytes=media.data,
            content_type=media.content_type,
            filename=media.filename,
        )

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
        from app.services import media_factory

        job_id = f"ac-mus-{uuid4()}"
        duration = float(kwargs.get("duration_seconds") or 8.0)
        style = str(kwargs.get("music_style") or "epic")
        media = media_factory.make_cinematic_music(prompt, duration_seconds=max(duration, 8.0), style=style)
        return ProviderResult(
            provider_job_id=job_id,
            status=GenerationStatus.SUCCEEDED,
            result_uri=f"inline://{job_id}",
            actual_cost=self.estimate_cost(prompt, modality),
            output_bytes=media.data,
            content_type=media.content_type,
            filename=media.filename,
        )

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
        from app.services import media_factory

        job_id = f"ac-aud-{uuid4()}"
        media = media_factory.make_sfx(prompt)
        return ProviderResult(
            provider_job_id=job_id,
            status=GenerationStatus.SUCCEEDED,
            result_uri=f"inline://{job_id}",
            actual_cost=self.estimate_cost(prompt, modality),
            output_bytes=media.data,
            content_type=media.content_type,
            filename=media.filename,
        )

    def status(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.SUCCEEDED)

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.CANCELLED)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return 0.03


class ArtCityAsrProvider(ProviderAdapter):
    """Speech recognition provider registered for Model Gateway health/routing."""

    name = "artcity-asr"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        from app.core.config import get_settings

        settings = get_settings()
        return ProviderResult(
            provider_job_id=f"ac-asr-{uuid4()}",
            status=GenerationStatus.SUCCEEDED,
            result_uri="speech://gateway",
            actual_cost=self.estimate_cost(prompt, modality),
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

    def health_check(self) -> bool:
        return True


class ExternalFallbackProvider(ProviderAdapter):
    """Approved external fallback — disabled when EXTERNAL_PROVIDERS_ENABLED=false."""

    name = "external-fallback"

    def submit(self, prompt: str, modality: str, model: Optional[str] = None, **kwargs) -> ProviderResult:
        settings = get_settings()
        if not settings.external_providers_enabled:
            return ProviderResult(
                provider_job_id=f"ext-off-{uuid4()}",
                status=GenerationStatus.FAILED,
                error_message="External providers disabled",
            )
        # Fall back to stub media until real keys are wired
        return StubProvider().submit(prompt, modality, model, **kwargs)

    def status(self, provider_job_id: str) -> ProviderResult:
        return StubProvider().status(provider_job_id)

    def result(self, provider_job_id: str) -> ProviderResult:
        return StubProvider().result(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        return StubProvider().cancel(provider_job_id)

    def estimate_cost(self, prompt: str, modality: str) -> float:
        return StubProvider().estimate_cost(prompt, modality) * 1.5

    def health_check(self) -> bool:
        return get_settings().external_providers_enabled


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
