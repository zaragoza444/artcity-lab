"""AC Communications persistence. One Art City deployment, division-scoped."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid4())


class CommOrganization(Base):
    __tablename__ = "comm_organizations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_portfolio_id: Mapped[Optional[str]] = mapped_column(String(64))
    billing_currency: Mapped[str] = mapped_column(String(8), default="USD")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Baghdad")
    status: Mapped[str] = mapped_column(String(32), default="active")
    settings_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommBusinessUnit(Base):
    __tablename__ = "comm_business_units"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cost_center: Mapped[Optional[str]] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommMembership(Base):
    __tablename__ = "comm_memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_comm_membership_user"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_organizations.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(128))
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommSender(Base):
    __tablename__ = "comm_senders"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_organizations.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), default="direct_meta")
    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number_id: Mapped[Optional[str]] = mapped_column(String(64))
    waba_id: Mapped[Optional[str]] = mapped_column(String(64))
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    quality: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    limits_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_error: Mapped[Optional[str]] = mapped_column(String(255))
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommContact(Base):
    __tablename__ = "comm_contacts"
    __table_args__ = (
        UniqueConstraint("organization_id", "phone_e164", name="uq_comm_contact_phone"),
        Index("ix_comm_contact_country", "country_iso"),
        Index("ix_comm_contact_city", "city"),
        Index("ix_comm_contact_locale", "preferred_locale"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_organizations.id"), nullable=False)
    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(120))
    country_iso: Mapped[Optional[str]] = mapped_column(String(2))
    preferred_locale: Mapped[Optional[str]] = mapped_column(String(16))
    source: Mapped[Optional[str]] = mapped_column(String(120))
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    parse_confidence: Mapped[Optional[str]] = mapped_column(String(16))
    merged_into_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_contacts.id"))
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommConsent(Base):
    __tablename__ = "comm_consents"
    __table_args__ = (
        Index("ix_comm_consent_lookup", "contact_id", "business_unit_id", "channel", "purpose"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    contact_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_contacts.id"), nullable=False)
    business_unit_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_business_units.id"))
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), default="whatsapp")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    obtained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source: Mapped[Optional[str]] = mapped_column(String(255))
    notice_version: Mapped[Optional[str]] = mapped_column(String(64))
    proof_uri: Mapped[Optional[str]] = mapped_column(String(512))
    evidence_note: Mapped[Optional[str]] = mapped_column(Text)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommSuppression(Base):
    __tablename__ = "comm_suppressions"
    __table_args__ = (Index("ix_comm_suppression_contact", "contact_id"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    contact_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_contacts.id"), nullable=False)
    scope: Mapped[str] = mapped_column(String(64), default="global")
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class CommImportJob(Base):
    __tablename__ = "comm_import_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_organizations.id"), nullable=False)
    business_unit_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_business_units.id"))
    file_uri: Mapped[Optional[str]] = mapped_column(String(1024))
    imported_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    count_total: Mapped[int] = mapped_column(Integer, default=0)
    inserted: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    rejected: Mapped[int] = mapped_column(Integer, default=0)
    with_valid_marketing_opt_in: Mapped[int] = mapped_column(Integer, default=0)
    requires_consent: Mapped[int] = mapped_column(Integer, default=0)
    rejections_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    errors_uri: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommSegment(Base):
    __tablename__ = "comm_segments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    business_unit_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_business_units.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filter_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    frozen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommTemplate(Base):
    __tablename__ = "comm_templates"
    __table_args__ = (
        UniqueConstraint("waba_id", "meta_name", "language_code", name="uq_comm_template_name_lang"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_organizations.id"), nullable=False)
    sender_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_senders.id"))
    waba_id: Mapped[str] = mapped_column(String(64), nullable=False)
    meta_name: Mapped[str] = mapped_column(String(255), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    components_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommAudienceSnapshot(Base):
    __tablename__ = "comm_audience_snapshots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    frozen_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommCampaign(Base):
    __tablename__ = "comm_campaigns"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft','submitted','approved','rejected','scheduled','running','paused','completed','cancelled')",
            name="ck_comm_campaign_state",
        ),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    business_unit_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_business_units.id"), nullable=False)
    sender_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_senders.id"), nullable=False)
    template_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_templates.id"), nullable=False)
    segment_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_segments.id"))
    audience_snapshot_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_audience_snapshots.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="marketing")
    state: Mapped[str] = mapped_column(String(32), default="draft")
    schedule_utc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    schedule_timezone: Mapped[str] = mapped_column(String(64), default="Asia/Baghdad")
    quiet_hours_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    allow_quiet_hours: Mapped[bool] = mapped_column(Boolean, default=False)
    parameter_template: Mapped[dict] = mapped_column(JSONB, default=dict)
    budget_micros: Mapped[int] = mapped_column(BigInteger, default=0)
    reserved_micros: Mapped[int] = mapped_column(BigInteger, default=0)
    consumed_micros: Mapped[int] = mapped_column(BigInteger, default=0)
    buffer_percent: Mapped[int] = mapped_column(Integer, default=0)
    quote_micros: Mapped[int] = mapped_column(BigInteger, default=0)
    snapshot_checksum: Mapped[Optional[str]] = mapped_column(String(128))
    submitted_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    approved_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pause_reason: Mapped[Optional[str]] = mapped_column(String(255))
    test_batch_size: Mapped[int] = mapped_column(Integer, default=5)
    production_released: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommRecipient(Base):
    __tablename__ = "comm_recipients"
    __table_args__ = (
        UniqueConstraint("campaign_id", "contact_id", name="uq_comm_recipient"),
        Index("ix_comm_recipient_status", "campaign_id", "status"),
        Index("ix_comm_recipient_contact", "contact_id", "campaign_id"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_campaigns.id"), nullable=False)
    contact_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_contacts.id"), nullable=False)
    rendered_parameters_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="selected")
    exclusion_reason: Mapped[Optional[str]] = mapped_column(String(64))
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommMessage(Base):
    __tablename__ = "comm_messages"
    __table_args__ = (
        Index("ix_comm_message_contact", "sender_id", "contact_id"),
        Index("ix_comm_message_status", "status"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    campaign_recipient_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_recipients.id"))
    sender_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_senders.id"), nullable=False)
    contact_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_contacts.id"), nullable=False)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[Optional[str]] = mapped_column(String(64))
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    pricing_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    provider_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommSendAttempt(Base):
    __tablename__ = "comm_send_attempts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    message_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_messages.id"), nullable=False)
    request_key: Mapped[str] = mapped_column(String(128), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    provider_error_code: Mapped[Optional[str]] = mapped_column(String(64))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    timeout_unknown: Mapped[bool] = mapped_column(Boolean, default=False)


class CommWebhookEvent(Base):
    __tablename__ = "comm_webhook_events"
    __table_args__ = (UniqueConstraint("provider", "dedupe_key", name="uq_comm_webhook_dedupe"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), default="batch")
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="received")


class CommConversation(Base):
    __tablename__ = "comm_conversations"
    __table_args__ = (UniqueConstraint("sender_id", "contact_id", name="uq_comm_conversation"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    sender_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_senders.id"), nullable=False)
    contact_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_contacts.id"), nullable=False)
    last_user_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    service_window_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    assigned_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    state: Mapped[str] = mapped_column(String(32), default="open")
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommRateCard(Base):
    __tablename__ = "comm_rate_cards"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    market: Mapped[str] = mapped_column(String(8), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    unit_rate_decimal: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rate_source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_version: Mapped[str] = mapped_column(String(64), nullable=False)
    rules_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommCostLedger(Base):
    __tablename__ = "comm_cost_ledger"
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('provisional','invoice_adjustment','reversal')",
            name="ck_comm_ledger_entry",
        ),
        Index("ix_comm_ledger_campaign", "campaign_id"),
        Index("ix_comm_ledger_invoice", "external_invoice_ref"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    message_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_messages.id"))
    campaign_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_campaigns.id"))
    amount_micros: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="posted")
    rate_card_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("comm_rate_cards.id"))
    external_invoice_ref: Mapped[Optional[str]] = mapped_column(String(128))
    note: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommAuditLog(Base):
    __tablename__ = "comm_audit_logs"
    __table_args__ = (Index("ix_comm_audit_created", "created_at"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    actor_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_id: Mapped[Optional[str]] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommOutbox(Base):
    __tablename__ = "comm_outbox"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_comm_outbox_key"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    job_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
