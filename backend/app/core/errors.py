"""Production-friendly API error handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, StatementError


def _format_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for err in errors:
        loc = [str(x) for x in err.get("loc", ()) if x != "body"]
        field = ".".join(loc) or "request"
        msg = err.get("msg", "Invalid value")
        # Humanize common pydantic messages
        if "Field required" in msg:
            msg = f"{field} is required"
        elif "string_too_short" in str(err.get("type")):
            msg = f"{field} is too short"
        out.append({"field": field, "message": msg, "type": err.get("type")})
    return out


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        items = _format_validation_errors(exc.errors())
        summary = "; ".join(f"{i['field']}: {i['message']}" for i in items[:5])
        return JSONResponse(
            status_code=422,
            content={
                "detail": items,
                "message": summary or "Validation failed",
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(DataError)
    async def data_error_handler(request: Request, exc: DataError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": [{"field": "id", "message": "Invalid id format (expected UUID)"}],
                "message": "Invalid id format (expected UUID)",
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(StatementError)
    async def statement_error_handler(request: Request, exc: StatementError):
        text = str(exc.orig if hasattr(exc, "orig") else exc)
        if "uuid" in text.lower() or "invalid input" in text.lower():
            return JSONResponse(
                status_code=422,
                content={
                    "detail": [{"field": "id", "message": "Invalid id format (expected UUID)"}],
                    "message": "Invalid id format (expected UUID)",
                    "path": str(request.url.path),
                },
            )
        return JSONResponse(
            status_code=400,
            content={"detail": "Database statement error", "message": text[:200], "path": str(request.url.path)},
        )
