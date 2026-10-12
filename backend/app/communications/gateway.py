"""Provider boundary. Direct Meta is canonical. Coexistence stays disabled until Art City records that decision."""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

import httpx

from app.core.config import get_settings

log = logging.getLogger("artcity.communications.gateway")


class UnknownOutcome(Exception):
    """The provider may have accepted the message. Do not resend."""


class ProviderError(Exception):
    def __init__(self, message: str, *, retryable: bool = False, http_status: int | None = None, code: str | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.http_status = http_status
        self.code = code


@dataclass
class SendResult:
    provider_message_id: str | None
    http_status: int
    error_code: str | None = None
    retryable: bool = False
    raw_id_only: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalEvent:
    event_type: str
    dedupe_key: str
    provider_message_id: str | None = None
    phone: str | None = None
    timestamp: datetime | None = None
    text: str | None = None
    pricing: dict[str, Any] | None = None
    error_code: str | None = None
    template_name: str | None = None
    template_language: str | None = None
    template_status: str | None = None
    quality: str | None = None
    capability: dict[str, Any] | None = None


def _ts(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def normalize_meta_webhook(payload: dict[str, Any]) -> list[CanonicalEvent]:
    events: list[CanonicalEvent] = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            field_name = change.get("field") or "messages"
            value = change.get("value") or {}
            if field_name == "message_template_status_update":
                name = str(value.get("message_template_name") or "")
                lang = str(value.get("message_template_language") or "")
                status = str(value.get("event") or value.get("message_template_status") or "")
                events.append(
                    CanonicalEvent(
                        event_type="template.status",
                        dedupe_key=f"tpl:{name}:{lang}:{status}",
                        template_name=name,
                        template_language=lang,
                        template_status=status.lower(),
                    )
                )
                continue
            if field_name in {"phone_number_quality_update", "business_capability_update"}:
                quality = value.get("current_limit") or value.get("event") or value.get("quality_rating")
                events.append(
                    CanonicalEvent(
                        event_type="business.capability_update" if "capability" in field_name else "template.quality",
                        dedupe_key=hashlib.sha256(repr(sorted(value.items())).encode()).hexdigest()[:32],
                        quality=str(quality) if quality else None,
                        capability=value if "capability" in field_name else None,
                    )
                )
                continue
            for status in value.get("statuses") or []:
                sid = str(status.get("id") or "")
                state = str(status.get("status") or "")
                stamp = str(status.get("timestamp") or "")
                error_code = None
                errors = status.get("errors") or []
                if errors:
                    error_code = str(errors[0].get("code") or errors[0].get("title") or "failed")
                events.append(
                    CanonicalEvent(
                        event_type=f"message.{state}",
                        dedupe_key=f"status:{sid}:{state}:{stamp}",
                        provider_message_id=sid or None,
                        phone=str(status.get("recipient_id") or "") or None,
                        timestamp=_ts(status.get("timestamp")),
                        pricing=status.get("pricing") if isinstance(status.get("pricing"), dict) else None,
                        error_code=error_code,
                    )
                )
            for message in value.get("messages") or []:
                mid = str(message.get("id") or "")
                body = ""
                if message.get("type") == "text":
                    body = str((message.get("text") or {}).get("body") or "")
                elif message.get("button"):
                    body = str((message.get("button") or {}).get("text") or (message.get("button") or {}).get("payload") or "")
                events.append(
                    CanonicalEvent(
                        event_type="message.inbound",
                        dedupe_key=f"inbound:{mid}",
                        provider_message_id=mid or None,
                        phone=str(message.get("from") or "") or None,
                        timestamp=_ts(message.get("timestamp")),
                        text=body,
                    )
                )
    return events


def verify_meta_signature(app_secret: str, raw_body: bytes, header: str | None) -> bool:
    if not app_secret or not header or not header.startswith("sha256="):
        return False
    import hmac

    expected = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    presented = header.split("=", 1)[1].strip()
    return hmac.compare_digest(expected, presented)


class MessagingGateway(Protocol):
    def send_template(
        self,
        sender_id: str,
        recipient_e164: str,
        template: dict[str, Any],
        components: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> SendResult: ...

    def send_session_message(self, sender_id: str, recipient_e164: str, kind: str, payload: dict[str, Any]) -> SendResult: ...

    def upload_media(self, sender_id: str, filename: str, data: bytes, content_type: str) -> str: ...

    def sync_templates(self, waba_id: str) -> list[dict[str, Any]]: ...

    def get_sender_health(self, sender_id: str) -> dict[str, Any]: ...

    def normalize_webhook(self, provider: str, raw_payload: dict[str, Any]) -> list[CanonicalEvent]: ...

    def supports_business_app_coexistence(self) -> bool: ...


def _graph_version() -> str:
    version = get_settings().graph_api_version.strip() or "v23.0"
    return version if version.startswith("v") else f"v{version}"


class DirectMetaAdapter:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client

    def supports_business_app_coexistence(self) -> bool:
        return False

    def _http(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        settings = get_settings()
        return httpx.Client(
            timeout=httpx.Timeout(20.0, connect=5.0),
            headers={"Authorization": f"Bearer {settings.meta_access_token}"},
        )

    def send_template(self, sender_id, recipient_e164, template, components, metadata) -> SendResult:
        settings = get_settings()
        phone_number_id = metadata.get("phone_number_id") or settings.meta_phone_number_id
        body = {
            "messaging_product": "whatsapp",
            "to": recipient_e164.lstrip("+"),
            "type": "template",
            "template": {
                "name": template["name"],
                "language": {"code": template["language_code"]},
                "components": components,
            },
        }
        return self._post_message(phone_number_id, body)

    def send_session_message(self, sender_id, recipient_e164, kind, payload) -> SendResult:
        settings = get_settings()
        phone_number_id = payload.get("phone_number_id") or settings.meta_phone_number_id
        body: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": recipient_e164.lstrip("+"),
            "type": kind,
        }
        if kind == "text":
            body["text"] = {"body": payload.get("text") or ""}
        else:
            body[kind] = payload.get("content") or {}
        return self._post_message(phone_number_id, body)

    def _post_message(self, phone_number_id: str, body: dict[str, Any]) -> SendResult:
        settings = get_settings()
        if not settings.comm_live_send_enabled:
            raise ProviderError("Live send is disabled", retryable=False, code="live_send_disabled")
        url = f"https://graph.facebook.com/{_graph_version()}/{phone_number_id}/messages"
        client = self._http()
        close = self._client is None
        try:
            try:
                response = client.post(url, json=body)
            except httpx.TimeoutException as exc:
                raise UnknownOutcome("provider timeout") from exc
            except httpx.TransportError as exc:
                raise UnknownOutcome("provider transport error") from exc
        finally:
            if close:
                client.close()
        if response.status_code == 429 or response.status_code >= 500:
            raise ProviderError("provider retryable", retryable=True, http_status=response.status_code, code=str(response.status_code))
        if response.status_code >= 400:
            code = "rejected"
            try:
                err = response.json().get("error") or {}
                code = str(err.get("code") or err.get("type") or code)
            except Exception:
                code = "rejected"
            log.info("meta send rejected status=%s code=%s", response.status_code, code)
            raise ProviderError("provider rejected", retryable=False, http_status=response.status_code, code=code)
        data = response.json()
        message_id = None
        messages = data.get("messages") or []
        if messages:
            message_id = messages[0].get("id")
        if not message_id:
            raise UnknownOutcome("accepted without message id")
        return SendResult(provider_message_id=str(message_id), http_status=response.status_code)

    def upload_media(self, sender_id, filename, data, content_type) -> str:
        raise ProviderError("Media upload is not enabled in this build", code="media_disabled")

    def sync_templates(self, waba_id: str) -> list[dict[str, Any]]:
        settings = get_settings()
        url = f"https://graph.facebook.com/{_graph_version()}/{waba_id}/message_templates"
        client = self._http()
        close = self._client is None
        try:
            response = client.get(url, params={"limit": 100})
        except httpx.HTTPError as exc:
            raise ProviderError("template sync failed", retryable=True) from exc
        finally:
            if close:
                client.close()
        if response.status_code >= 400:
            raise ProviderError("template sync rejected", http_status=response.status_code)
        rows = []
        for item in response.json().get("data") or []:
            rows.append(
                {
                    "meta_name": item.get("name"),
                    "language_code": item.get("language"),
                    "category": (item.get("category") or "marketing").lower(),
                    "status": (item.get("status") or "pending").lower(),
                    "components_json": _components_from_meta(item.get("components") or []),
                }
            )
        return rows

    def get_sender_health(self, sender_id: str) -> dict[str, Any]:
        settings = get_settings()
        phone_number_id = settings.meta_phone_number_id
        if not phone_number_id or not settings.meta_access_token:
            return {"status": "unconfigured", "quality": "UNKNOWN", "live": False}
        url = f"https://graph.facebook.com/{_graph_version()}/{phone_number_id}"
        client = self._http()
        close = self._client is None
        try:
            response = client.get(url, params={"fields": "quality_rating,messaging_limit_tier,display_phone_number,verified_name"})
        except httpx.HTTPError:
            return {"status": "unreachable", "quality": "UNKNOWN", "live": True}
        finally:
            if close:
                client.close()
        if response.status_code >= 400:
            return {"status": "error", "quality": "UNKNOWN", "http_status": response.status_code}
        data = response.json()
        return {
            "status": "ok",
            "quality": data.get("quality_rating") or "UNKNOWN",
            "messaging_limit_tier": data.get("messaging_limit_tier"),
            "display_name": data.get("verified_name"),
            "live": True,
        }

    def normalize_webhook(self, provider: str, raw_payload: dict[str, Any]) -> list[CanonicalEvent]:
        return normalize_meta_webhook(raw_payload)


def _components_from_meta(components: list[dict[str, Any]]) -> dict[str, Any]:
    body = 0
    header = 0
    buttons = 0
    for component in components:
        kind = (component.get("type") or "").upper()
        text = component.get("text") or ""
        count = text.count("{{")
        if kind == "BODY":
            body = count
        elif kind == "HEADER":
            header = count
        elif kind == "BUTTONS":
            buttons = len(component.get("buttons") or [])
    return {"body_param_count": body, "header_param_count": header, "button_param_count": buttons}


class FakeMetaAdapter:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.mode = "ok"
        self.health = {"quality": "GREEN", "messaging_limit_tier": "TIER_2K", "status": "ok", "live": False}
        self.remote_templates: list[dict[str, Any]] = []

    def supports_business_app_coexistence(self) -> bool:
        return False

    def send_template(self, sender_id, recipient_e164, template, components, metadata) -> SendResult:
        return self._send(sender_id, recipient_e164, "template", {"template": template["name"]})

    def send_session_message(self, sender_id, recipient_e164, kind, payload) -> SendResult:
        return self._send(sender_id, recipient_e164, kind, {})

    def _send(self, sender_id: str, recipient_e164: str, kind: str, extra: dict[str, Any]) -> SendResult:
        if self.mode == "timeout":
            raise UnknownOutcome("simulated timeout")
        if self.mode == "retryable":
            raise ProviderError("simulated 429", retryable=True, http_status=429, code="429")
        if self.mode == "terminal":
            raise ProviderError("simulated reject", retryable=False, http_status=400, code="131026")
        message_id = f"wamid.FAKE.{uuid.uuid4().hex}"
        self.sent.append({"sender_id": sender_id, "to_masked": True, "kind": kind, "id": message_id, **extra})
        return SendResult(provider_message_id=message_id, http_status=200)

    def upload_media(self, sender_id, filename, data, content_type) -> str:
        return "media.fake"

    def sync_templates(self, waba_id: str) -> list[dict[str, Any]]:
        return list(self.remote_templates)

    def get_sender_health(self, sender_id: str) -> dict[str, Any]:
        return dict(self.health)

    def normalize_webhook(self, provider: str, raw_payload: dict[str, Any]) -> list[CanonicalEvent]:
        return normalize_meta_webhook(raw_payload)


class CoexistenceBspAdapter:
    def supports_business_app_coexistence(self) -> bool:
        return False

    def send_template(self, *args, **kwargs) -> SendResult:
        raise ProviderError("Coexistence is not approved for Art City", code="coexistence_disabled")

    def send_session_message(self, *args, **kwargs) -> SendResult:
        raise ProviderError("Coexistence is not approved for Art City", code="coexistence_disabled")

    def upload_media(self, *args, **kwargs) -> str:
        raise ProviderError("Coexistence is not approved for Art City", code="coexistence_disabled")

    def sync_templates(self, waba_id: str) -> list[dict[str, Any]]:
        raise ProviderError("Coexistence is not approved for Art City", code="coexistence_disabled")

    def get_sender_health(self, sender_id: str) -> dict[str, Any]:
        return {"status": "disabled", "quality": "UNKNOWN", "live": False}

    def normalize_webhook(self, provider: str, raw_payload: dict[str, Any]) -> list[CanonicalEvent]:
        raise ProviderError("Coexistence webhooks are not enabled", code="coexistence_disabled")


def get_gateway() -> MessagingGateway:
    settings = get_settings()
    if settings.provider_kind == "official_bsp_coexistence":
        return CoexistenceBspAdapter()
    if settings.provider_kind == "fake" or not settings.comm_live_send_enabled or not settings.meta_access_token:
        return FakeMetaAdapter()
    return DirectMetaAdapter()
