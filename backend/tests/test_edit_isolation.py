"""Art City Edit — workspace access denial when membership missing."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.enums import UserRole
from app.services.edit_entitlements import require_workspace_access


class _Q:
    def __init__(self, result=None):
        self._result = result

    def filter(self, *a, **k):
        return self

    def first(self):
        return self._result


class _Db:
    def __init__(self, workspace=None, membership=None):
        self._workspace = workspace
        self._membership = membership

    def get(self, model, pk):
        if self._workspace and self._workspace.id == pk:
            return self._workspace
        return None

    def query(self, model):
        return _Q(self._membership)


def test_require_workspace_access_denies_foreign_user() -> None:
    ws_id = str(uuid4())
    workspace = SimpleNamespace(id=ws_id, organisation_id=str(uuid4()))
    user = SimpleNamespace(id=str(uuid4()), role=UserRole.EDITOR.value)
    with pytest.raises(ValueError, match="denied"):
        require_workspace_access(_Db(workspace=workspace, membership=None), user, ws_id)


def test_platform_admin_synthetic_membership() -> None:
    ws_id = str(uuid4())
    org_id = str(uuid4())
    workspace = SimpleNamespace(id=ws_id, organisation_id=org_id)
    admin = SimpleNamespace(id=str(uuid4()), role=UserRole.SUPER_ADMIN.value)
    m = require_workspace_access(_Db(workspace=workspace, membership=None), admin, ws_id)
    assert m.workspace_id == ws_id
    assert m.organisation_id == org_id
