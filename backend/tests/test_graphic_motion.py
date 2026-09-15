"""AC Graphic Motion — Wave A/C unit tests."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

# Avoid requiring live Postgres/psycopg for pure unit tests on Windows CI agents.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi import HTTPException

from app.core.config import get_settings

get_settings.cache_clear()

from app.services import agm_acx, agm_brand, agm_patch, agm_typography, agm_validate
from app.services.agm_patch import apply_patch

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "contracts" / "ac-graphic-motion" / "examples" / "example-scene.ckb.json"
SCHEMA = ROOT / "contracts" / "ac-graphic-motion" / "motion-scene-graph.schema.json"


def test_schema_file_exists() -> None:
    assert SCHEMA.exists()
    data = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert data.get("$schema")


def test_sorani_example_loads_and_validates() -> None:
    graph = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert graph["locale"] == "ckb-IQ"
    assert graph["direction"] == "rtl"
    assert "هەواڵی" in graph["nodes"][0]["payload"]["text"]
    report = agm_validate.validate_graph(graph, strict_assets=False)
    assert report["valid"], report["errors"]


def test_invalid_schema_rejected() -> None:
    report = agm_validate.validate_graph({"schema_version": "0.0.1"}, strict_assets=False)
    assert not report["valid"]
    assert "AGM_SCHEMA_INVALID" in report["error_codes"]


def test_revision_immutability_via_patch_copy() -> None:
    graph = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    original = copy.deepcopy(graph)
    patched = apply_patch(graph, [{"op": "replace", "path": "/name", "value": "Updated"}])
    assert patched["name"] == "Updated"
    assert graph == original
    assert original["name"] != patched["name"]


def test_if_match_conflict_semantics() -> None:
    from app.services import agm_scene

    scene = SimpleNamespace(
        id="s1",
        soft_deleted=False,
        etag="expected-etag",
        head_revision_id="r1",
        project_id=str(uuid4()),
        name="Scene",
    )

    class DB:
        def get(self, model, pk):
            if pk == "s1":
                return scene
            return None

    with pytest.raises(HTTPException) as exc:
        agm_scene.patch_scene(DB(), scene_id="s1", operations=[], if_match="wrong", user_id=None)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "AGM_REVISION_CONFLICT"


def test_protected_logo_mutation_fail_closed() -> None:
    before = {
        "nodes": [
            {
                "id": "logo1",
                "type": "logo",
                "payload": {"asset_id": "a1", "preserve_exact_pixels": True},
                "transform": {"scale": 1},
            }
        ]
    }
    after = copy.deepcopy(before)
    after["nodes"][0]["payload"]["recolor"] = True
    errs = agm_brand.validate_graph_brand(after)
    assert any(e["code"] == "AGM_BRAND_LOGO_MUTATION" for e in errs)
    after2 = copy.deepcopy(before)
    after2["nodes"][0]["payload"]["asset_id"] = "a2"
    errs2 = agm_brand.assert_no_logo_mutation(before, after2)
    assert any(e["code"] == "AGM_BRAND_LOGO_MUTATION" for e in errs2)


def test_typography_nfc_and_sorani_word_units() -> None:
    payload = {
        "text": "هەواڵی گرنگ",
        "direction": "rtl",
        "animation_unit": "word",
        "shaping_engine": "harfbuzz",
        "normalization": "NFC",
    }
    shaped = agm_typography.shape_text(payload)
    assert shaped["contains_arabic_script"]
    assert shaped["engine_status"] == "nfc_bidi_ready"
    assert "هەواڵی" in shaped["units"]


def test_typography_rejects_codepoint_animation() -> None:
    graph = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    graph["nodes"][0]["payload"]["animation_unit"] = "codepoint"
    report = agm_validate.validate_graph(graph)
    assert "AGM_RTL_SHAPING_FAILED" in report["error_codes"]


def test_acx_no_double_reserve_or_settle() -> None:
    from app.models_agm import AgmAcxReservation, AgmJob

    job = AgmJob(
        id=str(uuid4()),
        scene_id=str(uuid4()),
        project_id=str(uuid4()),
        revision_id=str(uuid4()),
        job_kind="preview",
        status="queued",
    )
    db_rows: list[AgmAcxReservation] = []

    class Q:
        def __init__(self, rows):
            self.rows = rows

        def filter(self, *a, **k):
            return self

        def first(self):
            return self.rows[0] if self.rows else None

    class DB:
        def query(self, model):
            return Q(db_rows)

        def add(self, row):
            if isinstance(row, AgmAcxReservation) and row not in db_rows:
                db_rows.append(row)

        def flush(self):
            for r in db_rows:
                if not getattr(r, "id", None):
                    r.id = str(uuid4())

    db = DB()
    r1 = agm_acx.reserve(db, job=job, quote_id="q1", amount=2.5)
    r2 = agm_acx.reserve(db, job=job, quote_id="q1", amount=2.5)
    assert r1 is r2
    assert len(db_rows) == 1
    s1 = agm_acx.settle(db, job_id=job.id)
    s2 = agm_acx.settle(db, job_id=job.id)
    assert s1.status == "settled" and s2.status == "settled"
    assert s1.settled_amount == 2.5


def test_broadcast_profile_alpha_rules() -> None:
    ok = agm_validate.validate_output_profile(
        {"container": "mp4", "codec": "h264", "alpha": False, "width": 1920, "height": 1080, "fps": 25}
    )
    assert ok == []
    bad = agm_validate.validate_output_profile({"container": "mp4", "codec": "h264", "alpha": True})
    assert any(e["code"] == "AGM_RENDER_PROFILE_INVALID" for e in bad)
    prores = agm_validate.validate_output_profile({"container": "mov", "codec": "prores4444", "alpha": True})
    assert prores == []


def test_rfc6902_replace() -> None:
    doc = {"a": 1, "b": {"c": 2}}
    out = agm_patch.apply_patch(doc, [{"op": "replace", "path": "/b/c", "value": 3}])
    assert out["b"]["c"] == 3


def test_preview_parity_helper_deterministic() -> None:
    from app.services.agm_render import _png_bytes

    a = _png_bytes(64, 36, "preview:100")
    b = _png_bytes(64, 36, "preview:100")
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()
