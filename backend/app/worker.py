"""Art City inference worker — processes Model Gateway and Edit queues from Redis."""

from __future__ import annotations

import time

from app.core.db import SessionLocal
from app.services.agm_render import process_agm_job
from app.services.edit_media import process_analysis_job
from app.services.edit_render import process_render_job
from app.services.gateway import process_generation_job
from app.services.queue import dequeue_agm_job, dequeue_edit_job, dequeue_job


def _process_edit_item(item: dict[str, str]) -> None:
    job_type = item.get("type")
    job_id = item.get("job_id")
    if not job_type or not job_id:
        return
    db = SessionLocal()
    try:
        if job_type == "analysis":
            job = process_analysis_job(db, job_id)
            print(f"edit analysis {job_id} → {job.state}")
        elif job_type == "render":
            job = process_render_job(db, job_id)
            print(f"edit render {job_id} → {job.state}")
        else:
            print(f"unknown edit job type {job_type} for {job_id}")
            return
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"edit job failed {job_type}/{job_id}: {exc}")
    finally:
        db.close()


def run_worker() -> None:
    print("Art City worker listening on Redis generation + edit + AGM queues…")
    while True:
        job_id = dequeue_job(timeout=5)
        if job_id:
            db = SessionLocal()
            try:
                job = process_generation_job(db, job_id)
                print(f"processed {job_id} → {job.status}")
            except Exception as exc:  # noqa: BLE001
                print(f"failed {job_id}: {exc}")
            finally:
                db.close()
            time.sleep(0.05)
            continue

        edit_item = dequeue_edit_job(timeout=1)
        if edit_item:
            _process_edit_item(edit_item)
            time.sleep(0.05)
            continue

        agm_id = dequeue_agm_job(timeout=1)
        if agm_id:
            db = SessionLocal()
            try:
                job = process_agm_job(db, agm_id)
                db.commit()
                print(f"agm {agm_id} → {job.status}")
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                print(f"agm job failed {agm_id}: {exc}")
            finally:
                db.close()
            time.sleep(0.05)
            continue

        time.sleep(0.05)


if __name__ == "__main__":
    run_worker()
