"""Redis list queue for Art City inference jobs."""

from __future__ import annotations

import json
from typing import Optional

from redis import Redis

from app.core.config import get_settings

QUEUE_KEY = "artcity:generation:queue"


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
