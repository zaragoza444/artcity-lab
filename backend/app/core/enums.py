from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMINISTRATOR = "administrator"
    PRODUCER = "producer"
    PROJECT_MANAGER = "project_manager"
    WRITER = "writer"
    CREATIVE_DIRECTOR = "creative_director"
    AI_OPERATOR = "ai_operator"
    ANIMATOR = "animator"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssetType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    VOICE = "voice"
    AUDIO = "audio"
    MUSIC = "music"
    SUBTITLE = "subtitle"
    SCRIPT = "script"
    OTHER = "other"


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class MediaModality(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    VOICE = "voice"
    AUDIO = "audio"
    MUSIC = "music"


class PublicationStatus(str, Enum):
    DRAFT = "draft"
    PACKAGING = "packaging"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"
