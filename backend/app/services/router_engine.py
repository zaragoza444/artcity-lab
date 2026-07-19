"""Model Gateway routing: character / modality → Art City model or fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import ModelStatus
from app.models import RegisteredModel, RouteRule


@dataclass
class RouteDecision:
    provider: str
    model_name: Optional[str]
    model_version: Optional[str]
    registered_model_id: Optional[str]
    character_key: Optional[str]
    reason: str


def resolve_route(
    db: Session,
    *,
    modality: str,
    character_key: Optional[str] = None,
    model: Optional[str] = None,
    prefer_external: bool = False,
) -> RouteDecision:
    settings = get_settings()

    if prefer_external and settings.external_providers_enabled:
        return RouteDecision(
            provider="external-fallback",
            model_name=model,
            model_version=None,
            registered_model_id=None,
            character_key=character_key,
            reason="explicit_external_fallback",
        )

    rule_q = (
        db.query(RouteRule)
        .filter(RouteRule.modality == modality, RouteRule.is_active.is_(True))
        .order_by(RouteRule.priority.asc())
    )
    if character_key:
        rule = rule_q.filter(RouteRule.character_key == character_key).first()
        if not rule:
            rule = rule_q.filter(RouteRule.character_key.is_(None)).first()
    else:
        rule = rule_q.filter(RouteRule.character_key.is_(None)).first()

    if rule:
        reg = db.get(RegisteredModel, rule.model_id) if rule.model_id else None
        if reg and reg.status in {
            ModelStatus.PRODUCTION.value,
            ModelStatus.STAGING.value,
            ModelStatus.APPROVED.value,
        }:
            return RouteDecision(
                provider=rule.provider,
                model_name=reg.name,
                model_version=reg.version,
                registered_model_id=reg.id,
                character_key=character_key or reg.character_key,
                reason=f"route_rule:{rule.name}",
            )
        return RouteDecision(
            provider=rule.provider,
            model_name=model or (reg.name if reg else None),
            model_version=reg.version if reg else None,
            registered_model_id=reg.id if reg else None,
            character_key=character_key,
            reason=f"route_rule_provider:{rule.name}",
        )

    if character_key:
        reg = (
            db.query(RegisteredModel)
            .filter(
                RegisteredModel.character_key == character_key,
                RegisteredModel.modality == modality,
                RegisteredModel.status.in_(
                    [
                        ModelStatus.PRODUCTION.value,
                        ModelStatus.STAGING.value,
                        ModelStatus.APPROVED.value,
                    ]
                ),
            )
            .order_by(RegisteredModel.created_at.desc())
            .first()
        )
        if reg:
            provider = "artcity-image" if modality == "image" else "artcity-video" if modality == "video" else "stub"
            return RouteDecision(
                provider=provider,
                model_name=reg.name,
                model_version=reg.version,
                registered_model_id=reg.id,
                character_key=character_key,
                reason="character_model_registry",
            )

    defaults = {
        "image": ("artcity-image", "artcity-local-v1"),
        "video": ("artcity-video", "artcity-video-v1"),
        "voice": ("artcity-voice", "artcity-voice-v1"),
        "music": ("artcity-music", "artcity-music-v1"),
        "audio": ("artcity-audio", "artcity-audio-v1"),
    }
    if modality in defaults:
        provider, default_model = defaults[modality]
        return RouteDecision(
            provider=provider,
            model_name=model or default_model,
            model_version="v1",
            registered_model_id=None,
            character_key=character_key,
            reason=f"default_{provider}",
        )
    return RouteDecision(
        provider="stub",
        model_name=model or "artcity-local-v1",
        model_version="v1",
        registered_model_id=None,
        character_key=character_key,
        reason="default_stub",
    )
