"""Art City inference worker — processes Model Gateway queue from Redis."""

from __future__ import annotations

import time

from app.core.db import SessionLocal
from app.services.gateway import process_generation_job
from app.services.queue import dequeue_job


def run_worker() -> None:
    print("Art City worker listening on Redis queue…")
    while True:
        job_id = dequeue_job(timeout=5)
        if not job_id:
            continue
        db = SessionLocal()
        try:
            job = process_generation_job(db, job_id)
            print(f"processed {job_id} → {job.status}")
        except Exception as exc:  # noqa: BLE001
            print(f"failed {job_id}: {exc}")
        finally:
            db.close()
        time.sleep(0.05)


if __name__ == "__main__":
    run_worker()
