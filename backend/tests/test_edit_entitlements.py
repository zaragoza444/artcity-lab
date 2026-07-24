"""Art City Edit — entitlement and tenant isolation unit tests."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.enums import EditAccountState, UserRole
from app.services.edit_entitlements import is_platform_admin, org_is_processable


def test_is_platform_admin_roles() -> None:
    assert is_platform_admin(SimpleNamespace(role=UserRole.SUPER_ADMIN.value))
    assert is_platform_admin(SimpleNamespace(role=UserRole.ADMINISTRATOR.value))
    assert not is_platform_admin(SimpleNamespace(role=UserRole.EDITOR.value))
    assert not is_platform_admin(SimpleNamespace(role=UserRole.VIEWER.value))


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class _FakeDb:
    def __init__(self, org=None, sub=None):
        self._org = org
        self._sub = sub

    def get(self, model, pk):
        if self._org and getattr(self._org, "id", None) == pk:
            return self._org
        return None

    def query(self, model):
        # Subscription lookup
        return _FakeQuery(self._sub)


def test_org_is_processable_requires_active_subscription() -> None:
    org_id = str(uuid4())
    active_org = SimpleNamespace(id=org_id, status=EditAccountState.ACTIVE.value)
    suspended = SimpleNamespace(id=org_id, status=EditAccountState.SUSPENDED.value)
    sub = SimpleNamespace(status="active")

    assert org_is_processable(_FakeDb(org=active_org, sub=sub), org_id)
    assert not org_is_processable(_FakeDb(org=suspended, sub=sub), org_id)
    assert not org_is_processable(_FakeDb(org=active_org, sub=None), org_id)
    assert not org_is_processable(_FakeDb(org=None, sub=sub), org_id)


def test_assert_entitled_blocks_suspended(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import edit_entitlements as mod

    org_id = str(uuid4())
    suspended = SimpleNamespace(id=org_id, status=EditAccountState.SUSPENDED.value)

    class Db:
        def get(self, model, pk):
            return suspended

        def query(self, model):
            return _FakeQuery(None)

    with pytest.raises(ValueError, match="suspended"):
        mod.assert_entitled(Db(), org_id, feature="processing_minutes", amount=1)
