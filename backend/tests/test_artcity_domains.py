"""Guard: Art City hosts only — reject foreign / blockchain domains."""

from __future__ import annotations

from app.core.config import (
    ARTCITY_BACKEND_ORIGIN,
    ARTCITY_FRONTEND_ORIGIN,
    Settings,
    _is_blocked_origin,
)


def test_canonical_art_city_hosts() -> None:
    assert "railway.app" in ARTCITY_FRONTEND_ORIGIN
    assert "railway.app" in ARTCITY_BACKEND_ORIGIN
    assert "blockchainsystem.com" not in ARTCITY_FRONTEND_ORIGIN
    assert "blockchainsystem.com" not in ARTCITY_BACKEND_ORIGIN


def test_blocked_origins_filtered() -> None:
    assert _is_blocked_origin("https://blockchainsystem.com")
    assert _is_blocked_origin("https://app.blockchainsystem.com")
    assert _is_blocked_origin("https://alltra.example.com")
    assert not _is_blocked_origin(ARTCITY_FRONTEND_ORIGIN)
    assert not _is_blocked_origin("http://localhost:3000")


def test_settings_strips_blocked_cors(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        f"{ARTCITY_FRONTEND_ORIGIN},https://blockchainsystem.com,http://localhost:3000",
    )
    # Clear lru_cache
    from app.core import config as cfg

    cfg.get_settings.cache_clear()
    settings = Settings()
    origins = settings.cors_origin_list
    assert ARTCITY_FRONTEND_ORIGIN in origins or "http://localhost:3000" in origins
    assert all("blockchainsystem.com" not in o for o in origins)
    cfg.get_settings.cache_clear()
