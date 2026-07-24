"""Art City Edit — structured edit plan schema validation helpers."""

from __future__ import annotations


def test_edit_plan_schema_shape() -> None:
    plan = {
        "schema_version": "1.0",
        "project_id": "prj_demo",
        "source_asset_id": "ast_demo",
        "output_duration_seconds": 42.5,
        "segments": [
            {
                "source_in": 814.2,
                "source_out": 822.8,
                "role": "hook",
                "speed": 1.0,
                "integrity_note": None,
            }
        ],
        "format_profile": "social_vertical_1080x1920",
    }
    assert plan["schema_version"] == "1.0"
    assert plan["segments"][0]["source_out"] > plan["segments"][0]["source_in"]
    assert all(k in plan["segments"][0] for k in ("source_in", "source_out", "role"))
