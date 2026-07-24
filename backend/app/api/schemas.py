from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    budget_limit: Optional[float] = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    budget_limit: Optional[float] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    status: str
    budget_limit: Optional[float]
    created_at: datetime
    updated_at: datetime


class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    identity_rules: Optional[dict[str, Any]] = None
    costume_notes: Optional[str] = None
    voice_profile: Optional[dict[str, Any]] = None
    reference_paths: Optional[list[str]] = None


class CharacterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    description: Optional[str]
    identity_rules: Optional[dict[str, Any]]
    costume_notes: Optional[str]
    voice_profile: Optional[dict[str, Any]]
    reference_paths: Optional[list]
    created_at: datetime


class ScriptCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    language: str = "ku"


class ScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    language: str
    body: str
    created_at: datetime


class GenerationSubmit(BaseModel):
    modality: str = Field(default="image")
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = "artcity-local-v1"
    provider: str = "stub"
    dialect: Optional[str] = None
    run_asr: bool = True
    duration_seconds: float = Field(default=4.0, ge=0.5, le=60.0)
    dialogue_lines: Optional[list[str]] = None
    character_name: Optional[str] = None

    @field_validator("modality", mode="before")
    @classmethod
    def normalize_modality(cls, v: object) -> object:
        if v is None or v == "":
            return "image"
        if isinstance(v, str):
            m = v.strip().lower()
            allowed = {"image", "video", "voice", "audio", "music"}
            if m not in allowed:
                raise ValueError(f"modality must be one of {sorted(allowed)}")
            return m
        return v

    @field_validator("prompt", "character_name", "model", "provider", "dialect", mode="before")
    @classmethod
    def strip_text(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("duration_seconds", mode="before")
    @classmethod
    def coerce_duration(cls, v: object) -> object:
        if v is None or v == "":
            return 4.0
        if isinstance(v, str):
            return float(v)
        return v


class GenerationJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    modality: str
    provider: str
    model: Optional[str]
    model_version: Optional[str] = None
    registered_model_id: Optional[str] = None
    character_key: Optional[str] = None
    prompt: Optional[str]
    status: str
    result_uri: Optional[str]
    error_message: Optional[str]
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    provider_job_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    media_url: Optional[str] = None
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    transcript_job_id: Optional[str] = None
    asr_summary: Optional[str] = None


class BankBuildingGenerate(BaseModel):
    """Optional notes appended to the curated bank-building image prompt."""

    notes: Optional[str] = Field(default=None, max_length=500)
    project_id: Optional[str] = None
    prefer_external: bool = True

    @field_validator("notes", "project_id", mode="before")
    @classmethod
    def strip_optional(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip() or None
        return v


class ReviewCreate(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject|request_changes)$")
    notes: Optional[str] = None
    quality_score: Optional[float] = Field(default=None, ge=0, le=10)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    generation_job_id: str
    decision: str
    notes: Optional[str]
    reviewer_role: str
    quality_score: Optional[float]
    created_at: datetime


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    asset_type: str
    name: str
    storage_path: Optional[str]
    checksum: Optional[str]
    metadata_json: Optional[dict[str, Any]]
    soft_deleted: bool
    created_at: datetime
    media_url: Optional[str] = None


class StudioSummary(BaseModel):
    project_id: str
    totals: dict[str, int]
    approved: int
    pending_review: int
    spent: float


class CinemaPackageCreate(BaseModel):
    campaign: str = Field(..., min_length=1, max_length=180)
    brief: str = Field(..., min_length=1, max_length=4000)
    cta: str = Field(default="Discover more", max_length=80)
    brand: str = Field(default="Art City", max_length=80)
    voiceover_script: Optional[str] = Field(default=None, max_length=4000)
    music_style: str = Field(default="epic")
    duration_seconds: float = Field(default=15.0, ge=5.0, le=60.0)
    initiated_by: str = Field(default="art-city-producer", max_length=120)
    dialect: Optional[str] = Field(default="sorani")
    character_key: Optional[str] = None
    character_name: Optional[str] = None
    channels: Optional[list[str]] = None
    delivery_targets: Optional[list[str]] = None
    variants: Optional[list[str]] = Field(default=None, description="A/B/C advertising variants")

    @field_validator("campaign", "brief", "cta", "brand", "voiceover_script", "initiated_by", mode="before")
    @classmethod
    def strip_cinema_text(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("music_style", mode="before")
    @classmethod
    def normalize_music_style(cls, v: object) -> object:
        allowed = {"epic", "warm", "pulse", "soft"}
        if v is None or v == "":
            return "epic"
        if isinstance(v, str):
            m = v.strip().lower()
            return m if m in allowed else "epic"
        return "epic"

    @field_validator("duration_seconds", mode="before")
    @classmethod
    def coerce_cinema_duration(cls, v: object) -> object:
        if v is None or v == "":
            return 15.0
        if isinstance(v, str):
            return float(v)
        return v

    @field_validator("variants", mode="before")
    @classmethod
    def normalize_variants(cls, v: object) -> object:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            parts = [p.strip().upper() for p in v.replace(",", " ").split() if p.strip()]
            return [p for p in parts if p in {"A", "B", "C"}] or None
        if isinstance(v, list):
            out = [str(p).strip().upper() for p in v if str(p).strip().upper() in {"A", "B", "C"}]
            return out or None
        return None


class CinemaTimelineUpdate(BaseModel):
    music_gain_db: Optional[float] = None
    voice_gain_db: Optional[float] = None
    duck_music_under_vo: Optional[bool] = None


class CinemaDeliverable(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: Optional[str] = None
    type: Optional[str] = None
    modality: str
    job_id: str
    label: Optional[str] = None
    aspect: Optional[str] = None
    aspect_ratio: Optional[str] = None
    media_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_file: Optional[str] = None
    audio_file: Optional[str] = None
    file: Optional[str] = None
    mood: Optional[str] = None


class CinemaPackageOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    package_id: str
    asset_id: str
    product: Optional[str] = "Art City Cinema"
    campaign: str
    brief: str
    cta: str
    brand: str
    brand_colors: Optional[dict[str, str]] = None
    music_style: str
    dialect: Optional[str] = None
    character_key: Optional[str] = None
    channels: Optional[list[str]] = None
    duration_seconds: float
    formats: list[str]
    deliverables: list[CinemaDeliverable]
    total_cost: float
    production_time_seconds: Optional[float] = None
    initiated_by: Optional[str] = None
    usage_rights: Optional[str] = None
    campaign_manifest: Optional[dict[str, Any]] = None
    validation: Optional[dict[str, Any]] = None
    validation_passed: Optional[bool] = None
    manifest_url: Optional[str] = None
    validation_url: Optional[str] = None
    zip_url: Optional[str] = None
    created_at: Optional[str] = None


class PublicationCreate(BaseModel):
    cinema_package_id: str = Field(..., min_length=1)
    channel: str = Field(default="art_city_channel", max_length=80)
    auto_approve_missing: bool = True
    publisher_note: Optional[str] = Field(default=None, max_length=2000)


class ChecklistItem(BaseModel):
    id: str
    label: str
    required: bool = True
    status: str
    detail: Optional[str] = None
    master: Optional[dict[str, Any]] = None


class PublicationOut(BaseModel):
    publication_id: str
    asset_id: str
    project_id: str
    cinema_package_id: Optional[str] = None
    campaign: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    formats: list[str] = []
    checklist: list[ChecklistItem] = []
    masters: list[dict[str, Any]] = []
    progress: int = 0
    manifest_url: Optional[str] = None
    report_url: Optional[str] = None
    publisher_note: Optional[str] = None
    published_at: Optional[str] = None
    created_at: Optional[str] = None


class HealthOut(BaseModel):
    status: str
    database: str
    redis: str
    minio: str
