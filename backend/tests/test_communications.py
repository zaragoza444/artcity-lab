"""AC Communications acceptance coverage for blueprint cases T01–T20."""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite://"

import csv
import hashlib
import hmac
import io
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.communications.billing import reconcile_invoice, record_provisional
from app.communications.campaigns import (
    approve_campaign,
    in_quiet_hours,
    preview,
    schedule_campaign,
    submit_campaign,
)
from app.communications.crm import exclusion_reason, has_verified_consent, import_contacts, suppress_contact
from app.communications.dispatch import process_due
from app.communications.foundation import ensure_foundation
from app.communications.gateway import CoexistenceBspAdapter, DirectMetaAdapter, FakeMetaAdapter, ProviderError
from app.communications.inbox import send_reply, upsert_conversation
from app.communications.money import to_micros
from app.communications.phones import csv_safe, normalize_phone
from app.communications.rbac import require_membership
from app.communications.webhooks import advance_status, apply_webhook_payload, ingest_webhook
from app.core.config import get_settings
from app.core.db import Base
from app.core.security import hash_password
from app.models import User
from app.models_comm import (
    CommCampaign,
    CommContact,
    CommCostLedger,
    CommMembership,
    CommMessage,
    CommRateCard,
    CommRecipient,
    CommSender,
    CommSuppression,
    CommTemplate,
)


@compiles(JSONB, "sqlite")
def _compile_jsonb(type_, compiler, **kw):  # noqa: ANN001
    return "JSON"


@compiles(PGUUID, "sqlite")
def _compile_uuid(type_, compiler, **kw):  # noqa: ANN001
    return "CHAR(36)"


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    import app.models  # noqa: F401
    import app.models_comm as models_comm

    tables = [User.__table__]
    for obj in vars(models_comm).values():
        table = getattr(obj, "__table__", None)
        if table is not None and str(table.name).startswith("comm_"):
            tables.append(table)
    Base.metadata.create_all(engine, tables=tables)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    settings = get_settings()
    settings.comm_process_inline = False
    settings.comm_live_send_enabled = False
    settings.comm_allow_unverified_consent = False
    settings.comm_require_separate_approval = True
    settings.comm_require_valid_webhook_signature = True
    settings.comm_enable_unknown_outcome_auto_retry = False
    settings.meta_app_secret = "test-secret"
    settings.meta_verify_token = "verify-me"
    settings.comm_default_max_spend_usd = "100.00"
    settings.comm_send_worker_initial_mps = 50
    settings.comm_marketing_cooldown_hours = 72
    yield session
    session.close()


def _user(db, role: str) -> User:
    user = User(
        id=str(uuid4()),
        email=f"{role}-{uuid4().hex[:8]}@artcity.ai",
        full_name=role,
        password_hash=hash_password("test-password-123"),
        role="viewer",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _world(db):
    org, unit = ensure_foundation(db)
    owner = _user(db, "owner")
    approver = _user(db, "approver")
    operator = _user(db, "operator")
    db.add(CommMembership(organization_id=org.id, user_id=owner.id, role="marketing_manager", active=True))
    db.add(CommMembership(organization_id=org.id, user_id=approver.id, role="campaign_approver", active=True))
    db.add(CommMembership(organization_id=org.id, user_id=operator.id, role="operator", active=True))
    e164, _iso, err = normalize_phone("+9647512345678")
    sender = CommSender(
        organization_id=org.id,
        phone_e164=e164 or "+9647512345678",
        display_name="Art City",
        status="connected",
        quality="GREEN",
        waba_id="local",
        limits_snapshot={"unique_recipient_limit": 10000},
    )
    if err:
        sender.phone_e164 = "+9647512345678"
    db.add(sender)
    db.flush()
    template = CommTemplate(
        organization_id=org.id,
        sender_id=sender.id,
        waba_id="local",
        meta_name="art_city_event_invite_en",
        language_code="en_US",
        category="marketing",
        status="approved",
        components_json={"body_param_count": 1, "header_param_count": 0, "button_param_count": 0},
        approved_at=datetime.now(timezone.utc),
    )
    db.add(template)
    db.flush()
    return {"org": org, "unit": unit, "owner": owner, "approver": approver, "operator": operator, "sender": sender, "template": template}


def _valid_iq(count: int, start: int = 0) -> list[str]:
    found = []
    for offset in range(count):
        e164, iso, err = normalize_phone(f"+96475{start + offset:08d}")
        if err or iso != "IQ":
            raise RuntimeError(f"expected a valid IQ number at offset {start + offset}")
        found.append(e164)
    return found


def _row(phone: str, name: str, *, proof: bool = True, consent: str = "granted") -> dict[str, str]:
    return {
        "phone_number": phone,
        "full_name": name,
        "preferred_language": "ar",
        "city": "Erbil",
        "contact_source": "registration_form",
        "consent_status": consent,
        "consent_timestamp": "2026-10-01T09:00:00+03:00" if proof else "",
        "consent_source": "form_v3" if proof else "",
        "consent_proof_ref": "proof-123" if proof else "",
        "marketing_purpose": "event_updates",
    }


def _csv(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO()
    fieldnames = list(rows[0].keys()) if rows else ["phone_number"]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def _import(db, world, rows: list[dict[str, str]], filename: str = "contacts.csv"):
    return import_contacts(
        db,
        organization_id=world["org"].id,
        business_unit_id=world["unit"].id,
        actor_id=world["owner"].id,
        filename=filename,
        data=_csv(rows),
    )


def _campaign(db, world, budget: str = "10.00") -> CommCampaign:
    campaign = CommCampaign(
        business_unit_id=world["unit"].id,
        sender_id=world["sender"].id,
        template_id=world["template"].id,
        name="Seminar",
        category="marketing",
        state="draft",
        schedule_timezone="Asia/Baghdad",
        quiet_hours_json={"start": "21:00", "end": "09:00"},
        allow_quiet_hours=True,
        parameter_template={"body": ["{{name}}"], "header": [], "buttons": []},
        budget_micros=to_micros(Decimal(budget)),
        buffer_percent=0,
        test_batch_size=5,
        created_by=world["owner"].id,
    )
    db.add(campaign)
    db.flush()
    return campaign


def _ready(db, world, budget: str = "10.00") -> tuple[CommCampaign, FakeMetaAdapter]:
    campaign = _campaign(db, world, budget)
    preview(db, campaign)
    submit_campaign(db, campaign, world["owner"].id)
    approve_campaign(db, campaign, world["approver"].id)
    gateway = FakeMetaAdapter()
    schedule_campaign(db, campaign, world["operator"].id)
    return campaign, gateway


def _deliver(db, provider_message_id: str) -> None:
    apply_webhook_payload(
        db,
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": provider_message_id,
                                        "status": "delivered",
                                        "timestamp": "1792000000",
                                        "pricing": {"billable": True, "category": "marketing"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )


def test_t01_import_counts_are_deterministic(db):
    world = _world(db)
    numbers = _valid_iq(3)
    rows = [
        _row(numbers[0], "A"),
        _row(numbers[1], "B", proof=False),
        _row(numbers[0], "dup"),
        _row("not-a-phone", "bad"),
        _row("=1+1", "formula"),
        _row(numbers[2], "Robert'); DROP TABLE comm_contacts;--"),
    ]
    first = _import(db, world, rows)
    assert first.count_total == 6
    assert first.inserted + first.updated + first.rejected == first.count_total
    assert first.rejections_json["counts"]["duplicate_in_file"] == 1
    assert db.query(CommContact).count() == 3
    big = [_row(f"+100000{i:05d}", f"n{i}", proof=False) for i in range(20000)]
    job = _import(db, world, big, filename="bulk.csv")
    assert job.count_total == 20000
    assert job.inserted + job.updated + job.rejected == 20000


def test_t02_unproven_consent_is_excluded(db):
    world = _world(db)
    number = _valid_iq(1)[0]
    _import(db, world, [_row(number, "Sample", proof=False)])
    contact = db.query(CommContact).one()
    assert not has_verified_consent(db, contact.id, business_unit_id=world["unit"].id, purpose="marketing")
    assert exclusion_reason(db, contact, business_unit_id=world["unit"].id, purpose="marketing", category="marketing") == "no_consent"


def test_t03_opt_out_survives_reimport(db):
    world = _world(db)
    number = _valid_iq(1)[0]
    _import(db, world, [_row(number, "Kept")])
    contact = db.query(CommContact).one()
    suppress_contact(db, contact, reason="stop", actor_id=world["owner"].id, source="test")
    _import(db, world, [_row(number, "Renamed")])
    assert db.query(CommSuppression).filter(CommSuppression.contact_id == contact.id).count() == 1
    assert exclusion_reason(db, contact, business_unit_id=world["unit"].id, purpose="marketing", category="marketing") == "opted_out"


def test_t04_import_keeps_unicode_and_formula_text(db):
    world = _world(db)
    numbers = _valid_iq(2)
    formula = '=HYPERLINK("http://evil")'
    _import(db, world, [_row(numbers[0], formula), _row(numbers[1], "هێمن")])
    stored = db.query(CommContact).filter(CommContact.phone_e164 == numbers[1]).one()
    assert stored.display_name == "هێمن"
    assert csv_safe(formula).startswith("'")
    assert db.query(CommContact).count() == 2


def test_t05_accept_delivery_and_cost_are_distinct(db):
    world = _world(db)
    _import(db, world, [_row(_valid_iq(1)[0], "Guest")])
    campaign, gateway = _ready(db, world)
    assert process_due(db, gateway) == 1
    message = db.query(CommMessage).one()
    assert message.status == "accepted"
    assert db.query(CommCostLedger).count() == 0
    _deliver(db, message.provider_message_id)
    assert message.status == "delivered"
    ledger = db.query(CommCostLedger).one()
    assert ledger.entry_type == "provisional"
    assert ledger.amount_micros == to_micros("0.0341")


def test_t06_preflight_blocks_paused_template_and_missing_variables(db):
    world = _world(db)
    _import(db, world, [_row(_valid_iq(1)[0], "")])
    campaign = _campaign(db, world)
    assert preview(db, campaign)["can_submit"] is False
    world["template"].status = "paused"
    campaign.parameter_template = {"body": ["Hello"], "header": [], "buttons": []}
    db.query(CommContact).one().display_name = "Guest"
    report = preview(db, campaign)
    assert "template_not_approved" in report["blocking_errors"]
    assert world["template"].language_code == "en_US"


def test_t07_duplicate_dispatch_and_webhook_replay(db):
    world = _world(db)
    _import(db, world, [_row(_valid_iq(1)[0], "Guest")])
    _campaign_row, gateway = _ready(db, world)
    process_due(db, gateway)
    process_due(db, gateway)
    assert len(gateway.sent) == 1
    message = db.query(CommMessage).one()
    body = json.dumps(
        {"entry": [{"changes": [{"value": {"statuses": [{"id": message.provider_message_id, "status": "delivered", "timestamp": "1792000001", "pricing": {"billable": True}}]}}]}]}
    ).encode()
    signature = "sha256=" + hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
    first = ingest_webhook(db, raw_body=body, signature=signature)
    second = ingest_webhook(db, raw_body=body, signature=signature)
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert db.query(CommCostLedger).count() == 1


def test_t08_timeout_is_quarantined(db):
    world = _world(db)
    _import(db, world, [_row(_valid_iq(1)[0], "Guest")])
    _campaign_row, gateway = _ready(db, world)
    gateway.mode = "timeout"
    process_due(db, gateway)
    process_due(db, gateway)
    recipient = db.query(CommRecipient).one()
    assert recipient.status == "quarantined"
    assert gateway.sent == []


def test_t09_capacity_limit_is_shared(db):
    world = _world(db)
    numbers = _valid_iq(3)
    _import(db, world, [_row(number, f"P{i}") for i, number in enumerate(numbers)])
    world["sender"].limits_snapshot = {"unique_recipient_limit": 2}
    _campaign_row, gateway = _ready(db, world, "10")
    process_due(db, gateway, limit=10)
    assert len(gateway.sent) == 2
    assert db.query(CommRecipient).filter(CommRecipient.status == "queued").count() == 1


def test_t10_mps_throttles(db):
    world = _world(db)
    get_settings().comm_send_worker_initial_mps = 1
    numbers = _valid_iq(2)
    _import(db, world, [_row(number, f"P{i}") for i, number in enumerate(numbers)])
    _campaign_row, gateway = _ready(db, world)
    process_due(db, gateway, limit=10)
    assert len(gateway.sent) == 1


def test_t11_budget_stops_before_overspend(db):
    world = _world(db)
    get_settings().comm_default_max_spend_usd = "0.0341"
    numbers = _valid_iq(2)
    _import(db, world, [_row(number, f"P{i}") for i, number in enumerate(numbers)])
    campaign, gateway = _ready(db, world, "10")
    process_due(db, gateway, limit=10)
    assert len(gateway.sent) == 1
    db.refresh(campaign)
    assert campaign.pause_reason == "daily_spend_cap"
    assert campaign.consumed_micros == to_micros("0.0341")


def test_t12_pause_withdraws_unsent_only(db):
    world = _world(db)
    numbers = _valid_iq(2)
    _import(db, world, [_row(number, f"P{i}") for i, number in enumerate(numbers)])
    campaign, gateway = _ready(db, world)
    process_due(db, gateway, limit=1)
    from app.communications.campaigns import _withdraw_unsent, transition

    transition(campaign, "paused")
    _withdraw_unsent(db, campaign)
    assert db.query(CommRecipient).filter(CommRecipient.status == "accepted").count() == 1
    assert db.query(CommRecipient).filter(CommRecipient.status == "cancelled").count() == 1


def test_t13_bad_signature_rejected(db):
    bad = ingest_webhook(db, raw_body=b'{"entry":[]}', signature="sha256=deadbeef")
    assert bad["accepted"] is False
    assert bad["reason"] == "bad_signature"


def test_t14_service_window_blocks_late_reply(db):
    world = _world(db)
    _import(db, world, [_row(_valid_iq(1)[0], "Guest")])
    contact = db.query(CommContact).one()
    conversation = upsert_conversation(db, world["sender"], contact, datetime.now(timezone.utc))
    gateway = FakeMetaAdapter()
    message = send_reply(db, conversation, actor_id=world["operator"].id, text="Hello", gateway=gateway)
    assert message.status == "accepted"
    conversation.service_window_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    with pytest.raises(Exception) as exc:
        send_reply(db, conversation, actor_id=world["operator"].id, text="Too late", gateway=gateway)
    assert getattr(exc.value, "status_code", None) == 409


def test_t15_service_allowance(db):
    world = _world(db)
    card = db.query(CommRateCard).filter(CommRateCard.category == "service").one()
    card.rules_json = {"monthly_free_allowance": 1}
    e164, iso, err = normalize_phone("+9647511111111")
    contact = CommContact(
        organization_id=world["org"].id,
        phone_e164=e164 or "+9647511111111",
        country_iso=iso or "IQ",
        display_name="S",
        tags=[],
    )
    db.add(contact)
    db.flush()
    now = datetime.now(timezone.utc)
    first = CommMessage(sender_id=world["sender"].id, contact_id=contact.id, direction="inbound", kind="session", status="delivered", delivered_at=now)
    second = CommMessage(sender_id=world["sender"].id, contact_id=contact.id, direction="inbound", kind="session", status="delivered", delivered_at=now)
    db.add_all([first, second])
    db.flush()
    free = record_provisional(db, message=first, campaign_id=None, market="IQ", category="service", sender_id=world["sender"].id)
    paid = record_provisional(db, message=second, campaign_id=None, market="IQ", category="service", sender_id=world["sender"].id)
    assert free is not None and free.amount_micros == 0
    assert paid is not None and paid.amount_micros == to_micros("0.0079")
    assert err in {"", "invalid_phone"}


def test_t16_operator_cannot_approve_or_read_tokens(db):
    world = _world(db)
    membership = db.query(CommMembership).filter(CommMembership.user_id == world["operator"].id).one()
    with pytest.raises(Exception) as exc:
        require_membership(membership, "campaigns.approve")
    assert exc.value.status_code == 403
    with pytest.raises(Exception):
        require_membership(membership, "admin.secrets")
    _import(db, world, [_row(_valid_iq(1)[0], "Guest")])
    campaign = _campaign(db, world)
    preview(db, campaign)
    submit_campaign(db, campaign, world["owner"].id)
    with pytest.raises(Exception) as own:
        approve_campaign(db, campaign, world["owner"].id)
    assert own.value.status_code == 403


def test_t17_preview_quotes_by_market(db):
    world = _world(db)
    numbers = _valid_iq(2)
    _import(db, world, [_row(numbers[0], "A"), _row(numbers[1], "B", proof=False)])
    report = preview(db, _campaign(db, world))
    assert report["selected"] == 2
    assert report["eligible"] == 1
    assert report["excluded"]["no_consent"] == 1
    assert report["by_market"][0]["market"] == "IQ"
    assert report["quote_usd"] == "0.03"


def test_t18_invoice_adjustment_does_not_overwrite(db):
    world = _world(db)
    _import(db, world, [_row(_valid_iq(1)[0], "Guest")])
    campaign, gateway = _ready(db, world)
    process_due(db, gateway)
    message = db.query(CommMessage).one()
    _deliver(db, message.provider_message_id)
    original = db.query(CommCostLedger).one()
    original_amount = original.amount_micros
    result = reconcile_invoice(db, external_invoice_ref="INV-1", amount_usd="1.00", actor_id=world["owner"].id, campaign_id=campaign.id)
    again = reconcile_invoice(db, external_invoice_ref="INV-1", amount_usd="9.00", actor_id=world["owner"].id, campaign_id=campaign.id)
    db.refresh(original)
    assert original.amount_micros == original_amount
    assert result["idempotent"] is False
    assert again["idempotent"] is True


def test_t19_logical_restore_round_trip(db):
    world = _world(db)
    _import(db, world, [_row(_valid_iq(1)[0], "Guest")])
    contact = db.query(CommContact).one()
    suppress_contact(db, contact, reason="restore", actor_id=world["owner"].id, source="test")
    snapshot = [{"contact_id": row.contact_id, "reason": row.reason} for row in db.query(CommSuppression).all()]
    db.query(CommSuppression).delete()
    db.flush()
    for row in snapshot:
        db.add(CommSuppression(contact_id=row["contact_id"], scope="global", reason=row["reason"]))
    db.flush()
    assert db.query(CommSuppression).count() == 1


def test_t20_pilot_reply_optout_and_quality_pause(db):
    world = _world(db)
    numbers = _valid_iq(2)
    _import(db, world, [_row(number, f"P{i}") for i, number in enumerate(numbers)])
    campaign, gateway = _ready(db, world)
    process_due(db, gateway, limit=1)
    message = db.query(CommMessage).one()
    apply_webhook_payload(
        db,
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": numbers[0].lstrip("+"),
                                        "id": "wamid.IN",
                                        "timestamp": "1760000100",
                                        "type": "text",
                                        "text": {"body": "STOP"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )
    assert db.query(CommSuppression).count() >= 1
    apply_webhook_payload(db, {"entry": [{"changes": [{"field": "phone_number_quality_update", "value": {"quality_rating": "RED"}}]}]})
    db.refresh(campaign)
    assert campaign.state == "paused"
    assert message.provider_message_id


def test_quiet_hours_and_monotonic_status():
    quiet = datetime(2026, 10, 12, 19, 30, tzinfo=timezone.utc)
    daytime = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
    assert in_quiet_hours(quiet, "21:00", "09:00", "Asia/Baghdad") is True
    assert in_quiet_hours(daytime, "21:00", "09:00", "Asia/Baghdad") is False
    assert advance_status("delivered", "sent") == "delivered"
    assert advance_status("read", "failed") == "read"
    assert advance_status("accepted", "delivered") == "delivered"


def test_direct_adapter_posts_template_and_coexistence_is_closed():
    settings = get_settings()
    settings.comm_live_send_enabled = True
    settings.meta_access_token = "server-token"
    settings.graph_api_version = "v23.0"
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json={"messages": [{"id": "wamid.LIVE"}]})

    try:
        adapter = DirectMetaAdapter(
            client=httpx.Client(transport=httpx.MockTransport(handler), headers={"Authorization": "Bearer server-token"})
        )
        result = adapter.send_template(
            "sender",
            "+9647500000000",
            {"name": "art_city_event_invite_en", "language_code": "en_US"},
            [{"type": "body", "parameters": [{"type": "text", "text": "Ada"}]}],
            {"phone_number_id": "PHONE123"},
        )
        assert result.provider_message_id == "wamid.LIVE"
        assert seen["url"].endswith("/v23.0/PHONE123/messages")
        assert seen["body"]["type"] == "template"
        assert "server-token" not in json.dumps(seen["body"])
        with pytest.raises(ProviderError):
            CoexistenceBspAdapter().send_template()
    finally:
        settings.comm_live_send_enabled = False


def test_local_trunk_prefix_uses_library():
    _e164, iso, err = normalize_phone("07501234567")
    if not err:
        assert iso == "IQ"
    else:
        assert err == "invalid_phone"
