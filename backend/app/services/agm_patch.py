"""RFC 6902 JSON Patch for MSG revisions."""

from __future__ import annotations

import copy
from typing import Any


class PatchError(ValueError):
    def __init__(self, message: str, code: str = "AGM_SCHEMA_INVALID") -> None:
        super().__init__(message)
        self.code = code


def _pointer_tokens(path: str) -> list[str]:
    if path == "":
        return []
    if not path.startswith("/"):
        raise PatchError("JSON Pointer must start with /")
    parts = path[1:].split("/") if path != "/" else []
    out = []
    for p in parts:
        out.append(p.replace("~1", "/").replace("~0", "~"))
    return out


def _resolve(doc: Any, tokens: list[str], *, create_parent: bool = False) -> tuple[Any, str | int | None]:
    if not tokens:
        return doc, None
    cur = doc
    for token in tokens[:-1]:
        if isinstance(cur, list):
            idx = int(token) if token != "-" else len(cur)
            cur = cur[idx]
        elif isinstance(cur, dict):
            if token not in cur:
                if create_parent:
                    cur[token] = {}
                else:
                    raise PatchError(f"path not found: {token}")
            cur = cur[token]
        else:
            raise PatchError("cannot traverse path")
    return cur, tokens[-1]


def apply_patch(document: dict[str, Any], operations: list[dict[str, Any]]) -> dict[str, Any]:
    doc = copy.deepcopy(document)
    if not isinstance(operations, list):
        raise PatchError("patch must be an array")
    for op in operations:
        if not isinstance(op, dict) or "op" not in op or "path" not in op:
            raise PatchError("each op needs op+path")
        kind = op["op"]
        path = op["path"]
        tokens = _pointer_tokens(path)
        parent, key = _resolve(doc, tokens, create_parent=kind in {"add", "replace"})
        if kind == "add":
            if "value" not in op:
                raise PatchError("add requires value")
            if key is None:
                if not isinstance(op["value"], dict):
                    raise PatchError("replace root must be object")
                doc = copy.deepcopy(op["value"])
            elif isinstance(parent, list):
                if key == "-":
                    parent.append(op["value"])
                else:
                    parent.insert(int(key), op["value"])
            else:
                parent[str(key)] = op["value"]
        elif kind == "remove":
            if key is None:
                raise PatchError("cannot remove root")
            if isinstance(parent, list):
                parent.pop(int(key))
            else:
                if str(key) not in parent:
                    raise PatchError("remove path missing")
                del parent[str(key)]
        elif kind == "replace":
            if "value" not in op:
                raise PatchError("replace requires value")
            if key is None:
                if not isinstance(op["value"], dict):
                    raise PatchError("replace root must be object")
                doc = copy.deepcopy(op["value"])
            elif isinstance(parent, list):
                parent[int(key)] = op["value"]
            else:
                if str(key) not in parent:
                    raise PatchError("replace path missing")
                parent[str(key)] = op["value"]
        elif kind == "test":
            if key is None:
                actual = doc
            elif isinstance(parent, list):
                actual = parent[int(key)]
            else:
                actual = parent.get(str(key))
            if actual != op.get("value"):
                raise PatchError("test operation failed")
        elif kind == "move":
            raise PatchError("move not supported in v1")
        elif kind == "copy":
            raise PatchError("copy not supported in v1")
        else:
            raise PatchError(f"unsupported op {kind}")
    return doc
