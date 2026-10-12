"""Rate-limited dispatch. An outbox row is written before any provider call."""

from __future__ import annotations

import random
from datetime import timedelta

from sqlalchemy.orm import Session

from app.communications.billing import rate_for
from app.communications.campaigns import in_quiet_hours, meta_components, pause_campaigns_for_sender
from app.communications.crm import active_suppression, exclusion_reason
from app.communications.foundation import utcnow
from app.communications.gateway import MessagingGateway, ProviderError, UnknownOutcome
from app.communications.money import to_micros
from app.core.config import get_settings
from app.models_comm import (
    CommBusinessUnit,
    CommCampaign,
    CommContact,
    CommMessage,
    CommOutbox,
    CommRecipient,
    CommSendAttempt,
    CommSender,
    CommTemplate,
)

_TERMINAL_RECIPIENT = {"accepted", "sent", "delivered", "read", "failed", "send_failed", "excluded", "cancelled", "quarantined"}


def _requeue(job: CommOutbox, delay_seconds: int, reason: str) -> None:
    job.status = "pending"
    job.next_attempt_at = utcnow() + timedelta(seconds=delay_seconds)
    job.last_error = reason[:255]
    job.updated_at = utcnow()


def _claim(db: Session, job: CommOutbox) -> bool:
    updated = (
        db.query(CommOutbox)
        .filter(CommOutbox.id == job.id, CommOutbox.status == "pending")
        .update({"status": "processing"}, synchronize_session=False)
    )
    db.flush()
    if updated != 1:
        return False
    db.refresh(job)
    return True


def _rolling_unique(db: Session, organization_id: str) -> int:
    since = utcnow() - timedelta(hours=24)
    rows = (
        db.query(CommMessage.contact_id)
        .join(CommSender, CommSender.id == CommMessage.sender_id)
        .filter(
            CommSender.organization_id == organization_id,
            CommMessage.direction == "outbound",
            CommMessage.accepted_at.is_not(None),
            CommMessage.accepted_at >= since,
        )
        .distinct()
        .all()
    )
    return len(rows)


def _reserved_today(db: Session) -> int:
    since = utcnow() - timedelta(hours=24)
    rows = (
        db.query(CommMessage)
        .filter(CommMessage.direction == "outbound", CommMessage.accepted_at.is_not(None), CommMessage.accepted_at >= since)
        .all()
    )
    total = 0
    for row in rows:
        total += int((row.provider_metadata or {}).get("reserved_micros") or 0)
    return total


def _pair_blocked(db: Session, sender_id: str, contact_id: str) -> bool:
    window = get_settings().comm_pair_min_interval_seconds
    if window <= 0:
        return False
    since = utcnow() - timedelta(seconds=window)
    row = (
        db.query(CommSendAttempt)
        .join(CommMessage, CommMessage.id == CommSendAttempt.message_id)
        .filter(CommMessage.sender_id == sender_id, CommMessage.contact_id == contact_id, CommSendAttempt.start_at >= since)
        .first()
    )
    return row is not None


def _mps_blocked(db: Session) -> bool:
    limit = get_settings().comm_send_worker_initial_mps
    if limit <= 0:
        return False
    since = utcnow() - timedelta(seconds=1)
    count = db.query(CommSendAttempt).filter(CommSendAttempt.start_at >= since).count()
    return count >= limit


def dispatch_recipient(db: Session, recipient_id: str, gateway: MessagingGateway) -> str:
    recipient = db.get(CommRecipient, recipient_id)
    if recipient is None:
        return "missing"
    if recipient.status in _TERMINAL_RECIPIENT:
        return "skipped"
    campaign = db.get(CommCampaign, recipient.campaign_id)
    contact = db.get(CommContact, recipient.contact_id)
    template = db.get(CommTemplate, campaign.template_id) if campaign else None
    sender = db.get(CommSender, campaign.sender_id) if campaign else None
    unit = db.get(CommBusinessUnit, campaign.business_unit_id) if campaign else None
    if not campaign or not contact or not template or not sender or not unit:
        recipient.status = "send_failed"
        recipient.exclusion_reason = "missing_reference"
        return "missing"
    if campaign.state not in {"scheduled", "running"}:
        if recipient.status in {"queued", "retryable", "dispatching"}:
            recipient.status = "cancelled"
        return "campaign_not_running"
    if campaign.state == "scheduled":
        if campaign.schedule_utc and campaign.schedule_utc > utcnow():
            return "waiting_schedule"
        campaign.state = "running"
    settings = get_settings()
    quiet_start = (campaign.quiet_hours_json or {}).get("start") or settings.comm_quiet_hours_start
    quiet_end = (campaign.quiet_hours_json or {}).get("end") or settings.comm_quiet_hours_end
    if not campaign.allow_quiet_hours and in_quiet_hours(utcnow(), quiet_start, quiet_end, campaign.schedule_timezone):
        return "quiet_hours"
    if template.status != "approved":
        pause_campaigns_for_template_safe(db, template.id)
        return "template_halted"
    quality = (sender.quality or "").upper()
    if quality in {"RED", "LOW", "FLAGGED"} or sender.status == "restricted":
        pause_campaigns_for_sender(db, sender.id, "sender_quality")
        return "quality_halted"
    reason = exclusion_reason(
        db,
        contact,
        business_unit_id=unit.id,
        purpose="marketing" if campaign.category == "marketing" else campaign.category,
        category=campaign.category,
    )
    if reason or active_suppression(db, contact.id):
        recipient.status = "excluded"
        recipient.exclusion_reason = reason or "opted_out"
        return "excluded"
    card = rate_for(db, contact.country_iso or "", campaign.category)
    if card is None:
        recipient.status = "excluded"
        recipient.exclusion_reason = "no_rate_card"
        return "excluded"
    price = to_micros(card.unit_rate_decimal)
    if campaign.consumed_micros + price > campaign.reserved_micros:
        campaign.state = "paused"
        campaign.pause_reason = "budget_guard"
        return "budget_guard"
    cap = to_micros(settings.comm_default_max_spend_usd)
    if _reserved_today(db) + price > cap:
        campaign.state = "paused"
        campaign.pause_reason = "daily_spend_cap"
        return "daily_spend_cap"
    limit = int((sender.limits_snapshot or {}).get("unique_recipient_limit") or 0)
    if limit and _rolling_unique(db, unit.organization_id) >= limit:
        return "capacity"
    if _mps_blocked(db) or _pair_blocked(db, sender.id, contact.id):
        return "throttled"
    existing = (
        db.query(CommMessage)
        .filter(CommMessage.campaign_recipient_id == recipient.id, CommMessage.direction == "outbound")
        .order_by(CommMessage.created_at.desc())
        .first()
    )
    if existing and existing.provider_message_id:
        recipient.status = "accepted"
        return "duplicate_skipped"
    if existing and existing.status == "quarantined":
        recipient.status = "quarantined"
        return "quarantined"
    message = existing or CommMessage(
        campaign_recipient_id=recipient.id,
        sender_id=sender.id,
        contact_id=contact.id,
        direction="outbound",
        kind="template",
        status="dispatching",
        provider_metadata={"simulated": gateway.__class__.__name__ != "DirectMetaAdapter"},
    )
    if existing is None:
        db.add(message)
        db.flush()
    attempt_no = db.query(CommSendAttempt).filter(CommSendAttempt.message_id == message.id).count() + 1
    attempt = CommSendAttempt(
        message_id=message.id,
        request_key=f"{recipient.id}:{attempt_no}",
        attempt_no=attempt_no,
        start_at=utcnow(),
    )
    db.add(attempt)
    db.flush()
    recipient.status = "dispatching"
    try:
        result = gateway.send_template(
            sender.id,
            contact.phone_e164,
            {"name": template.meta_name, "language_code": template.language_code},
            meta_components(recipient.rendered_parameters_json or {}),
            {"phone_number_id": sender.phone_number_id, "campaign_id": campaign.id},
        )
    except UnknownOutcome:
        attempt.timeout_unknown = True
        attempt.end_at = utcnow()
        message.status = "quarantined"
        recipient.status = "quarantined"
        db.flush()
        return "quarantined"
    except ProviderError as exc:
        attempt.http_status = exc.http_status
        attempt.provider_error_code = exc.code
        attempt.end_at = utcnow()
        if exc.retryable and attempt_no < settings.comm_max_send_attempts and exc.code != "live_send_disabled":
            recipient.status = "retryable"
            message.status = "retryable"
            db.flush()
            return "retryable"
        recipient.status = "send_failed"
        message.status = "send_failed"
        message.error_code = exc.code
        db.flush()
        return "send_failed"
    attempt.http_status = result.http_status
    attempt.end_at = utcnow()
    message.provider_message_id = result.provider_message_id
    message.status = "accepted"
    message.accepted_at = utcnow()
    message.provider_metadata = {**(message.provider_metadata or {}), "reserved_micros": price}
    recipient.status = "accepted"
    campaign.consumed_micros += price
    db.flush()
    return "accepted"


def pause_campaigns_for_template_safe(db: Session, template_id: str) -> None:
    from app.communications.campaigns import pause_campaigns_for_template

    pause_campaigns_for_template(db, template_id, "template_not_approved")


def process_due(db: Session, gateway: MessagingGateway, *, limit: int | None = None) -> int:
    settings = get_settings()
    batch = limit or settings.comm_dispatch_batch_size
    now = utcnow()
    jobs = (
        db.query(CommOutbox)
        .filter(CommOutbox.status == "pending", CommOutbox.job_kind == "dispatch", CommOutbox.next_attempt_at <= now)
        .order_by(CommOutbox.next_attempt_at.asc())
        .limit(batch)
        .all()
    )
    handled = 0
    for job in jobs:
        if not _claim(db, job):
            continue
        outcome = dispatch_recipient(db, job.aggregate_id, gateway)
        if outcome in {"quiet_hours", "waiting_schedule", "capacity", "throttled"}:
            delay = 60 if outcome != "throttled" else 1
            if outcome == "capacity":
                delay = 900
            _requeue(job, delay, outcome)
        elif outcome == "retryable":
            job.attempts += 1
            delay = min(300, 2 ** job.attempts) + random.randint(0, 2)
            if job.attempts >= settings.comm_max_send_attempts:
                job.status = "dead"
            else:
                _requeue(job, delay, "retryable")
        elif outcome == "quarantined":
            job.status = "quarantined"
            job.last_error = "unknown_outcome"
        elif outcome in {"budget_guard", "daily_spend_cap", "template_halted", "quality_halted", "campaign_not_running"}:
            job.status = "cancelled"
            job.last_error = outcome
        else:
            job.status = "done"
        job.updated_at = utcnow()
        handled += 1
        _maybe_complete(db, (job.payload_json or {}).get("campaign_id"))
    db.flush()
    return handled


def _maybe_complete(db: Session, campaign_id: str | None) -> None:
    if not campaign_id:
        return
    campaign = db.get(CommCampaign, campaign_id)
    if campaign is None or campaign.state != "running":
        return
    open_recipients = (
        db.query(CommRecipient)
        .filter(
            CommRecipient.campaign_id == campaign.id,
            CommRecipient.status.in_(["queued", "dispatching", "retryable", "eligible"]),
        )
        .count()
    )
    pending_jobs = (
        db.query(CommOutbox)
        .filter(CommOutbox.status.in_(["pending", "processing", "quarantined"]))
        .all()
    )
    related = [job for job in pending_jobs if (job.payload_json or {}).get("campaign_id") == campaign.id]
    quarantined = db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id, CommRecipient.status == "quarantined").count()
    if open_recipients == 0 and not related and quarantined == 0:
        campaign.state = "completed"
        campaign.updated_at = utcnow()
