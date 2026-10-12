"""Currency helpers. Ledger amounts are integer USD micros."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

MICRO = Decimal("1000000")


def to_micros(amount: Decimal | str | int | float) -> int:
    dec = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    return int((dec * MICRO).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_micros(micros: int) -> Decimal:
    return (Decimal(int(micros)) / MICRO).quantize(Decimal("0.000001"))


def format_usd(micros: int) -> str:
    return f"{from_micros(micros):.2f}"
