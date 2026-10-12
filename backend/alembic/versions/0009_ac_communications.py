"""Alembic 0009 — AC Communications.

Revision ID: 0009_ac_communications
Revises: 0008_graphic_motion
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
from sqlalchemy import insert

from app.models_comm import (
    CommAudienceSnapshot,
    CommAuditLog,
    CommBusinessUnit,
    CommCampaign,
    CommConsent,
    CommContact,
    CommConversation,
    CommCostLedger,
    CommImportJob,
    CommMembership,
    CommMessage,
    CommOrganization,
    CommOutbox,
    CommRateCard,
    CommRecipient,
    CommSegment,
    CommSendAttempt,
    CommSender,
    CommSuppression,
    CommTemplate,
    CommWebhookEvent,
)

revision: str = "0009_ac_communications"
down_revision: Union[str, None] = "0008_graphic_motion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    CommOrganization,
    CommBusinessUnit,
    CommMembership,
    CommSender,
    CommContact,
    CommConsent,
    CommSuppression,
    CommImportJob,
    CommSegment,
    CommTemplate,
    CommAudienceSnapshot,
    CommCampaign,
    CommRecipient,
    CommMessage,
    CommSendAttempt,
    CommWebhookEvent,
    CommConversation,
    CommRateCard,
    CommCostLedger,
    CommAuditLog,
    CommOutbox,
]


def upgrade() -> None:
    bind = op.get_bind()
    for model in _TABLES:
        model.__table__.create(bind)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_comm_contact_name_trgm ON comm_contacts USING gin (display_name gin_trgm_ops)"
    )
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    rows = []
    for category, rate, rules in (
        ("marketing", "0.034100", {}),
        ("utility", "0.007900", {}),
        ("authentication", "0.007900", {}),
        ("service", "0.007900", {"monthly_free_allowance": 1000}),
    ):
        rows.append(
            {
                "id": str(uuid4()),
                "market": "IQ",
                "category": category,
                "currency": "USD",
                "unit_rate_decimal": Decimal(rate),
                "valid_from": start,
                "valid_to": None,
                "rate_source": "planning-snapshot-not-an-invoice",
                "source_version": "2026-10-10",
                "rules_json": rules,
            }
        )
    op.get_bind().execute(insert(CommRateCard.__table__), rows)


def downgrade() -> None:
    bind = op.get_bind()
    for model in reversed(_TABLES):
        model.__table__.drop(bind)
