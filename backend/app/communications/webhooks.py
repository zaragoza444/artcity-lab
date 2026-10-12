"""Signed webhook intake and monotonic message status."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from app.communications.billing import record_provisional
from app.communications.campaigns import pause_campaigns_for_sender, pause_campaigns_for_template
from app.communications.foundation import utcnow
from app.communications.gateway import CanonicalEvent, normalize_meta_webhook, verify_meta_signature
from app.communications.inbox import find_contact_by_phone, is_opt_out, record_opt_out, upsert_conversation
from app.core.config import get_settings
from app.models_comm import (
    CommCampaign,
    CommContact,
    CommMessage,
    CommOrganization,
    CommRecipient,
    CommSender,
    CommTemplate,
    CommWebhookEvent,
)

_RANK = {"accepted": 1, "sent": 2, "delivered": 3, "read": 4}


def advance_status(current: str, incoming: str) -> str:
    if incoming not in _RANK and incoming != "failed":
        return current
    if current in {"delivered", "read"} and incoming in {"accepted", "sent", "failed"}:
        return current
    if current == "read" and incoming == "delivered":
        return current
    if current == "failed" and incoming in {"accepted", "sent"}:
        return current
    if incoming == "failed" and current in {"delivered", "read"}:
        return current
    if incoming in _RANK and current in _RANK and _RANK[incoming] < _RANK[current]:
        return current
    return incoming


def ingest_webhook(db: Session, *, raw_body: bytes, signature: str | None, provider: str = "meta") -> dict:
    settings = get_settings()
    if len(raw_body) > settings.comm_webhook_max_bytes:
        return {"accepted": False, "reason": "payload_too_large"}
    if settings.comm_require_valid_webhook_signature:
        if not verify_meta_signature(settings.meta_app_secret, raw_body, signature):
            return {"accepted": False, "reason": "bad_signature"}
        signature_ok = True
    else:
        signature_ok = verify_meta_signature(settings.meta_app_secret, raw_body, signature)
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {"accepted": False, "reason": "bad_json"}
    if not isinstance(payload, dict):
        return {"accepted": False, "reason": "bad_json"}
    fingerprint = hashlib.sha256(raw_body).hexdigest()
    existing = (
        db.query(CommWebhookEvent)
        .filter(CommWebhookEvent.provider == provider, CommWebhookEvent.dedupe_key == fingerprint)
        .first()
    )
    if existing:
        return {"accepted": True, "duplicate": True, "id": existing.id}
    event = CommWebhookEvent(
        provider=provider,
        dedupe_key=fingerprint,
        event_type="batch",
        raw_payload=payload,
        signature_valid=signature_ok,
        status="received",
    )
    db.add(event)
    db.flush()
    try:
        apply_webhook_payload(db, payload)
        event.status = "processed"
        event.processed_at = utcnow()
    except Exception as exc:  # noqa: BLE001 — dead-letter the event, keep the ack
        event.status = "dead"
        event.error = exc.__class__.__name__
    db.flush()
    return {"accepted": True, "duplicate": False, "id": event.id}


def apply_webhook_payload(db: Session, payload: dict) -> int:
    events = normalize_meta_webhook(payload)
    for item in events:
        _apply_event(db, item)
    return len(events)


def _apply_event(db: Session, event: CanonicalEvent) -> None:
    if event.event_type == "template.status" and event.template_name:
        templates = db.query(CommTemplate).filter(CommTemplate.meta_name == event.template_name).all()
        for template in templates:
            if event.template_language and template.language_code != event.template_language:
                continue
            status = (event.template_status or "").lower()
            if status in {"paused", "disabled", "rejected", "pending"}:
                template.status = "paused" if status in {"paused", "disabled"} else status
                pause_campaigns_for_template(db, template.id, "template_status")
        return
    if event.quality or event.capability:
        senders = db.query(CommSender).all()
        for sender in senders:
            if event.quality and str(event.quality).upper() in {"RED", "LOW", "FLAGGED"}:
                sender.quality = str(event.quality).upper()
                pause_campaigns_for_sender(db, sender.id, "sender_quality")
            if event.capability:
                limit = event.capability.get("max_daily_conversation_per_phone") or event.capability.get("unique_recipient_limit")
                if limit:
                    sender.limits_snapshot = {**(sender.limits_snapshot or {}), "unique_recipient_limit": int(limit)}
        return
    if event.event_type == "message.inbound":
        _inbound(db, event)
        return
    if event.provider_message_id and event.event_type.startswith("message."):
        _status(db, event)


def _status(db: Session, event: CanonicalEvent) -> None:
    message = db.query(CommMessage).filter(CommMessage.provider_message_id == event.provider_message_id).first()
    if message is None:
        return
    incoming = event.event_type.split(".", 1)[1]
    if incoming not in {"sent", "delivered", "read", "failed", "accepted"}:
        return
    message.status = advance_status(message.status, incoming)
    moment = event.timestamp or utcnow()
    if message.status == "sent" and message.accepted_at is None:
        message.accepted_at = moment
    if message.status == "delivered":
        message.delivered_at = message.delivered_at or moment
    if message.status == "read":
        message.read_at = message.read_at or moment
        message.delivered_at = message.delivered_at or moment
    if incoming == "failed" and message.status == "failed":
        message.failed_at = moment
        message.error_code = event.error_code
    message.pricing_json = event.pricing or message.pricing_json
    message.updated_at = utcnow()
    recipient = db.get(CommRecipient, message.campaign_recipient_id) if message.campaign_recipient_id else None
    if recipient is not None:
        recipient.status = advance_status(recipient.status, message.status)
        recipient.updated_at = utcnow()
    if message.status in {"delivered", "read"}:
        contact = db.get(CommContact, message.contact_id)
        campaign_id = None
        category = "marketing"
        if recipient is not None:
            campaign = db.get(CommCampaign, recipient.campaign_id)
            if campaign is not None:
                campaign_id = campaign.id
                category = campaign.category
        billable = True
        if event.pricing and event.pricing.get("billable") is False:
            billable = False
        if billable:
            record_provisional(
                db,
                message=message,
                campaign_id=campaign_id,
                market=(contact.country_iso if contact else None) or "IQ",
                category=category,
                sender_id=message.sender_id,
            )


def _inbound(db: Session, event: CanonicalEvent) -> None:
    org = db.query(CommOrganization).order_by(CommOrganization.created_at.asc()).first()
    sender = db.query(CommSender).order_by(CommSender.created_at.asc()).first()
    if org is None or sender is None or not event.phone:
        return
    contact = find_contact_by_phone(db, org.id, event.phone)
    if contact is None:
        from app.communications.phones import normalize_phone

        e164, iso, error = normalize_phone("+" + event.phone if not event.phone.startswith("+") else event.phone)
        if error or not e164:
            return
        contact = CommContact(organization_id=org.id, phone_e164=e164, country_iso=iso, display_name="", tags=[], parse_confidence="1.0")
        db.add(contact)
        db.flush()
    when = event.timestamp or utcnow()
    db.add(
        CommMessage(
            sender_id=sender.id,
            contact_id=contact.id,
            provider_message_id=event.provider_message_id,
            direction="inbound",
            kind="session",
            status="received",
            body_text=event.text,
            accepted_at=when,
        )
    )
    upsert_conversation(db, sender, contact, when)
    if is_opt_out(event.text):
        record_opt_out(db, contact, actor_id=None, source="inbound_keyword", evidence=event.text)
