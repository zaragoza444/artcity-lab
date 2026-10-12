"""Default Art City organization, division, and the October 2026 planning rate card."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.communications.phones import normalize_phone
from app.core.enums import UserRole
from app.models import User
from app.models_comm import (
    CommAudienceSnapshot,
    CommBusinessUnit,
    CommCampaign,
    CommConversation,
    CommCostLedger,
    CommMembership,
    CommMessage,
    CommOrganization,
    CommRateCard,
    CommRecipient,
    CommSendAttempt,
    CommSender,
    CommTemplate,
)

# Art City's line is the Meta phone-number id used on the send path.
KNOWN_SENDERS = (
    {"phone": "+9647506931111", "name": "Art City", "phone_number_id": "9647506931111"},
)
REMOVED_SENDER_PHONES = ("+9647507777114",)

PLANNING_RATES = (
    ("marketing", Decimal("0.034100"), {}),
    ("utility", Decimal("0.007900"), {}),
    ("authentication", Decimal("0.007900"), {}),
    ("service", Decimal("0.007900"), {"monthly_free_allowance": 1000}),
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_foundation(db: Session) -> tuple[CommOrganization, CommBusinessUnit]:
    org = db.query(CommOrganization).order_by(CommOrganization.created_at.asc()).first()
    if org is None:
        org = CommOrganization(
            legal_name="Art City Company",
            billing_currency="USD",
            timezone="Asia/Baghdad",
            status="active",
            settings_json={"quick_replies": ["Thank you. A colleague will reply shortly."]},
        )
        db.add(org)
        db.flush()
    unit = (
        db.query(CommBusinessUnit)
        .filter(CommBusinessUnit.organization_id == org.id, CommBusinessUnit.active.is_(True))
        .order_by(CommBusinessUnit.created_at.asc())
        .first()
    )
    if unit is None:
        unit = CommBusinessUnit(organization_id=org.id, name="Marketing", cost_center="AC-MKT", active=True)
        db.add(unit)
        db.flush()
    ensure_rate_cards(db)
    remove_retired_senders(db, org.id)
    ensure_known_senders(db, org.id)
    return org, unit


def remove_retired_senders(db: Session, organization_id: str) -> None:
    for raw in REMOVED_SENDER_PHONES:
        e164, _iso, error = normalize_phone(raw)
        if error or not e164:
            continue
        sender = (
            db.query(CommSender)
            .filter(CommSender.organization_id == organization_id, CommSender.phone_e164 == e164)
            .first()
        )
        if sender is None:
            continue
        db.query(CommTemplate).filter(CommTemplate.sender_id == sender.id).update({"sender_id": None})
        campaign_ids = [row.id for row in db.query(CommCampaign.id).filter(CommCampaign.sender_id == sender.id).all()]
        message_ids = [row.id for row in db.query(CommMessage.id).filter(CommMessage.sender_id == sender.id).all()]
        if message_ids:
            db.query(CommSendAttempt).filter(CommSendAttempt.message_id.in_(message_ids)).delete(synchronize_session=False)
            db.query(CommCostLedger).filter(CommCostLedger.message_id.in_(message_ids)).delete(synchronize_session=False)
        if campaign_ids:
            db.query(CommCostLedger).filter(CommCostLedger.campaign_id.in_(campaign_ids)).delete(synchronize_session=False)
        db.query(CommMessage).filter(CommMessage.sender_id == sender.id).delete(synchronize_session=False)
        db.query(CommConversation).filter(CommConversation.sender_id == sender.id).delete(synchronize_session=False)
        if campaign_ids:
            db.query(CommRecipient).filter(CommRecipient.campaign_id.in_(campaign_ids)).delete(synchronize_session=False)
            db.query(CommAudienceSnapshot).filter(CommAudienceSnapshot.campaign_id.in_(campaign_ids)).delete(synchronize_session=False)
        db.query(CommCampaign).filter(CommCampaign.sender_id == sender.id).delete(synchronize_session=False)
        db.delete(sender)
    db.flush()


def ensure_known_senders(db: Session, organization_id: str) -> None:
    for item in KNOWN_SENDERS:
        e164, _iso, error = normalize_phone(item["phone"])
        if error or not e164:
            continue
        existing = (
            db.query(CommSender)
            .filter(CommSender.organization_id == organization_id, CommSender.phone_e164 == e164)
            .first()
        )
        if existing:
            if not existing.display_name:
                existing.display_name = item["name"]
            if item["phone_number_id"]:
                existing.phone_number_id = item["phone_number_id"]
            continue
        db.add(
            CommSender(
                organization_id=organization_id,
                provider="direct_meta",
                phone_e164=e164,
                phone_number_id=item["phone_number_id"],
                display_name=item["name"],
                status="pending",
                quality="UNKNOWN",
            )
        )
    db.flush()


def ensure_rate_cards(db: Session) -> None:
    existing = db.query(CommRateCard).count()
    if existing:
        return
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    for category, rate, rules in PLANNING_RATES:
        db.add(
            CommRateCard(
                market="IQ",
                category=category,
                currency="USD",
                unit_rate_decimal=rate,
                valid_from=start,
                valid_to=None,
                rate_source="planning-snapshot-not-an-invoice",
                source_version="2026-10-10",
                rules_json=rules,
            )
        )
    db.flush()


def ensure_membership(db: Session, user: User) -> CommMembership | None:
    org, _unit = ensure_foundation(db)
    row = (
        db.query(CommMembership)
        .filter(CommMembership.organization_id == org.id, CommMembership.user_id == user.id)
        .first()
    )
    if row:
        return row if row.active else None
    if user.role == UserRole.SUPER_ADMIN.value:
        row = CommMembership(organization_id=org.id, user_id=user.id, role="super_admin", active=True)
        db.add(row)
        db.flush()
        return row
    return None
