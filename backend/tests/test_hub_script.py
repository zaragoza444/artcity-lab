"""Production Hub unit tests — page eighths, lock rules, Sorani normalize, entitlements."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.enums import UserRole
from app.services.hub_access import hub_features, require_hub_module, require_script_lock
from app.services.hub_i18n_normalize import estimate_page_eighths, normalize_for_search
from app.services.hub_script import lock_version


def test_estimate_page_eighths_minimum() -> None:
    assert estimate_page_eighths([]) == 1
    assert estimate_page_eighths([""]) == 1


def test_estimate_page_eighths_scales() -> None:
    short = estimate_page_eighths(["INT. CAFE - DAY"])
    long = estimate_page_eighths(["x" * 1800, "y" * 1800])
    assert short >= 1
    assert long >= short
    assert long >= 8


def test_sorani_normalize_without_mutating_display() -> None:
    display = "كوردستان يه"
    _ = normalize_for_search(display)
    assert display == "كوردستان يه"  # original untouched
    # Arabic yeh/kaf map to Kurdish forms for search only
    assert normalize_for_search("ك") == normalize_for_search("ک")
    assert normalize_for_search("ي") == normalize_for_search("ی")


def test_normalize_collapses_whitespace_and_tatweel() -> None:
    assert normalize_for_search("hello   world") == "hello world"
    assert "ـ" not in normalize_for_search("سـلام")
    assert normalize_for_search("سـلام") == normalize_for_search("سلام")


def test_hub_features_respect_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import hub_access as mod

    monkeypatch.setattr(
        mod,
        "get_settings",
        lambda: SimpleNamespace(
            hub_feature_script=True,
            hub_feature_storyboard=False,
            hub_feature_budget=False,
            hub_feature_call=False,
        ),
    )
    feats = hub_features()
    assert feats["script"] is True
    assert feats["storyboard"] is False


def test_require_hub_module_blocks_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import hub_access as mod

    monkeypatch.setattr(
        mod,
        "get_settings",
        lambda: SimpleNamespace(
            hub_feature_script=False,
            hub_feature_storyboard=False,
            hub_feature_budget=False,
            hub_feature_call=False,
        ),
    )
    with pytest.raises(HTTPException) as exc:
        require_hub_module("script")
    assert exc.value.status_code == 403


def test_require_script_lock_permission_matrix() -> None:
    require_script_lock(SimpleNamespace(role=UserRole.PRODUCER.value))
    require_script_lock(SimpleNamespace(role=UserRole.ADMINISTRATOR.value))
    with pytest.raises(HTTPException):
        require_script_lock(SimpleNamespace(role=UserRole.VIEWER.value))


def test_lock_version_idempotent() -> None:
    user = SimpleNamespace(id=str(uuid4()))
    version = SimpleNamespace(
        id=str(uuid4()),
        project_id=str(uuid4()),
        script_id=str(uuid4()),
        version_label="v1",
        status="locked",
        locked_at="already",
        locked_by=user.id,
    )

    class Db:
        def add(self, obj):
            return None

        def flush(self):
            return None

    out = lock_version(Db(), version=version, user=user)  # type: ignore[arg-type]
    assert out.status == "locked"
    assert out.locked_at == "already"
