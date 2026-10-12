"""Effective-dated rates and append-only cost ledger."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.communications.audit import audit
from app.communications.foundation import utcnow
from app.communications.money import from_micros, to_micros
from app.core.config import get_settings
from app.models_comm import CommCostLedger, CommMessage, CommRateCard, CommSender


def rate_for(db: Session, market: str, category: str, at: datetime | None = None) -> CommRateCard | None:
    moment = at or utcnow()
    rows = (
        db.query(CommRateCard)
        .filter(CommRateCard.market == market, CommRateCard.category == category, CommRateCard.valid_from <= moment)
        .all()
    )
    open_rows = [row for row in rows if row.valid_to is None or row.valid_to > moment]
    open_rows.sort(key=lambda row: row.valid_from, reverse=True)
    return open_rows[0] if open_rows else None


def add_rate_card(
    db: Session,
    *,
    market: str,
    category: str,
    unit_rate: str,
    actor_id: str | None,
    source: str,
) -> CommRateCard:
    moment = utcnow()
    current = rate_for(db, market, category, moment)
    if current is not None:
        current.valid_to = moment
    card = CommRateCard(
        market=market,
        category=category,
        currency="USD",
        unit_rate_decimal=Decimal(unit_rate),
        valid_from=moment,
        rate_source=source,
        source_version=moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
        rules_json={"monthly_free_allowance": get_settings().comm_service_allowance_per_number} if category == "service" else {},
    )
    db.add(card)
    db.flush()
    audit(db, actor_id=actor_id, action="billing.rate_add", object_type="rate_card", object_id=card.id, metadata={"market": market, "category": category})
    return card


def record_provisional(
    db: Session,
    *,
    message: CommMessage,
    campaign_id: str | None,
    market: str,
    category: str,
    sender_id: str,
) -> CommCostLedger | None:
    existing = (
        db.query(CommCostLedger)
        .filter(CommCostLedger.message_id == message.id, CommCostLedger.entry_type == "provisional")
        .first()
    )
    if existing:
        return existing
    moment = message.delivered_at or utcnow()
    card = rate_for(db, market or "IQ", category, moment)
    if card is None:
        return None
    amount = to_micros(card.unit_rate_decimal)
    note = None
    if category == "service":
        allowance = int((card.rules_json or {}).get("monthly_free_allowance") or get_settings().comm_service_allowance_per_number)
        month_start = datetime(moment.year, moment.month, 1, tzinfo=timezone.utc)
        used = (
            db.query(CommCostLedger)
            .join(CommMessage, CommMessage.id == CommCostLedger.message_id)
            .filter(
                CommCostLedger.entry_type == "provisional",
                CommCostLedger.note.like("service:%"),
                CommMessage.sender_id == sender_id,
                CommCostLedger.created_at >= month_start,
            )
            .count()
        )
        note = f"service:{sender_id}"
        if used < allowance:
            amount = 0
    row = CommCostLedger(
        message_id=message.id,
        campaign_id=campaign_id,
        amount_micros=amount,
        currency="USD",
        entry_type="provisional",
        status="posted",
        rate_card_id=card.id,
        note=note,
    )
    db.add(row)
    db.flush()
    return row


def reconcile_invoice(
    db: Session,
    *,
    external_invoice_ref: str,
    amount_usd: str,
    actor_id: str | None,
    campaign_id: str | None = None,
) -> dict:
    existing = (
        db.query(CommCostLedger)
        .filter(
            CommCostLedger.external_invoice_ref == external_invoice_ref,
            CommCostLedger.entry_type == "invoice_adjustment",
        )
        .first()
    )
    if existing:
        return {"id": existing.id, "idempotent": True, "adjustment_micros": existing.amount_micros}
    query = db.query(CommCostLedger).filter(CommCostLedger.entry_type == "provisional")
    if campaign_id:
        query = query.filter(CommCostLedger.campaign_id == campaign_id)
    provisional = sum(row.amount_micros for row in query.all())
    target = to_micros(amount_usd)
    delta = target - provisional
    row = CommCostLedger(
        campaign_id=campaign_id,
        amount_micros=delta,
        currency="USD",
        entry_type="invoice_adjustment",
        status="posted",
        external_invoice_ref=external_invoice_ref,
        note="invoice_delta",
    )
    db.add(row)
    db.flush()
    audit(
        db,
        actor_id=actor_id,
        action="billing.reconcile",
        object_type="invoice",
        object_id=external_invoice_ref,
        metadata={"delta_micros": delta, "provisional_micros": provisional},
    )
    return {
        "id": row.id,
        "idempotent": False,
        "provisional_usd": f"{from_micros(provisional):.2f}",
        "invoice_usd": f"{from_micros(target):.2f}",
        "adjustment_micros": delta,
        "adjustment_usd": f"{from_micros(delta):.2f}",
    }


def sender_for_message(db: Session, message: CommMessage) -> CommSender | None:
    return db.get(CommSender, message.sender_id)
