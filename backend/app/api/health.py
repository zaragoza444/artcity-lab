from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import HealthOut
from app.core.config import get_settings
from app.core.db import get_db
from app.services.storage import get_storage

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)) -> HealthOut:
    settings = get_settings()

    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "error"

    redis_status = "ok"
    try:
        Redis.from_url(settings.redis_url).ping()
    except Exception:
        redis_status = "error"

    minio_status = "ok" if get_storage().ping() else "error"

    overall = "ok" if all(s == "ok" for s in (database, redis_status, minio_status)) else "degraded"
    return HealthOut(
        status=overall,
        database=database,
        redis=redis_status,
        minio=minio_status,
    )
