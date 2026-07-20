"""Art City production E2E — every critical path must be HTTP 200/201."""

from __future__ import annotations

import json
import os
import sys
import wave
from io import BytesIO
from typing import Any

import httpx

BASE = os.environ.get("ARTCITY_API_URL", "https://backend-production-9533.up.railway.app").rstrip("/")
APP = os.environ.get("ARTCITY_APP_URL", "https://frontend-production-6380.up.railway.app").rstrip("/")
EMAIL = os.environ.get("ARTCITY_ADMIN_EMAIL", "admin@artcity.ai")
PASSWORD = os.environ.get("ARTCITY_ADMIN_PASSWORD", "ArtCityAdmin!2026")


def _wav(duration: float = 1.0, rate: int = 16000) -> bytes:
    frames = max(1, int(rate * duration))
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


def main() -> int:
    rows: list[dict[str, Any]] = []

    def ok(name: str, code: int, detail: str = "") -> None:
        passed = code in {200, 201}
        rows.append({"name": name, "code": code, "pass": passed, "detail": detail[:200]})
        mark = "OK" if passed else "FAIL"
        print(f"{mark}  {name}  {code}  {detail[:100]}")

    def assert_true(name: str, cond: bool, detail: str = "") -> None:
        rows.append({"name": name, "code": 200 if cond else 0, "pass": cond, "detail": detail[:200]})
        mark = "OK" if cond else "FAIL"
        print(f"{mark}  {name}  {'200' if cond else '0'}  {detail[:100]}")

    client = httpx.Client(base_url=BASE, timeout=180.0)

    # Public API
    for path in ("/", "/health", "/docs", "/openapi.json", "/redoc"):
        r = client.get(path)
        ok(f"API GET {path}", r.status_code)

    # Frontend pages
    app = httpx.Client(base_url=APP, timeout=60.0, follow_redirects=True)
    for path in (
        "/",
        "/login",
        "/dashboard",
        "/advertising",
        "/cinema",
        "/studio",
        "/publish",
        "/speech",
        "/knowledge",
        "/projects",
    ):
        r = app.get(path)
        ok(f"UI GET {path}", r.status_code)

    # Auth — JSON login + OAuth2 token (Swagger)
    login = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    ok("POST /api/auth/login", login.status_code)
    if login.status_code != 200:
        print(json.dumps({"all_green": False, "fail": len(rows)}, indent=2))
        return 1
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    oauth = client.post(
        "/api/auth/token",
        data={"username": EMAIL, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    ok("POST /api/auth/token", oauth.status_code)

    me = client.get("/api/auth/me", headers=headers)
    ok("GET /api/auth/me", me.status_code)
    assert_true("admin is_active", bool(me.json().get("is_active")), me.text[:80])

    # Project
    proj = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "E2E 200 Full Prod", "description": "green suite"},
    )
    ok("POST /api/projects", proj.status_code)
    project_id = proj.json()["id"]

    # Studio modalities
    for modality in ("image", "video", "voice", "audio", "music"):
        r = client.post(
            f"/api/projects/{project_id}/studio/generate",
            headers=headers,
            json={
                "modality": modality,
                "prompt": f"E2E {modality} Kardokh Newroz",
                "duration_seconds": 5,
                "dialect": "sorani",
                "character_key": "kardokh",
                "character_name": "Kardokh",
                "run_asr": modality == "voice",
            },
        )
        ok(f"studio/{modality}", r.status_code)
        if r.status_code in {200, 201}:
            media = r.json().get("media_url")
            if media:
                mr = client.get(media)
                ok(f"studio/{modality}/media", mr.status_code)
                if modality == "video":
                    ctype = mr.headers.get("content-type", "")
                    assert_true(
                        "studio/video is mp4 or svg",
                        "mp4" in ctype or "svg" in ctype,
                        ctype,
                    )

    # Gateway
    for path in (
        "/api/v1/ai/images/generate",
        "/api/v1/ai/videos/generate",
        "/api/v1/ai/voices/generate",
        "/api/v1/ai/audio/generate",
        "/api/v1/ai/music/generate",
    ):
        r = client.post(
            path,
            headers=headers,
            json={
                "project_id": project_id,
                "prompt": f"E2E gateway {path}",
                "duration_seconds": 4,
                "dialect": "sorani",
                "character_key": "kurdiya",
            },
        )
        ok(f"gateway {path}", r.status_code)

    # Cinema full production package
    cinema = client.post(
        f"/api/projects/{project_id}/cinema/packages",
        headers=headers,
        json={
            "campaign": "E2E Full Prod Ad",
            "brief": "Kardokh Kurdiya Newroz advertising production masters",
            "cta": "Watch the story",
            "duration_seconds": 12,
            "dialect": "sorani",
            "character_key": "kardokh",
            "character_name": "Kardokh",
            "channels": ["broadcast", "social_vertical", "social_square"],
            "variants": ["A", "B"],
            "delivery_targets": ["youtube", "meta_stories", "broadcast_tv"],
            "music_style": "epic",
        },
    )
    ok("cinema package", cinema.status_code)
    package_id = cinema.json().get("package_id") if cinema.status_code in {200, 201} else None
    if package_id:
        body = cinema.json()
        assert_true("cinema QC passed", bool(body.get("validation_passed")), str(body.get("validation"))[:120])
        assert_true("cinema has variants", len(body.get("variants") or []) >= 2, str(len(body.get("variants") or [])))
        assert_true(
            "cinema has delivery targets",
            len(body.get("delivery_targets") or []) >= 2,
            str(len(body.get("delivery_targets") or [])),
        )
        assert_true(
            "cinema has timeline",
            bool((body.get("timeline") or {}).get("clips")),
            str(body.get("timeline"))[:80],
        )
        videos = [d for d in (body.get("deliverables") or []) if d.get("modality") == "video"]
        assert_true("cinema has video cutdowns", len(videos) >= 3, str(len(videos)))
        if videos:
            media = videos[0].get("mp4_url") or videos[0].get("media_url")
            if media:
                mr = client.get(media, headers=headers)
                ok("cinema video media", mr.status_code)
                ctype = mr.headers.get("content-type", "")
                assert_true("cinema master is mp4", "mp4" in ctype or mr.content[4:8] == b"ftyp", ctype)

        tl = client.patch(
            f"/api/projects/{project_id}/cinema/packages/{package_id}/timeline",
            headers=headers,
            json={"music_gain_db": -1.5, "voice_gain_db": 1.0, "duck_music_under_vo": True},
        )
        ok("cinema timeline patch", tl.status_code)

        zip_r = client.get(
            f"/api/projects/{project_id}/cinema/packages/{package_id}/zip",
            headers=headers,
        )
        ok("cinema zip", zip_r.status_code)
        assert_true("cinema zip non-empty", len(zip_r.content) > 1000, str(len(zip_r.content)))

        man = client.get(
            f"/api/projects/{project_id}/cinema/packages/{package_id}/manifest",
            headers=headers,
        )
        ok("cinema manifest", man.status_code)

        pub = client.post(
            f"/api/projects/{project_id}/publications",
            headers=headers,
            json={"cinema_package_id": package_id, "channel": "art_city_channel"},
        )
        ok("publication create", pub.status_code)
        if pub.status_code in {200, 201}:
            pub_id = pub.json()["publication_id"]
            rel = client.post(
                f"/api/projects/{project_id}/publications/{pub_id}/publish",
                headers=headers,
            )
            ok("publication publish", rel.status_code)

    # Speech / ASR — always 200 (including missing key)
    dialects = client.get("/api/v1/ai/speech/dialects", headers=headers)
    ok("speech dialects", dialects.status_code)
    detect = client.post(
        "/api/v1/ai/speech/detect",
        headers=headers,
        json={"text": "Silav Newroz Zagros"},
    )
    ok("speech detect", detect.status_code)

    for dialect in ("sorani", "badini", "kurmanji"):
        up = client.post(
            "/api/v1/ai/speech/upload",
            headers=headers,
            files={"file": (f"e2e-{dialect}.wav", _wav(1.0), "audio/wav")},
            data={"project_id": project_id},
        )
        ok(f"speech upload {dialect}", up.status_code)
        key = up.json().get("audio_storage_key") if up.status_code in {200, 201} else f"e2e/{dialect}.wav"
        asr = client.post(
            "/api/v1/ai/speech/asr",
            headers=headers,
            json={"audio_storage_key": key, "dialect": dialect, "project_id": project_id},
        )
        ok(f"speech asr {dialect}", asr.status_code)
        if asr.status_code in {200, 201} and asr.json().get("job_id"):
            jid = asr.json()["job_id"]
            ok(f"speech job {dialect}", client.get(f"/api/v1/ai/speech/jobs/{jid}", headers=headers).status_code)

    missing = client.post(
        "/api/v1/ai/speech/asr",
        headers=headers,
        json={"audio_storage_key": "e2e/does-not-exist.wav", "dialect": "sorani"},
    )
    ok("speech asr missing-key", missing.status_code)

    kb = client.get("/api/knowledge/cultural-pack", headers=headers)
    ok("knowledge cultural-pack", kb.status_code)

    providers = client.get("/api/v1/ai/providers", headers=headers)
    ok("providers", providers.status_code)

    models = client.get("/api/v1/ai/models", headers=headers)
    ok("models registry", models.status_code)
    if models.status_code == 200:
        names = {m.get("name") for m in models.json()}
        assert_true(
            "lora models seeded",
            any("LORA" in (n or "").upper() or "KARDOKH" in (n or "").upper() for n in names),
            str(sorted(names)[:8]),
        )

    failed = [r for r in rows if not r["pass"]]
    out = {
        "api": BASE,
        "app": APP,
        "total": len(rows),
        "pass": len(rows) - len(failed),
        "fail": len(failed),
        "all_green": len(failed) == 0,
        "failed": failed,
    }
    print(json.dumps({k: out[k] for k in ("api", "app", "total", "pass", "fail", "all_green")}, indent=2))
    if failed:
        print("FAILURES:")
        for f in failed:
            print(f"  {f['name']} -> {f['code']} {f.get('detail')}")
    path = os.environ.get("E2E_OUT", "e2e_200_report.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("wrote", path)
    return 0 if out["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
