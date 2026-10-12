"""Inbox, service window, and opt-out keywords."""

from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.communications.crm import suppress_contact
from app.communications.foundation import utcnow
from app.communications.gateway import MessagingGateway
from app.communications.phones import phones_equal
from app.core.config import get_settings
from app.models_comm import CommContact, CommConversation, CommMessage, CommSender


def opt_out_keywords() -> set[str]:
    return {part.strip().casefold() for part in get_settings().comm_optout_keywords.split(",") if part.strip()}


def is_opt_out(text: str | None) -> bool:
    if not text:
        return False
    token = text.strip().casefold()
    keywords = opt_out_keywords()
    if token in keywords:
        return True
    first = token.split()[0] if token.split() else ""
    return first in keywords


def upsert_conversation(db: Session, sender: CommSender, contact: CommContact, when) -> CommConversation:
    row = (
        db.query(CommConversation)
        .filter(CommConversation.sender_id == sender.id, CommConversation.contact_id == contact.id)
        .first()
    )
    if row is None:
        row = CommConversation(sender_id=sender.id, contact_id=contact.id, state="open", unread_count=0)
        db.add(row)
    row.last_user_message_at = when
    row.service_window_expires_at = when + timedelta(hours=24)
    row.state = "open"
    row.unread_count = (row.unread_count or 0) + 1
    row.updated_at = utcnow()
    db.flush()
    return row


def find_contact_by_phone(db: Session, organization_id: str, phone: str) -> CommContact | None:
    contacts = db.query(CommContact).filter(CommContact.organization_id == organization_id, CommContact.deleted_at.is_(None)).all()
    for contact in contacts:
        if phones_equal(contact.phone_e164, phone):
            return contact
    return None


def window_open(conversation: CommConversation) -> bool:
    if conversation.service_window_expires_at is None:
        return False
    return conversation.service_window_expires_at > utcnow()


def send_reply(
    db: Session,
    conversation: CommConversation,
    *,
    actor_id: str,
    text: str,
    gateway: MessagingGateway,
) -> CommMessage:
    if not window_open(conversation):
        raise HTTPException(status_code=409, detail="Service window is closed. Use an approved template.")
    contact = db.get(CommContact, conversation.contact_id)
    sender = db.get(CommSender, conversation.sender_id)
    if contact is None or sender is None:
        raise HTTPException(status_code=404, detail="Conversation is missing a party")
    result = gateway.send_session_message(
        sender.id,
        contact.phone_e164,
        "text",
        {"text": text, "phone_number_id": sender.phone_number_id},
    )
    message = CommMessage(
        sender_id=sender.id,
        contact_id=contact.id,
        provider_message_id=result.provider_message_id,
        direction="outbound",
        kind="session",
        status="accepted",
        accepted_at=utcnow(),
        body_text=text,
        provider_metadata={"actor_id": actor_id},
    )
    db.add(message)
    conversation.unread_count = 0
    conversation.updated_at = utcnow()
    db.flush()
    return message


def record_opt_out(db: Session, contact: CommContact, *, actor_id: str | None, source: str, evidence: str | None) -> None:
    suppress_contact(db, contact, reason=f"opt_out:{source}"[:255], actor_id=actor_id, source=source)
    if evidence:
        db.add(
            CommMessage(
                sender_id=_any_sender_id(db, contact),
                contact_id=contact.id,
                direction="inbound",
                kind="opt_out_evidence",
                status="received",
                body_text=evidence[:1000],
            )
        )


def _any_sender_id(db: Session, contact: CommContact) -> str:
    sender = db.query(CommSender).filter(CommSender.organization_id == contact.organization_id).first()
    if sender is None:
        raise HTTPException(status_code=409, detail="No sender is configured")
    return sender.id
