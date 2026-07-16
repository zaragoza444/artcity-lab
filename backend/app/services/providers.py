from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.core.enums import GenerationStatus


@dataclass
class ProviderResult:
    provider_job_id: str
    status: GenerationStatus
    result_uri: Optional[str] = None
    error_message: Optional[str] = None
    actual_cost: Optional[float] = None


class ProviderAdapter(ABC):
    name: str

    @abstractmethod
    def submit(self, prompt: str, modality: str, model: Optional[str] = None) -> ProviderResult:
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
    """Local stub so workflows wire without real API keys."""

    name = "stub"
    _jobs: dict[str, ProviderResult] = {}

    def submit(self, prompt: str, modality: str, model: Optional[str] = None) -> ProviderResult:
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
            ProviderResult(provider_job_id=provider_job_id, status=GenerationStatus.FAILED, error_message="not found"),
        )

    def result(self, provider_job_id: str) -> ProviderResult:
        return self.status(provider_job_id)

    def cancel(self, provider_job_id: str) -> ProviderResult:
        result = ProviderResult(
            provider_job_id=provider_job_id,
            status=GenerationStatus.CANCELLED,
        )
        self._jobs[provider_job_id] = result
        return result

    def estimate_cost(self, prompt: str, modality: str) -> float:
        base = {"image": 0.02, "video": 0.25, "voice": 0.05, "audio": 0.03, "music": 0.08}
        return base.get(modality, 0.01) + min(len(prompt) / 10000, 0.05)


def get_provider(name: str = "stub") -> ProviderAdapter:
    if name == "stub":
        return StubProvider()
    # Future: fal, kling, runway, etc. — all behind the same interface.
    return StubProvider()
