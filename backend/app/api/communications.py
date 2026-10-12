"""AC Communications HTTP API."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from decimal import Decimal

import pyotp
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.communications.audit import audit
from app.communications.billing import add_rate_card, reconcile_invoice
from app.communications.campaigns import (
    approve_campaign,
    campaign_stats,
    preview,
    release_production,
    schedule_campaign,
    submit_campaign,
    transition,
)
from app.communications.crm import import_contacts, suppress_contact
from app.communications.dispatch import process_due
from app.communications.foundation import ensure_foundation, ensure_membership, utcnow
from app.communications.gateway import get_gateway
from app.communications.inbox import send_reply, window_open
from app.communications.money import format_usd, to_micros
from app.communications.phones import csv_safe, mask_phone, normalize_phone
from app.communications.rbac import require_membership, require_totp
from app.communications.webhooks import apply_webhook_payload, ingest_webhook
from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import client_ip, get_current_user
from app.models import User
from app.models_comm import (
    CommAuditLog,
    CommBusinessUnit,
    CommCampaign,
    CommContact,
    CommConversation,
    CommCostLedger,
    CommImportJob,
    CommMembership,
    CommMessage,
    CommRateCard,
    CommRecipient,
    CommSegment,
    CommSender,
    CommTemplate,
)

router = APIRouter(prefix="/api/v1/communications", tags=["communications"])


class SenderIn(BaseModel):
    phone_e164: str
    display_name: str
    phone_number_id: str | None = None
    waba_id: str | None = None
    unique_recipient_limit: int | None = None


class ContactIn(BaseModel):
    phone_number: str
    display_name: str | None = None
    city: str | None = None
    preferred_locale: str | None = None
    source: str | None = None


class ConsentIn(BaseModel):
    purpose: str = "marketing"
    obtained_at: datetime
    source: str
    notice_version: str
    proof_uri: str
    business_unit_id: str | None = None


class SegmentIn(BaseModel):
    name: str
    business_unit_id: str | None = None
    filter_json: dict = Field(default_factory=dict)


class TemplateIn(BaseModel):
    meta_name: str
    language_code: str
    category: str = "marketing"
    body_param_count: int = 0
    header_param_count: int = 0
    button_param_count: int = 0
    waba_id: str | None = None
    sender_id: str | None = None


class CampaignIn(BaseModel):
    name: str
    business_unit_id: str | None = None
    sender_id: str
    template_id: str
    segment_id: str | None = None
    schedule_timezone: str = "Asia/Baghdad"
    maximum_budget_usd: str
    buffer_percent: int = 0
    quiet_hours: dict | None = None
    allow_quiet_hours: bool = False
    parameter_template: dict = Field(default_factory=dict)
    schedule_utc: datetime | None = None
    test_batch_size: int = 5


class ReplyIn(BaseModel):
    text: str


class RateIn(BaseModel):
    market: str
    category: str
    unit_rate: str
    source: str = "manual"


class ReconcileIn(BaseModel):
    external_invoice_ref: str
    amount_usd: str
    campaign_id: str | None = None


class MemberIn(BaseModel):
    email: str
    role: str


class SimulateIn(BaseModel):
    provider_message_id: str
    status: str = "delivered"
    billable: bool = True


def _guard(db: Session, user: User, perm: str) -> tuple[CommMembership, CommBusinessUnit]:
    org, unit = ensure_foundation(db)
    membership = ensure_membership(db, user)
    require_membership(membership, perm)
    _ = org
    return membership, unit


def _commit(db: Session):
    db.commit()


@router.get("/system/health")
def system_health(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "overview.read")
    redis_ok = False
    try:
        from redis import Redis

        redis_ok = bool(Redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5).ping())
    except Exception:
        redis_ok = False
    settings = get_settings()
    _commit(db)
    return {
        "api": "ok",
        "database": "ok",
        "redis": "ok" if redis_ok else "unavailable",
        "provider": settings.provider_kind,
        "live_send_enabled": settings.comm_live_send_enabled,
        "token_configured": bool(settings.meta_access_token),
        "graph_api_version": settings.graph_api_version,
    }


@router.get("/overview")
def overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "overview.read")
    org, _unit = ensure_foundation(db)
    today = utcnow().date()
    messages = db.query(CommMessage).all()
    def _day(row: CommMessage) -> bool:
        stamp = row.accepted_at or row.created_at
        return bool(stamp and stamp.date() == today)
    todays = [row for row in messages if _day(row)]
    ledger = db.query(CommCostLedger).filter(CommCostLedger.entry_type == "provisional").all()
    _commit(db)
    return {
        "senders": db.query(CommSender).filter(CommSender.organization_id == org.id).count(),
        "contacts": db.query(CommContact).filter(CommContact.organization_id == org.id, CommContact.deleted_at.is_(None)).count(),
        "accepted_today": sum(1 for row in todays if row.status in {"accepted", "sent", "delivered", "read"}),
        "delivered_today": sum(1 for row in todays if row.status in {"delivered", "read"}),
        "failed_today": sum(1 for row in todays if row.status in {"failed", "send_failed"}),
        "replied_today": sum(1 for row in todays if row.direction == "inbound"),
        "provisional_usd": format_usd(sum(row.amount_micros for row in ledger)),
        "live_send_enabled": get_settings().comm_live_send_enabled,
        "business_units": [
            {"id": row.id, "name": row.name}
            for row in db.query(CommBusinessUnit).filter(CommBusinessUnit.organization_id == org.id, CommBusinessUnit.active.is_(True)).all()
        ],
    }


@router.get("/senders")
def list_senders(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    membership, _unit = _guard(db, user, "overview.read")
    org_id = membership.organization_id
    rows = db.query(CommSender).filter(CommSender.organization_id == org_id).all()
    _commit(db)
    return [_sender_out(row) for row in rows]


@router.post("/senders", status_code=201)
def create_sender(payload: SenderIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    membership, _unit = _guard(db, user, "admin.secrets")
    e164, iso, error = normalize_phone(payload.phone_e164)
    if error or not e164:
        raise HTTPException(status_code=422, detail="Sender phone is not a valid number")
    sender = CommSender(
        organization_id=membership.organization_id,
        provider=get_settings().provider_kind,
        phone_e164=e164,
        phone_number_id=payload.phone_number_id,
        waba_id=payload.waba_id or get_settings().meta_waba_id or "local",
        display_name=payload.display_name,
        status="connected",
        quality="UNKNOWN",
        limits_snapshot={"unique_recipient_limit": payload.unique_recipient_limit} if payload.unique_recipient_limit else {},
    )
    db.add(sender)
    audit(db, actor_id=user.id, action="sender.create", object_type="sender", object_id=sender.id, metadata={"country": iso})
    _commit(db)
    return _sender_out(sender)


@router.get("/senders/{sender_id}/health")
def sender_health(sender_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "overview.read")
    sender = db.get(CommSender, sender_id)
    if sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")
    health = get_gateway().get_sender_health(sender.id)
    health["quality"] = sender.quality
    health["limits"] = sender.limits_snapshot
    health["token"] = None
    _commit(db)
    return health


@router.get("/contacts")
def list_contacts(
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    membership, _unit = _guard(db, user, "contacts.read")
    rows = db.query(CommContact).filter(CommContact.organization_id == membership.organization_id, CommContact.deleted_at.is_(None)).all()
    if q:
        needle = q.lower()
        rows = [row for row in rows if needle in (row.display_name or "").lower() or needle in (row.city or "").lower() or needle in row.phone_e164]
    _commit(db)
    return [_contact_out(row, reveal=membership.role in {"super_admin", "marketing_manager"}) for row in rows[:200]]


@router.post("/contacts", status_code=201)
def create_contact(payload: ContactIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    membership, _unit = _guard(db, user, "contacts.write")
    e164, iso, error = normalize_phone(payload.phone_number)
    if error or not e164:
        raise HTTPException(status_code=422, detail=error or "invalid_phone")
    contact = CommContact(
        organization_id=membership.organization_id,
        phone_e164=e164,
        display_name=payload.display_name,
        city=payload.city,
        country_iso=iso,
        preferred_locale=payload.preferred_locale,
        source=payload.source,
        tags=[],
        parse_confidence="1.0",
    )
    db.add(contact)
    audit(db, actor_id=user.id, action="contact.create", object_type="contact", object_id=contact.id, metadata={"consent": "not_granted"})
    _commit(db)
    return _contact_out(contact, reveal=True)


@router.post("/contacts/imports", status_code=202)
async def start_import(
    file: UploadFile = File(...),
    business_unit_id: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    membership, unit = _guard(db, user, "contacts.write")
    data = await file.read()
    if len(data) > 20_000_000:
        raise HTTPException(status_code=413, detail="Import file is too large")
    job = import_contacts(
        db,
        organization_id=membership.organization_id,
        business_unit_id=business_unit_id or unit.id,
        actor_id=user.id,
        filename=file.filename or "contacts.csv",
        data=data,
    )
    _commit(db)
    return _job_out(job)


@router.get("/contacts/imports/{job_id}")
def get_import(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "contacts.read")
    job = db.get(CommImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    return _job_out(job)


@router.post("/contacts/{contact_id}/consents", status_code=201)
def add_consent(
    contact_id: str,
    payload: ConsentIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _membership, unit = _guard(db, user, "contacts.consent")
    contact = db.get(CommContact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    from app.models_comm import CommConsent

    row = CommConsent(
        contact_id=contact.id,
        business_unit_id=payload.business_unit_id or unit.id,
        purpose=payload.purpose,
        channel="whatsapp",
        status="granted",
        obtained_at=payload.obtained_at,
        source=payload.source,
        notice_version=payload.notice_version,
        proof_uri=payload.proof_uri,
    )
    db.add(row)
    audit(db, actor_id=user.id, action="consent.append", object_type="contact", object_id=contact.id, ip=client_ip(request), metadata={"purpose": payload.purpose})
    _commit(db)
    return {"id": row.id, "status": row.status}


@router.post("/contacts/{contact_id}/opt-out")
def opt_out(contact_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "contacts.optout")
    contact = db.get(CommContact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    suppress_contact(db, contact, reason="agent_opt_out", actor_id=user.id, source="agent")
    _commit(db)
    return {"status": "suppressed"}


@router.get("/contacts/export")
def export_contacts(
    request: Request,
    mask: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    membership, _unit = _guard(db, user, "contacts.export")
    reveal = (not mask) and membership.role == "super_admin"
    rows = db.query(CommContact).filter(CommContact.organization_id == membership.organization_id, CommContact.deleted_at.is_(None)).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["phone_e164", "display_name", "city", "country_iso", "preferred_locale"])
    for row in rows:
        phone = row.phone_e164 if reveal else mask_phone(row.phone_e164)
        writer.writerow([csv_safe(phone), csv_safe(row.display_name), csv_safe(row.city), row.country_iso or "", row.preferred_locale or ""])
    audit(db, actor_id=user.id, action="contacts.export", object_type="contact", object_id=membership.organization_id, ip=client_ip(request), metadata={"count": len(rows), "masked": not reveal})
    _commit(db)
    return Response(buffer.getvalue(), media_type="text/csv")


@router.get("/segments")
def list_segments(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _guard(db, user, "contacts.read")
    rows = db.query(CommSegment).all()
    return [{"id": row.id, "name": row.name, "business_unit_id": row.business_unit_id, "filter_json": row.filter_json} for row in rows]


@router.post("/segments", status_code=201)
def create_segment(payload: SegmentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _membership, unit = _guard(db, user, "segments.write")
    row = CommSegment(
        business_unit_id=payload.business_unit_id or unit.id,
        name=payload.name,
        filter_json=payload.filter_json,
        created_by=user.id,
    )
    db.add(row)
    _commit(db)
    return {"id": row.id, "name": row.name}


@router.get("/templates")
def list_templates(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _guard(db, user, "overview.read")
    rows = db.query(CommTemplate).all()
    return [_template_out(row) for row in rows]


@router.post("/templates", status_code=201)
def register_template(payload: TemplateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    membership, _unit = _guard(db, user, "templates.sync")
    settings = get_settings()
    if settings.comm_live_send_enabled:
        raise HTTPException(status_code=403, detail="Live templates must be synced from Meta")
    row = CommTemplate(
        organization_id=membership.organization_id,
        sender_id=payload.sender_id,
        waba_id=payload.waba_id or "local",
        meta_name=payload.meta_name,
        language_code=payload.language_code,
        category=payload.category,
        status="approved",
        components_json={
            "body_param_count": payload.body_param_count,
            "header_param_count": payload.header_param_count,
            "button_param_count": payload.button_param_count,
        },
        approved_at=utcnow(),
        synced_at=utcnow(),
    )
    db.add(row)
    audit(db, actor_id=user.id, action="template.local_register", object_type="template", object_id=row.id, metadata={"language": payload.language_code})
    _commit(db)
    return _template_out(row)


@router.post("/templates/sync")
def sync_templates(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    membership, _unit = _guard(db, user, "templates.sync")
    settings = get_settings()
    waba = settings.meta_waba_id
    if not waba:
        raise HTTPException(status_code=409, detail="META_WABA_ID is not configured")
    remote = get_gateway().sync_templates(waba)
    saved = 0
    for item in remote:
        existing = (
            db.query(CommTemplate)
            .filter(
                CommTemplate.waba_id == waba,
                CommTemplate.meta_name == item["meta_name"],
                CommTemplate.language_code == item["language_code"],
            )
            .first()
        )
        if existing is None:
            existing = CommTemplate(
                organization_id=membership.organization_id,
                waba_id=waba,
                meta_name=item["meta_name"],
                language_code=item["language_code"],
                category=item["category"],
                status=item["status"],
                components_json=item["components_json"],
            )
            db.add(existing)
        else:
            existing.status = item["status"]
            existing.category = item["category"]
            existing.components_json = item["components_json"]
        existing.synced_at = utcnow()
        if existing.status == "approved":
            existing.approved_at = existing.approved_at or utcnow()
        saved += 1
    _commit(db)
    return {"synced": saved}


@router.get("/campaigns")
def list_campaigns(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _guard(db, user, "overview.read")
    rows = db.query(CommCampaign).order_by(CommCampaign.created_at.desc()).all()
    return [_campaign_out(row) for row in rows]


@router.post("/campaigns", status_code=201)
def create_campaign(payload: CampaignIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _membership, unit = _guard(db, user, "campaigns.create")
    template = db.get(CommTemplate, payload.template_id)
    sender = db.get(CommSender, payload.sender_id)
    if template is None or sender is None:
        raise HTTPException(status_code=404, detail="Sender or template not found")
    campaign = CommCampaign(
        business_unit_id=payload.business_unit_id or unit.id,
        sender_id=sender.id,
        template_id=template.id,
        segment_id=payload.segment_id,
        name=payload.name,
        category=template.category,
        state="draft",
        schedule_timezone=payload.schedule_timezone,
        schedule_utc=payload.schedule_utc,
        quiet_hours_json=payload.quiet_hours or {"start": "21:00", "end": "09:00"},
        allow_quiet_hours=payload.allow_quiet_hours,
        parameter_template=payload.parameter_template,
        budget_micros=to_micros(Decimal(payload.maximum_budget_usd)),
        buffer_percent=payload.buffer_percent,
        test_batch_size=payload.test_batch_size,
        created_by=user.id,
    )
    db.add(campaign)
    db.flush()
    audit(db, actor_id=user.id, action="campaign.create", object_type="campaign", object_id=campaign.id, metadata={})
    _commit(db)
    return _campaign_out(campaign)


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "overview.read")
    campaign = _campaign(db, campaign_id)
    data = _campaign_out(campaign)
    data["stats"] = campaign_stats(db, campaign)
    return data


@router.post("/campaigns/{campaign_id}/preview")
def preview_campaign(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.create")
    campaign = _campaign(db, campaign_id)
    report = preview(db, campaign)
    _commit(db)
    return report


@router.post("/campaigns/{campaign_id}/submit")
def submit(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.create")
    campaign = _campaign(db, campaign_id)
    submit_campaign(db, campaign, user.id)
    _commit(db)
    return _campaign_out(campaign)


@router.post("/campaigns/{campaign_id}/approve")
def approve(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.approve")
    campaign = _campaign(db, campaign_id)
    approve_campaign(db, campaign, user.id)
    _commit(db)
    return _campaign_out(campaign)


@router.post("/campaigns/{campaign_id}/reject")
def reject(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.approve")
    campaign = _campaign(db, campaign_id)
    transition(campaign, "rejected")
    audit(db, actor_id=user.id, action="campaign.reject", object_type="campaign", object_id=campaign.id, metadata={})
    _commit(db)
    return _campaign_out(campaign)


@router.post("/campaigns/{campaign_id}/schedule")
def schedule(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.operate")
    campaign = _campaign(db, campaign_id)
    queued = schedule_campaign(db, campaign, user.id)
    if get_settings().comm_process_inline:
        process_due(db, get_gateway())
    _commit(db)
    return {"queued": queued, "state": campaign.state}


@router.post("/campaigns/{campaign_id}/tick")
def tick(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.operate")
    _campaign(db, campaign_id)
    handled = process_due(db, get_gateway())
    _commit(db)
    return {"processed": handled}


@router.post("/campaigns/{campaign_id}/pause")
def pause(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.operate")
    campaign = _campaign(db, campaign_id)
    transition(campaign, "paused")
    campaign.pause_reason = "operator"
    from app.communications.campaigns import _withdraw_unsent

    _withdraw_unsent(db, campaign)
    audit(db, actor_id=user.id, action="campaign.pause", object_type="campaign", object_id=campaign.id, metadata={})
    _commit(db)
    return _campaign_out(campaign)


@router.post("/campaigns/{campaign_id}/resume")
def resume(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.operate")
    campaign = _campaign(db, campaign_id)
    transition(campaign, "running")
    campaign.pause_reason = None
    _commit(db)
    return _campaign_out(campaign)


@router.post("/campaigns/{campaign_id}/cancel")
def cancel(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.operate")
    campaign = _campaign(db, campaign_id)
    transition(campaign, "cancelled")
    from app.communications.campaigns import _withdraw_unsent

    _withdraw_unsent(db, campaign)
    audit(db, actor_id=user.id, action="campaign.cancel", object_type="campaign", object_id=campaign.id, metadata={"note": "accepted messages are not recalled"})
    _commit(db)
    return _campaign_out(campaign)


@router.post("/campaigns/{campaign_id}/release")
def release(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.operate")
    campaign = _campaign(db, campaign_id)
    queued = release_production(db, campaign, user.id)
    if get_settings().comm_process_inline:
        process_due(db, get_gateway())
    _commit(db)
    return {"queued": queued}


@router.get("/campaigns/{campaign_id}/stats")
def stats(campaign_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "overview.read")
    return campaign_stats(db, _campaign(db, campaign_id))


@router.get("/campaigns/{campaign_id}/export")
def export_campaign(campaign_id: str, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    membership, _unit = _guard(db, user, "contacts.export")
    campaign = _campaign(db, campaign_id)
    rows = db.query(CommRecipient).filter(CommRecipient.campaign_id == campaign.id).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["contact_id", "phone", "status", "exclusion_reason"])
    reveal = membership.role == "super_admin"
    for row in rows:
        contact = db.get(CommContact, row.contact_id)
        phone = contact.phone_e164 if contact and reveal else mask_phone(contact.phone_e164 if contact else "")
        writer.writerow([row.contact_id, csv_safe(phone), row.status, row.exclusion_reason or ""])
    audit(db, actor_id=user.id, action="campaign.export", object_type="campaign", object_id=campaign.id, ip=client_ip(request), metadata={"count": len(rows)})
    _commit(db)
    return Response(buffer.getvalue(), media_type="text/csv")


@router.get("/inbox/conversations")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _guard(db, user, "inbox.read")
    rows = db.query(CommConversation).order_by(CommConversation.updated_at.desc()).all()
    return [_conversation_out(row) for row in rows]


@router.get("/inbox/conversations/{conversation_id}")
def get_conversation(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "inbox.read")
    row = db.get(CommConversation, conversation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = (
        db.query(CommMessage)
        .filter(CommMessage.contact_id == row.contact_id, CommMessage.sender_id == row.sender_id)
        .order_by(CommMessage.created_at.asc())
        .all()
    )
    data = _conversation_out(row)
    data["messages"] = [
        {"id": item.id, "direction": item.direction, "kind": item.kind, "status": item.status, "text": item.body_text, "at": _iso(item.created_at)}
        for item in messages
    ]
    return data


@router.post("/inbox/conversations/{conversation_id}/reply")
def reply(conversation_id: str, payload: ReplyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "inbox.reply")
    row = db.get(CommConversation, conversation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    message = send_reply(db, row, actor_id=user.id, text=payload.text, gateway=get_gateway())
    _commit(db)
    return {"id": message.id, "status": message.status}


@router.post("/inbox/conversations/{conversation_id}/opt-out")
def conversation_opt_out(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "contacts.optout")
    row = db.get(CommConversation, conversation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    contact = db.get(CommContact, row.contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    suppress_contact(db, contact, reason="agent_opt_out", actor_id=user.id, source="inbox")
    _commit(db)
    return {"status": "suppressed"}


@router.get("/billing/rates")
def list_rates(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _guard(db, user, "billing.read")
    rows = db.query(CommRateCard).order_by(CommRateCard.valid_from.desc()).all()
    return [
        {
            "id": row.id,
            "market": row.market,
            "category": row.category,
            "currency": row.currency,
            "unit_rate": f"{row.unit_rate_decimal:.6f}",
            "valid_from": _iso(row.valid_from),
            "valid_to": _iso(row.valid_to),
            "source": row.rate_source,
            "source_version": row.source_version,
        }
        for row in rows
    ]


@router.post("/billing/rates", status_code=201)
def create_rate(
    payload: RateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_comm_totp: str | None = Header(default=None),
) -> dict:
    membership, _unit = _guard(db, user, "billing.write")
    require_totp(membership, x_comm_totp)
    card = add_rate_card(db, market=payload.market.upper(), category=payload.category, unit_rate=payload.unit_rate, actor_id=user.id, source=payload.source)
    _commit(db)
    return {"id": card.id}


@router.get("/billing/summary")
def billing_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "billing.read")
    rows = db.query(CommCostLedger).all()
    provisional = sum(row.amount_micros for row in rows if row.entry_type == "provisional")
    adjustments = sum(row.amount_micros for row in rows if row.entry_type == "invoice_adjustment")
    return {
        "provisional_usd": format_usd(provisional),
        "adjustments_usd": format_usd(adjustments),
        "reconciled_usd": format_usd(provisional + adjustments),
        "entries": len(rows),
        "daily_cap_usd": get_settings().comm_default_max_spend_usd,
    }


@router.post("/billing/reconcile")
def reconcile(
    payload: ReconcileIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_comm_totp: str | None = Header(default=None),
) -> dict:
    membership, _unit = _guard(db, user, "billing.write")
    require_totp(membership, x_comm_totp)
    result = reconcile_invoice(
        db,
        external_invoice_ref=payload.external_invoice_ref,
        amount_usd=payload.amount_usd,
        actor_id=user.id,
        campaign_id=payload.campaign_id,
    )
    _commit(db)
    return result


@router.get("/audit")
def list_audit(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _guard(db, user, "audit.read")
    rows = db.query(CommAuditLog).order_by(CommAuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": row.id,
            "actor_id": row.actor_id,
            "action": row.action,
            "object_type": row.object_type,
            "object_id": row.object_id,
            "metadata": row.metadata_json,
            "at": _iso(row.created_at),
        }
        for row in rows
    ]


@router.get("/administration/provider")
def provider_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "admin.secrets")
    settings = get_settings()
    return {
        "provider_kind": settings.provider_kind,
        "live_send_enabled": settings.comm_live_send_enabled,
        "token_configured": bool(settings.meta_access_token),
        "token": None,
        "phone_number_id_configured": bool(settings.meta_phone_number_id),
        "waba_configured": bool(settings.meta_waba_id),
        "graph_api_version": settings.graph_api_version,
        "coexistence_enabled": False,
    }


@router.post("/administration/provider/token")
def rotate_token(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "campaigns.operate")
    raise HTTPException(status_code=403, detail="API tokens are not editable from the dashboard")


@router.get("/administration/members")
def list_members(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _guard(db, user, "admin.members")
    rows = db.query(CommMembership).all()
    return [{"id": row.id, "user_id": row.user_id, "role": row.role, "active": row.active, "totp_enabled": row.totp_enabled} for row in rows]


@router.post("/administration/members", status_code=201)
def add_member(payload: MemberIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    membership, _unit = _guard(db, user, "admin.members")
    from app.communications.rbac import ROLES

    if payload.role not in ROLES:
        raise HTTPException(status_code=422, detail="Unknown role")
    target = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    row = CommMembership(organization_id=membership.organization_id, user_id=target.id, role=payload.role, active=True)
    db.add(row)
    audit(db, actor_id=user.id, action="member.add", object_type="membership", object_id=row.id, metadata={"role": payload.role})
    _commit(db)
    return {"id": row.id, "role": row.role}


@router.post("/administration/mfa/enroll")
def enroll_mfa(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    membership, _unit = _guard(db, user, "admin.secrets")
    secret = pyotp.random_base32()
    membership.totp_secret = secret
    membership.totp_enabled = False
    _commit(db)
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Art City Communications")
    return {"otpauth_uri": uri, "secret": secret}


@router.post("/administration/mfa/confirm")
def confirm_mfa(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_comm_totp: str | None = Header(default=None),
) -> dict:
    membership, _unit = _guard(db, user, "admin.secrets")
    if not membership.totp_secret or not x_comm_totp or not pyotp.TOTP(membership.totp_secret).verify(x_comm_totp, valid_window=1):
        raise HTTPException(status_code=403, detail="Invalid authenticator code")
    membership.totp_enabled = True
    _commit(db)
    return {"totp_enabled": True}


@router.post("/administration/simulate-delivery")
def simulate_delivery(payload: SimulateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _guard(db, user, "admin.secrets")
    if get_settings().comm_live_send_enabled:
        raise HTTPException(status_code=403, detail="Simulation is disabled when live send is on")
    message = db.query(CommMessage).filter(CommMessage.provider_message_id == payload.provider_message_id).first()
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    body = {
        "entry": [
            {
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "statuses": [
                                {
                                    "id": payload.provider_message_id,
                                    "status": payload.status,
                                    "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
                                    "pricing": {"billable": payload.billable, "category": "marketing"},
                                }
                            ]
                        },
                    }
                ]
            }
        ]
    }
    apply_webhook_payload(db, body)
    _commit(db)
    return {"status": message.status}


@router.get("/integrations/whatsapp/webhook")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> PlainTextResponse:
    settings = get_settings()
    if hub_mode == "subscribe" and settings.meta_verify_token and hub_verify_token == settings.meta_verify_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/integrations/whatsapp/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    raw = await request.body()
    result = ingest_webhook(db, raw_body=raw, signature=request.headers.get("x-hub-signature-256"))
    if not result.get("accepted"):
        code = 403 if result.get("reason") == "bad_signature" else 400
        raise HTTPException(status_code=code, detail=result.get("reason"))
    _commit(db)
    return {"status": "ok"}


def _campaign(db: Session, campaign_id: str) -> CommCampaign:
    campaign = db.get(CommCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _sender_out(row: CommSender) -> dict:
    return {
        "id": row.id,
        "phone_masked": mask_phone(row.phone_e164),
        "display_name": row.display_name,
        "status": row.status,
        "quality": row.quality,
        "limits": row.limits_snapshot,
        "provider": row.provider,
    }


def _contact_out(row: CommContact, *, reveal: bool) -> dict:
    return {
        "id": row.id,
        "phone": row.phone_e164 if reveal else mask_phone(row.phone_e164),
        "display_name": row.display_name,
        "city": row.city,
        "country_iso": row.country_iso,
        "preferred_locale": row.preferred_locale,
        "source": row.source,
        "tags": row.tags or [],
    }


def _template_out(row: CommTemplate) -> dict:
    return {
        "id": row.id,
        "meta_name": row.meta_name,
        "language_code": row.language_code,
        "category": row.category,
        "status": row.status,
        "components": row.components_json,
        "approved_at": _iso(row.approved_at),
    }


def _campaign_out(row: CommCampaign) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "state": row.state,
        "category": row.category,
        "sender_id": row.sender_id,
        "template_id": row.template_id,
        "segment_id": row.segment_id,
        "business_unit_id": row.business_unit_id,
        "budget_usd": format_usd(row.budget_micros),
        "quote_usd": format_usd(row.quote_micros),
        "reserved_usd": format_usd(row.reserved_micros),
        "consumed_usd": format_usd(row.consumed_micros),
        "pause_reason": row.pause_reason,
        "schedule_timezone": row.schedule_timezone,
        "production_released": row.production_released,
    }


def _conversation_out(row: CommConversation) -> dict:
    return {
        "id": row.id,
        "sender_id": row.sender_id,
        "contact_id": row.contact_id,
        "state": row.state,
        "unread_count": row.unread_count,
        "window_open": window_open(row),
        "service_window_expires_at": _iso(row.service_window_expires_at),
        "assigned_user_id": row.assigned_user_id,
    }


def _job_out(job: CommImportJob) -> dict:
    counts = (job.rejections_json or {}).get("counts") or {}
    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.count_total,
        "inserted": job.inserted,
        "updated": job.updated,
        "rejected": job.rejected,
        "rejections": counts,
        "with_valid_marketing_opt_in": job.with_valid_marketing_opt_in,
        "requires_consent": job.requires_consent,
        "checksum": job.checksum,
    }
