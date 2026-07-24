"""Seed Art City Edit plans and internal Art City Group organisation."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import User
from app.services.edit_access import ensure_default_plans, seed_internal_art_city


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.default_admin_email).first()
        if not admin:
            admin = User(
                id=str(uuid4()),
                email=settings.default_admin_email,
                full_name="Art City Admin",
                password_hash=hash_password(settings.default_admin_password),
                role="super_admin",
                is_active=True,
                account_state="active",
            )
            db.add(admin)
            db.flush()
            print(f"Created admin {admin.email}")
        else:
            print(f"Admin exists {admin.email}")

        plans = ensure_default_plans(db)
        print(f"Plans ready: {', '.join(p.code for p in plans)}")

        org = seed_internal_art_city(db, admin)
        db.commit()
        print(f"Internal org ready: {org.display_name} ({org.id}) status={org.status}")
        print("Art City Edit seed complete")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
