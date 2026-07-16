"""Seed a genuine Art City Cinema campaign and run deep technical validation + ZIP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure backend root on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.db import SessionLocal  # noqa: E402
from app.models import Project  # noqa: E402
from app.services.cinema import build_cinematic_package  # noqa: E402
from app.services.packaging import build_campaign_zip  # noqa: E402


ART_CITY_BRIEF = """
Art City Channel brand film: warm Kurdish golden-hour village, two friends reuniting on a dusty path,
handmade instruments, childhood kite colours (Art City gold #c5a15e and teal #3aa39c), emotional close-ups,
slow push-ins, premium television advertising finish for Kardokh & Kurdiya season launch.
""".strip()

VOICEOVER = """
Some friendships rewrite the map of home.
Kardokh. Kurdiya.
A new season of wonder — only on Art City Channel.
Watch the story.
""".strip()


def main() -> int:
    db = SessionLocal()
    try:
        project = (
            db.query(Project)
            .filter(Project.name.ilike("%Kardokh%"))
            .order_by(Project.created_at.desc())
            .first()
        )
        if not project:
            project = Project(
                name="Art City Channel · Kardokh & Kurdiya",
                description="Official Art City brand production project",
            )
            db.add(project)
            db.commit()
            db.refresh(project)

        package = build_cinematic_package(
            db,
            project_id=project.id,
            campaign="Kardokh & Kurdiya · Season of Homecoming",
            brief=ART_CITY_BRIEF,
            cta="Watch on Art City Channel",
            brand="Art City",
            voiceover_script=VOICEOVER,
            music_style="warm",
            duration_seconds=15,
            initiated_by="art-city-producer",
            brand_colors={
                "ink": "#05070b",
                "gold": "#c5a15e",
                "gold_bright": "#efd39a",
                "teal": "#3aa39c",
                "paper": "#f3f6fa",
            },
            usage_rights="Art City Channel — proprietary broadcast and social advertising rights",
        )

        passed = package.get("validation_passed")
        print("project_id:", project.id)
        print("package_id:", package["package_id"])
        print("validation_passed:", passed)
        print("total_cost:", package.get("total_cost"))
        print("production_time_seconds:", package.get("production_time_seconds"))

        validation = package.get("validation") or {}
        for d in validation.get("deliverables", []):
            status = "PASS" if d.get("passed") else "FAIL"
            print(f"  [{status}] {d.get('role')}")
            for c in d.get("checks", []):
                if not c.get("passed"):
                    print(f"      - FAIL {c.get('id')}: expected={c.get('expected')} actual={c.get('actual')}")

        completeness = validation.get("completeness") or {}
        print("completeness:", completeness.get("passed"), completeness.get("detail"))

        zip_bytes = build_campaign_zip(db, project.id, package["package_id"])
        out = ROOT / "demo_output" / f"art-city-cinema-{package['package_id'][:8]}.zip"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(zip_bytes)
        print("zip_bytes:", len(zip_bytes))
        print("zip_path:", out)

        manifest_path = ROOT / "demo_output" / f"CAMPAIGN_MANIFEST-{package['package_id'][:8]}.json"
        manifest_path.write_text(json.dumps(package.get("campaign_manifest"), indent=2), encoding="utf-8")
        print("manifest_path:", manifest_path)

        return 0 if passed else 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
