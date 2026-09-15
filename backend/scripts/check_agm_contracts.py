#!/usr/bin/env python3
"""CI contract check: MSG schema + OpenAPI must exist; schema_version locked to 1.0.0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts" / "ac-graphic-motion"


def main() -> int:
    schema_path = CONTRACTS / "motion-scene-graph.schema.json"
    openapi_path = CONTRACTS / "openapi.yaml"
    example_path = CONTRACTS / "examples" / "example-scene.ckb.json"
    missing = [p for p in (schema_path, openapi_path, example_path) if not p.exists()]
    if missing:
        print("MISSING", missing)
        return 1
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    example = json.loads(example_path.read_text(encoding="utf-8"))
    if example.get("schema_version") != "1.0.0":
        print("FAIL: example schema_version must be 1.0.0 (breaking changes require new version)")
        return 1
    # Breaking MSG schema requires new schema_version — enforce enum/const if present
    props = schema.get("properties") or {}
    sv = props.get("schema_version") or {}
    const = sv.get("const") or (sv.get("enum") or [None])[0]
    if const and const != "1.0.0":
        print("FAIL: schema_version const/enum drift", const)
        return 1
    openapi = openapi_path.read_text(encoding="utf-8")
    if "/api/v1/graphic-motion" not in openapi and "servers:" not in openapi:
        print("FAIL: openapi missing graphic-motion server")
        return 1
    print("OK contracts/ac-graphic-motion schema_version=1.0.0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
