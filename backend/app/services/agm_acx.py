"""Art City–owned ACX utility ledger for Graphic Motion jobs (not Nova/Alltra)."""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models_agm import AgmAcxReservation, AgmJob


class AcxError(Exception):
    def __init__(self, message: str, code: str = "AGM_ACX_RESERVATION_FAILED") -> None:
        super().__init__(message)
        self.code = code


def quote_render(*, job_kind: str, duration_ms: int, profile: Optional[dict] = None) -> dict:
    profile = profile or {}
    base = 1.0 if job_kind == "preview" else 5.0
    seconds = max(duration_ms / 1000.0, 0.5)
    codec = (profile.get("codec") or "h264").lower()
    mult = 2.0 if "prores" in codec or codec == "exr" else 1.0
    amount = round(base * seconds * mult, 4)
    return {
        "quote_id": f"acx_{uuid4().hex[:16]}",
        "amount": amount,
        "currency": "ACX",
        "job_kind": job_kind,
    }


def reserve(db: Session, *, job: AgmJob, quote_id: str, amount: float) -> AgmAcxReservation:
    existing = db.query(AgmAcxReservation).filter(AgmAcxReservation.job_id == job.id).first()
    if existing:
        # Idempotent: same job never double-reserves
        return existing
    if amount < 0:
        raise AcxError("invalid reserve amount")
    row = AgmAcxReservation(
        job_id=job.id,
        quote_id=quote_id,
        project_id=job.project_id,
        reserved_amount=amount,
        settled_amount=0.0,
        status="reserved",
        metadata_json={"engine": "artcity-acx"},
    )
    db.add(row)
    db.flush()
    job.acx_quote_id = quote_id
    job.acx_reservation_id = row.id
    db.add(job)
    return row


def settle(db: Session, *, job_id: str, actual_amount: Optional[float] = None) -> AgmAcxReservation:
    row = db.query(AgmAcxReservation).filter(AgmAcxReservation.job_id == job_id).first()
    if not row:
        raise AcxError("reservation not found")
    if row.status == "settled":
        return row
    if row.status == "reversed":
        raise AcxError("cannot settle reversed reservation")
    row.settled_amount = float(actual_amount if actual_amount is not None else row.reserved_amount)
    row.status = "settled"
    db.add(row)
    return row


def reverse(db: Session, *, job_id: str) -> Optional[AgmAcxReservation]:
    row = db.query(AgmAcxReservation).filter(AgmAcxReservation.job_id == job_id).first()
    if not row:
        return None
    if row.status == "settled":
        # Already settled — no reverse double-charge path
        return row
    if row.status == "reversed":
        return row
    row.status = "reversed"
    row.settled_amount = 0.0
    db.add(row)
    return row
