"""Vertical Drama unit tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.enums import UserRole
from app.services.vd_access import assert_transition, require_approve, require_edit, require_vd


def test_episode_state_machine() -> None:
    assert_transition("planned", "drafted")
    assert_transition("drafted", "reviewed")
    assert_transition("reviewed", "approved")
    assert_transition("approved", "production_ready")
    assert_transition("production_ready", "locked")
    with pytest.raises(ValueError):
        assert_transition("locked", "drafted")
    with pytest.raises(ValueError):
        assert_transition("planned", "locked")


def test_require_vd_respects_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import vd_access as mod

    monkeypatch.setattr(mod, "get_settings", lambda: SimpleNamespace(vd_feature_enabled=False))
    with pytest.raises(HTTPException) as exc:
        require_vd()
    assert exc.value.status_code == 403


def test_viewer_cannot_edit() -> None:
    with pytest.raises(HTTPException):
        require_edit(SimpleNamespace(role=UserRole.VIEWER.value, is_active=True))


def test_producer_can_approve() -> None:
    require_approve(SimpleNamespace(role=UserRole.PRODUCER.value))


def test_project_isolation_query_keys() -> None:
    """Characters/canon are scoped by vd_project_id + platform project_id (never global)."""
    from app.models_vd import VdCharacter, VdCanonFact

    assert "vd_project_id" in VdCharacter.__table__.c
    assert "project_id" in VdCharacter.__table__.c
    assert "vd_project_id" in VdCanonFact.__table__.c
    assert "project_id" in VdCanonFact.__table__.c
