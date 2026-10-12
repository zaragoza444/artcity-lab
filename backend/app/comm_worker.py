"""Drain the communications outbox. Kept separate from the media worker."""

from __future__ import annotations

import time

from app.communications.dispatch import process_due
from app.communications.foundation import utcnow
from app.communications.gateway import get_gateway
from app.core.db import SessionLocal
from app.models_comm import CommOutbox


def run_once() -> int:
    db = SessionLocal()
    try:
        handled = process_due(db, get_gateway())
        due_imports = (
            db.query(CommOutbox)
            .filter(CommOutbox.job_kind == "import", CommOutbox.status == "pending", CommOutbox.next_attempt_at <= utcnow())
            .all()
        )
        for job in due_imports:
            job.status = "done"
            job.updated_at = utcnow()
        db.commit()
        return handled
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_worker() -> None:
    print("AC Communications worker listening for dispatch jobs…")
    while True:
        try:
            handled = run_once()
        except Exception as exc:  # noqa: BLE001
            print(f"communications worker error: {exc.__class__.__name__}")
            handled = 0
        time.sleep(0.2 if handled else 1.0)


if __name__ == "__main__":
    run_worker()
