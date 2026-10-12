"""Campaign snapshot, approval, and reporting."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.communications.audit import audit
from app.communications.billing import rate_for
from app.communications.crm import contact_matches, exclusion_reason
from app.communications.foundation import utcnow
from app.communications.money import format_usd, to_micros
from app.core.config import get_settings
from app.models_comm import (
    CommAudienceSnapshot,
    CommBusinessUnit,
    CommCampaign,
    CommContact,
    CommOutbox,
    CommRecipient,
    CommSegment,
    CommSender,
    CommTemplate,
)

_TRANSITIONS = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"approved", "rejected", "cancelled"},
    "rejected": {"draft"},
    "approved": {"scheduled", "cancelled"},
    "scheduled": {"running", "paused", "cancelled"},
    "running": {"paused", "completed", "cancelled"},
    "paused": {"running", "scheduled", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}

_ACCEPTED = {"accepted", "sent", "delivered", "read", "failed"}


def in_quiet_hours(moment: datetime, start: str, end: str, tz_name: str) -> bool:
    local = moment.astimezone(ZoneInfo(tz_name))
    minutes = local.hour * 60 + local.minute
    sh, sm = (int(part) for part in start.split(":"))
    eh, em = (int(part) for part in end.split(":"))
    start_m = sh * 60 + sm
    end_m = eh * 60 + em
    if start_m == end_m:
        return False
    if start_m < end_m:
        return start_m <= minutes < end_m
    return minutes >= start_m or minutes < end_m


def _resolve(contact: CommContact, token: str) -> str:
    text = (token or "").strip()
    if text.startswith("{{") and text.endswith("}}"):
        field = text[2:-2].strip()
        if field in {"name", "display_name"}:
            return contact.display_name or ""
        if field == "city":
            return contact.city or ""
        if field == "locale":
            return contact.preferred_locale or ""
        return ""
    return text


def render_parameters(contact: CommContact, parameter_template: dict[str, Any]) -> dict[str, list[str]]:
    rendered: dict[str, list[str]] = {}
    for key in ("body", "header", "buttons"):
        rendered[key] = [_resolve(contact, item) for item in (parameter_template.get(key) or [])]
    return rendered


def parameters_complete(rendered: dict[str, list[str]], components: dict[str, Any]) -> bool:
    needed = {
        "body": int(components.get("body_param_count") or 0),
        "header": int(components.get("header_param_count") or 0),
        "buttons": int(components.get("button_param_count") or 0),
    }
    for key, count in needed.items():
        values = rendered.get(key) or []
        if len(values) < count:
            return False
        if any(not str(values[idx]).strip() for idx in range(count)):
            return False
    return True


def meta_components(rendered: dict[str, list[str]]) -> list[dict[str, Any]]:
    components = []
    for key, meta_type in (("header", "header"), ("body", "body"), ("buttons", "button")):
        values = [value for value in rendered.get(key) or [] if value != ""]
        if not values:
            continue
        components.append({"type": meta_type, "parameters": [{"type": "text", "text": value} for value in values]})
    return components


def _purpose(category: str) -> str:
    return "marketing" if category == "marketing" else category


def transition(campaign: CommCampaign, target: str) -> None:
    allowed = _TRANSITIONS.get(campaign.state, set())
    if target not in allowed:
        raise HTTPException(status_code=409, detail=f"Cannot move campaign from {campaign.state} to {target}")
    campaign.state = target
    campaign.updated_at = utcnow()


def _segment_contacts(db: Session, unit: CommBusinessUnit, segment: CommSegment | None) -> list[CommContact]:
    query = db.query(CommContact).filter(
        CommContact.organization_id == unit.organization_id,
        CommContact.deleted_at.is_(None),
    )
    contacts = query.all()
    filt = segment.filter_json if segment else {}
    return [contact for contact in contacts if contact_matches(contact, filt or {})]


def rebuild_recipients(db: Session, campaign: CommCampaign) -> list[CommRecipient]:
    if campaign.state not in {"draft", "submitted"}:
        return db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id).all()
    unit = db.get(CommBusinessUnit, campaign.business_unit_id)
    segment = db.get(CommSegment, campaign.segment_id) if campaign.segment_id else None
    template = db.get(CommTemplate, campaign.template_id)
    if unit is None or template is None:
        raise HTTPException(status_code=404, detail="Campaign references are missing")
    db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id).delete()
    now = utcnow()
    rows: list[CommRecipient] = []
    for contact in _segment_contacts(db, unit, segment):
        rendered = render_parameters(contact, campaign.parameter_template or {})
        reason = exclusion_reason(
            db,
            contact,
            business_unit_id=unit.id,
            purpose=_purpose(campaign.category),
            category=campaign.category,
            now=now,
        )
        if reason is None and not parameters_complete(rendered, template.components_json or {}):
            reason = "missing_variable"
        if reason is None and rate_for(db, contact.country_iso or "", campaign.category, now) is None:
            reason = "no_rate_card"
        recipient = CommRecipient(
            campaign_id=campaign.id,
            contact_id=contact.id,
            rendered_parameters_json=rendered,
            status="excluded" if reason else "eligible",
            exclusion_reason=reason,
        )
        db.add(recipient)
        rows.append(recipient)
    db.flush()
    return rows


def preview(db: Session, campaign: CommCampaign) -> dict[str, Any]:
    template = db.get(CommTemplate, campaign.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    blocking = []
    if template.status != "approved":
        blocking.append("template_not_approved")
    if template.category != campaign.category:
        blocking.append("template_category_mismatch")
    rows = rebuild_recipients(db, campaign) if campaign.state in {"draft", "submitted"} else (
        db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id).all()
    )
    excluded: dict[str, int] = {}
    by_market: dict[str, int] = {}
    eligible_rows = []
    for row in rows:
        if row.exclusion_reason:
            excluded[row.exclusion_reason] = excluded.get(row.exclusion_reason, 0) + 1
            continue
        eligible_rows.append(row)
        contact = db.get(CommContact, row.contact_id)
        market = (contact.country_iso if contact else None) or "??"
        by_market[market] = by_market.get(market, 0) + 1
    quote = 0
    markets = []
    now = utcnow()
    for market, count in sorted(by_market.items()):
        card = rate_for(db, market, campaign.category, now)
        unit = to_micros(card.unit_rate_decimal) if card else 0
        if card is None:
            blocking.append(f"no_rate_card:{market}")
        part = unit * count
        quote += part
        markets.append({"market": market, "eligible": count, "quote_usd": format_usd(part)})
    samples = []
    for row in eligible_rows[:5]:
        contact = db.get(CommContact, row.contact_id)
        samples.append(
            {
                "contact_id": row.contact_id,
                "phone_masked": True,
                "parameters": row.rendered_parameters_json,
                "template_language": template.language_code,
            }
        )
    settings = get_settings()
    sender = db.get(CommSender, campaign.sender_id)
    limit = int((sender.limits_snapshot or {}).get("unique_recipient_limit") or 0) if sender else 0
    return {
        "selected": len(rows),
        "eligible": len(eligible_rows),
        "excluded": excluded,
        "quote_usd": format_usd(quote),
        "quote_micros": quote,
        "by_market": markets,
        "samples": samples,
        "blocking_errors": blocking,
        "can_submit": not blocking and len(eligible_rows) > 0,
        "sender_capacity_status": "check_live_provider_limit" if settings.comm_live_send_enabled else "internal_snapshot",
        "unique_recipient_limit": limit,
        "budget_usd": format_usd(campaign.budget_micros),
        "budget_feasible": campaign.budget_micros >= quote,
        "template_language": template.language_code,
        "template_status": template.status,
    }


def checksum_for(rows: list[CommRecipient], campaign: CommCampaign) -> str:
    payload = {
        "template_id": campaign.template_id,
        "sender_id": campaign.sender_id,
        "budget_micros": campaign.budget_micros,
        "contacts": [
            {"id": row.contact_id, "status": row.status, "reason": row.exclusion_reason, "params": row.rendered_parameters_json}
            for row in sorted(rows, key=lambda item: item.contact_id)
        ],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def submit_campaign(db: Session, campaign: CommCampaign, actor_id: str) -> CommCampaign:
    report = preview(db, campaign)
    if not report["can_submit"]:
        raise HTTPException(status_code=422, detail={"code": "preflight_failed", "blocking_errors": report["blocking_errors"]})
    rows = db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id).all()
    digest = checksum_for(rows, campaign)
    transition(campaign, "submitted")
    campaign.submitted_by = actor_id
    campaign.quote_micros = report["quote_micros"]
    campaign.snapshot_checksum = digest
    audit(db, actor_id=actor_id, action="campaign.submit", object_type="campaign", object_id=campaign.id, metadata={"checksum": digest})
    return campaign


def approve_campaign(db: Session, campaign: CommCampaign, actor_id: str) -> CommCampaign:
    settings = get_settings()
    if settings.comm_require_separate_approval and campaign.submitted_by == actor_id:
        raise HTTPException(status_code=403, detail="Campaign submitter cannot approve the same campaign")
    if campaign.snapshot_checksum is None:
        raise HTTPException(status_code=409, detail="Campaign has no snapshot")
    rows = db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id).all()
    if checksum_for(rows, campaign) != campaign.snapshot_checksum:
        raise HTTPException(status_code=409, detail="Audience changed after submit")
    buffer = campaign.buffer_percent or 0
    reserve = int(campaign.quote_micros * (100 + buffer) / 100)
    if reserve > campaign.budget_micros:
        raise HTTPException(status_code=422, detail="Budget does not cover the quoted reserve")
    template = db.get(CommTemplate, campaign.template_id)
    if template is None or template.status != "approved":
        raise HTTPException(status_code=422, detail="Template is not approved")
    snap = CommAudienceSnapshot(
        campaign_id=campaign.id,
        checksum=campaign.snapshot_checksum,
        frozen_json={
            "template_id": campaign.template_id,
            "language_code": template.language_code,
            "sender_id": campaign.sender_id,
            "quote_micros": campaign.quote_micros,
            "contact_ids": [row.contact_id for row in rows if not row.exclusion_reason],
            "quiet_hours": campaign.quiet_hours_json,
        },
    )
    db.add(snap)
    db.flush()
    transition(campaign, "approved")
    campaign.approved_by = actor_id
    campaign.approved_at = datetime.now(timezone.utc)
    campaign.reserved_micros = reserve
    campaign.audience_snapshot_id = snap.id
    audit(db, actor_id=actor_id, action="campaign.approve", object_type="campaign", object_id=campaign.id, metadata={"reserved_micros": reserve})
    return campaign


def schedule_campaign(db: Session, campaign: CommCampaign, actor_id: str) -> int:
    transition(campaign, "scheduled")
    eligible = (
        db.query(CommRecipient)
        .filter(CommRecipient.campaign_id == campaign.id, CommRecipient.status == "eligible")
        .order_by(CommRecipient.created_at.asc())
        .all()
    )
    settings = get_settings()
    if settings.comm_live_send_enabled and not campaign.production_released:
        chosen = eligible[: campaign.test_batch_size]
        for row in chosen:
            row.is_test = True
    else:
        chosen = eligible
    moment = campaign.schedule_utc or utcnow()
    created = 0
    for row in chosen:
        key = f"dispatch:{campaign.id}:{row.contact_id}"
        if db.query(CommOutbox).filter(CommOutbox.idempotency_key == key).first():
            continue
        db.add(
            CommOutbox(
                job_kind="dispatch",
                aggregate_id=row.id,
                idempotency_key=key,
                status="pending",
                payload_json={"campaign_id": campaign.id, "recipient_id": row.id},
                next_attempt_at=moment,
            )
        )
        row.status = "queued"
        row.updated_at = utcnow()
        created += 1
    audit(db, actor_id=actor_id, action="campaign.schedule", object_type="campaign", object_id=campaign.id, metadata={"queued": created})
    db.flush()
    return created


def release_production(db: Session, campaign: CommCampaign, actor_id: str) -> int:
    accepted = (
        db.query(CommRecipient)
        .filter(CommRecipient.campaign_id == campaign.id, CommRecipient.is_test.is_(True), CommRecipient.status.in_(list(_ACCEPTED)))
        .count()
    )
    if accepted < 1:
        raise HTTPException(status_code=409, detail="Test batch has no accepted message yet")
    campaign.production_released = True
    if campaign.state == "paused":
        transition(campaign, "running")
    elif campaign.state == "scheduled":
        pass
    eligible = (
        db.query(CommRecipient)
        .filter(CommRecipient.campaign_id == campaign.id, CommRecipient.status == "eligible", CommRecipient.is_test.is_(False))
        .all()
    )
    created = 0
    moment = utcnow()
    for row in eligible:
        key = f"dispatch:{campaign.id}:{row.contact_id}"
        if db.query(CommOutbox).filter(CommOutbox.idempotency_key == key).first():
            continue
        db.add(
            CommOutbox(
                job_kind="dispatch",
                aggregate_id=row.id,
                idempotency_key=key,
                status="pending",
                payload_json={"campaign_id": campaign.id, "recipient_id": row.id},
                next_attempt_at=moment,
            )
        )
        row.status = "queued"
        created += 1
    audit(db, actor_id=actor_id, action="campaign.release", object_type="campaign", object_id=campaign.id, metadata={"queued": created})
    db.flush()
    return created


def campaign_stats(db: Session, campaign: CommCampaign) -> dict[str, Any]:
    rows = db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id).all()
    excluded = {}
    for row in rows:
        if row.exclusion_reason and row.status == "excluded":
            excluded[row.exclusion_reason] = excluded.get(row.exclusion_reason, 0) + 1
    def count(states: set[str]) -> int:
        return sum(1 for row in rows if row.status in states)
    accepted = count(_ACCEPTED)
    delivered = count({"delivered", "read"})
    read = count({"read"})
    failed = count({"failed", "send_failed"})
    replied = 0
    return {
        "selected": len(rows),
        "eligible": len(rows) - count({"excluded"}),
        "api_accepted": accepted,
        "delivered": delivered,
        "read": read,
        "read_receipts": "available" if read else "unknown_or_unavailable",
        "failed": failed,
        "replied": replied,
        "excluded": excluded,
        "delivery_rate": (delivered / accepted) if accepted else None,
        "quote_usd": format_usd(campaign.quote_micros),
        "reserved_usd": format_usd(campaign.reserved_micros),
        "consumed_usd": format_usd(campaign.consumed_micros),
        "state": campaign.state,
        "pause_reason": campaign.pause_reason,
    }


def pause_campaigns_for_template(db: Session, template_id: str, reason: str) -> int:
    rows = (
        db.query(CommCampaign)
        .filter(CommCampaign.template_id == template_id, CommCampaign.state.in_(["scheduled", "running", "approved"]))
        .all()
    )
    paused = 0
    for campaign in rows:
        if campaign.state in {"scheduled", "running"}:
            campaign.state = "paused"
        campaign.pause_reason = reason
        campaign.updated_at = utcnow()
        _withdraw_unsent(db, campaign)
        paused += 1
    return paused


def pause_campaigns_for_sender(db: Session, sender_id: str, reason: str) -> int:
    rows = (
        db.query(CommCampaign)
        .filter(CommCampaign.sender_id == sender_id, CommCampaign.state.in_(["scheduled", "running"]))
        .all()
    )
    for campaign in rows:
        campaign.state = "paused"
        campaign.pause_reason = reason
        campaign.updated_at = utcnow()
        _withdraw_unsent(db, campaign)
    return len(rows)


def _withdraw_unsent(db: Session, campaign: CommCampaign) -> None:
    jobs = db.query(CommOutbox).filter(CommOutbox.job_kind == "dispatch", CommOutbox.status == "pending").all()
    for job in jobs:
        if (job.payload_json or {}).get("campaign_id") != campaign.id:
            continue
        job.status = "cancelled"
        job.updated_at = utcnow()
        recipient = db.get(CommRecipient, job.aggregate_id)
        if recipient and recipient.status in {"queued", "retryable"}:
            recipient.status = "cancelled"
            recipient.updated_at = utcnow()
