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
    QUEUED = "queued"
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


class DatasetStatus(str, Enum):
    RAW = "raw"
    INGESTING = "ingesting"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    VERIFIED = "verified"
    TRAINING_READY = "training_ready"
    EVALUATION_ONLY = "evaluation_only"
    REFERENCE_ONLY = "reference_only"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


class RightsStatus(str, Enum):
    APPROVED_FOR_TRAINING = "approved_for_training"
    APPROVED_FOR_REFERENCE = "approved_for_reference"
    APPROVED_FOR_COMMERCIAL_USE = "approved_for_commercial_use"
    APPROVED_FOR_VOICE_CLONING = "approved_for_voice_cloning"
    RESTRICTED = "restricted"
    EXPIRED = "expired"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"


class ModelStatus(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    TRAINING = "training"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


class TrainingJobStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    QUEUED = "queued"
    RUNNING = "running"
    EVALUATING = "evaluating"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AnnotationStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICT = "conflict"


class EvaluationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    NEEDS_HUMAN = "needs_human"
    APPROVED = "approved"
    REJECTED = "rejected"


# Roles that may perform privileged AI Core actions
PRIVILEGED_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.ADMINISTRATOR,
    UserRole.PRODUCER,
}

DATASET_UPLOAD_ROLES = PRIVILEGED_ROLES | {UserRole.AI_OPERATOR, UserRole.PROJECT_MANAGER}
RIGHTS_APPROVE_ROLES = PRIVILEGED_ROLES
TRAINING_ROLES = PRIVILEGED_ROLES | {UserRole.AI_OPERATOR}
MODEL_PROMOTE_ROLES = PRIVILEGED_ROLES
ROUTE_CHANGE_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMINISTRATOR}
