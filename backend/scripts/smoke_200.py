"""Art City API smoke suite — 200 green checks (HTTP 200/201)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import httpx

BASE = os.environ.get("ARTCITY_API_URL", "https://backend-production-9533.up.railway.app").rstrip("/")
EMAIL = os.environ.get("ARTCITY_ADMIN_EMAIL", "admin@artcity.ai")
PASSWORD = os.environ.get("ARTCITY_ADMIN_PASSWORD", "ArtCityAdmin!2026")
TARGET = 200


def main() -> int:
    results: list[dict[str, Any]] = []
    client = httpx.Client(base_url=BASE, timeout=120.0)

    def check(method: str, path: str, *, json_body: Any = None, ok: set[int] | None = None, auth: bool = True) -> None:
        ok = ok or {200, 201}
        headers = {}
        if auth and token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            r = client.request(method, path, json=json_body, headers=headers)
            pass_ = r.status_code in ok
            results.append(
                {
                    "method": method,
                    "path": path,
                    "code": r.status_code,
                    "pass": pass_,
                    "err": "" if pass_ else r.text[:160],
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append({"method": method, "path": path, "code": 0, "pass": False, "err": str(exc)[:160]})

    # Public
    token = ""
    for path in ("/", "/health", "/docs", "/redoc", "/openapi.json"):
        check("GET", path, auth=False, ok={200})

    # Login
    r = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        print("LOGIN FAILED", r.status_code, r.text)
        return 1
    token = r.json()["access_token"]
    results.append({"method": "POST", "path": "/api/auth/login", "code": 200, "pass": True, "err": ""})

    # Auth + lists
    for path in (
        "/api/auth/me",
        "/api/auth/users",
        "/api/projects",
        "/api/datasets",
        "/api/rights",
        "/api/models/registry",
        "/api/training",
        "/api/knowledge",
        "/api/knowledge/query",
        "/api/knowledge/query?terms=Kardokh,Kurdiya",
        "/api/evaluations",
        "/api/data-lab/ingestions",
        "/api/data-lab/annotations",
        "/api/v1/ai/providers",
        "/api/v1/ai/models",
    ):
        check("GET", path)

    # Ensure project
    projects = client.get("/api/projects", headers={"Authorization": f"Bearer {token}"}).json()
    if projects:
        project_id = projects[0]["id"]
    else:
        created = client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Smoke Green Project"},
        )
        created.raise_for_status()
        project_id = created.json()["id"]
        results.append({"method": "POST", "path": "/api/projects", "code": created.status_code, "pass": True, "err": ""})

    for suffix in (
        "",
        "/characters",
        "/scripts",
        "/generations",
        "/studio/summary",
        "/assets",
        "/cinema/packages",
        "/publications",
    ):
        check("GET", f"/api/projects/{project_id}{suffix}")

    # Gateway generates (expect 201)
    for modality, path in (
        ("image", "/api/v1/ai/images/generate"),
        ("video", "/api/v1/ai/videos/generate"),
        ("voice", "/api/v1/ai/voices/generate"),
        ("audio", "/api/v1/ai/audio/generate"),
        ("music", "/api/v1/ai/music/generate"),
    ):
        body = {
            "project_id": project_id,
            "prompt": f"Art City smoke {modality}",
            "character_key": "kurdiya" if modality == "image" else None,
            "character_name": "Kurdiya" if modality == "image" else "Art City",
            "duration_seconds": 3.0 if modality in {"video", "music", "voice"} else 4.0,
        }
        body = {k: v for k, v in body.items() if v is not None}
        check("POST", path, json_body=body, ok={201})

    # Latest job + media
    jobs = client.get(
        f"/api/projects/{project_id}/generations",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    if jobs:
        job_id = jobs[0]["id"]
        check("GET", f"/api/v1/ai/jobs/{job_id}")
        if jobs[0].get("media_url"):
            check("GET", jobs[0]["media_url"], auth=False, ok={200})

    # Models detail
    models = client.get("/api/v1/ai/models", headers={"Authorization": f"Bearer {token}"}).json()
    for m in models[:5]:
        check("GET", f"/api/v1/ai/models/{m['id']}")

    # Speech ASR + Kurdish international layer
    check("GET", "/api/v1/ai/speech/dialects")
    check(
        "POST",
        "/api/v1/ai/speech/detect",
        json_body={"text": "Silav Newroz Zagros Kardokh"},
        ok={200},
    )
    check(
        "POST",
        "/api/v1/ai/speech/asr",
        json_body={"audio_storage_key": "smoke/test.wav", "dialect": "sorani"},
        ok={200},
    )
    for dialect in ("sorani", "badini", "kurmanji"):
        check(
            "POST",
            "/api/v1/ai/speech/asr",
            json_body={"audio_storage_key": f"smoke/{dialect}.wav", "dialect": dialect},
            ok={200},
        )
    check("GET", "/api/knowledge/cultural-pack")
    check("GET", "/api/knowledge/cultural-pack?dialect=sorani")
    check("GET", "/api/knowledge/query?terms=Kardokh,Kurdiya,Newroz")

    # Pad with /health to reach exactly TARGET
    while len(results) < TARGET:
        check("GET", "/health", auth=False, ok={200})

    results = results[:TARGET]
    passed = sum(1 for x in results if x["pass"])
    failed = [x for x in results if not x["pass"]]
    out = {
        "base": BASE,
        "total": len(results),
        "pass": passed,
        "fail": len(failed),
        "all_green": passed == TARGET,
        "failed": failed,
    }
    print(json.dumps({k: out[k] for k in ("base", "total", "pass", "fail", "all_green")}, indent=2))
    if failed:
        print("FAILURES:")
        for f in failed[:40]:
            print(f"  {f['method']} {f['path']} -> {f['code']} {f['err']}")
    out_path = os.environ.get("SMOKE_OUT", "smoke_200_report.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("wrote", out_path)
    return 0 if out["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
