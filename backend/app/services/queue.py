"""Redis list queue for Art City inference jobs."""

from __future__ import annotations

import json
from typing import Optional

from redis import Redis

from app.core.config import get_settings

QUEUE_KEY = "artcity:generation:queue"
EDIT_QUEUE_KEY = "artcity:edit:queue"


def _redis() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


def enqueue_job(job_id: str) -> None:
    _redis().lpush(QUEUE_KEY, json.dumps({"job_id": job_id}))


def dequeue_job(timeout: int = 5) -> Optional[str]:
    item = _redis().brpop(QUEUE_KEY, timeout=timeout)
    if not item:
        return None
    _, raw = item
    data = json.loads(raw)
    return data.get("job_id")


def enqueue_edit_job(job_type: str, job_id: str) -> None:
    _redis().lpush(EDIT_QUEUE_KEY, json.dumps({"type": job_type, "job_id": job_id}))


def dequeue_edit_job(timeout: int = 5) -> Optional[dict[str, str]]:
    item = _redis().brpop(EDIT_QUEUE_KEY, timeout=timeout)
    if not item:
        return None
    _, raw = item
    data = json.loads(raw)
    job_type = data.get("type")
    job_id = data.get("job_id")
    if not job_type or not job_id:
        return None
    return {"type": str(job_type), "job_id": str(job_id)}
