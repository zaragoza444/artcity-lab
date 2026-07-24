"""Customer signup fields: phone + verification tokens.

Revision ID: 0005_customer_signup
Revises: 0004_art_city_edit
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_customer_signup"
down_revision: Union[str, None] = "0004_art_city_edit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("email_verify_token", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("phone_verify_code", sa.String(16), nullable=True))
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_column("users", "phone_verify_code")
    op.drop_column("users", "email_verify_token")
    op.drop_column("users", "phone_verified_at")
    op.drop_column("users", "phone_number")
