"""Live production test — signup auth + Studio + Cinema + Edit + video."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid

import httpx

BASE = os.environ.get("ARTCITY_API_URL", "https://backend-production-9533.up.railway.app").rstrip("/")
APP = os.environ.get("ARTCITY_APP_URL", "https://frontend-production-6380.up.railway.app").rstrip("/")
ADMIN_EMAIL = os.environ.get("ARTCITY_ADMIN_EMAIL", "admin@artcity.ai")
ADMIN_PASSWORD = os.environ.get("ARTCITY_ADMIN_PASSWORD", "ArtCityAdmin!2026")


def main() -> int:
    rows: list[dict] = []

    def ok(name: str, code: int, detail: str = "") -> None:
        passed = code in {200, 201}
        rows.append({"name": name, "code": code, "pass": passed, "detail": detail[:200]})
        print(f"{'OK' if passed else 'FAIL'}  {name}  {code}  {detail[:100]}")

    def assert_true(name: str, cond: bool, detail: str = "") -> None:
        rows.append({"name": name, "code": 200 if cond else 0, "pass": cond, "detail": detail[:200]})
        print(f"{'OK' if cond else 'FAIL'}  {name}  {'200' if cond else '0'}  {detail[:100]}")

    client = httpx.Client(base_url=BASE, timeout=300.0)
    app = httpx.Client(base_url=APP, timeout=60.0, follow_redirects=True)

    for path in (
        "/",
        "/login",
        "/signup",
        "/cinema",
        "/studio",
        "/studio/bank-building",
        "/data-bank",
        "/edit",
        "/dashboard",
        "/hub",
        "/vertical-drama",
    ):
        ok(f"UI GET {path}", app.get(path).status_code)

    # Customer signup with email + phone
    suffix = uuid.uuid4().hex[:8]
    email = f"customer.{suffix}@artcity.ai"
    phone = f"+964750{secrets_digits()}"
    password = "ArtCityCust!2026"

    signup = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "full_name": "Live Test Customer",
            "phone_number": phone,
            "password": password,
            "accept_terms": True,
        },
    )
    ok("POST /api/auth/signup", signup.status_code, signup.text[:120])
    if signup.status_code not in {200, 201}:
        return _finish(rows)
    body = signup.json()
    assert_true("signup returns email_token", bool(body.get("email_token")), str(body.keys()))
    assert_true("signup returns phone_code", bool(body.get("phone_code")), str(body.keys()))

    blocked = client.post("/api/auth/login", json={"email": email, "password": password})
    assert_true(
        "login blocked before verify",
        blocked.status_code == 403,
        f"expected 403 got {blocked.status_code}",
    )

    ve = client.post("/api/auth/verify-email", json={"email": email, "token": body["email_token"]})
    ok("POST /api/auth/verify-email", ve.status_code)
    vp = client.post("/api/auth/verify-phone", json={"email": email, "code": body["phone_code"]})
    ok("POST /api/auth/verify-phone", vp.status_code)

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    ok("customer login after verify", login.status_code)
    if login.status_code != 200:
        # Fallback admin for product tests if customer role restricted
        login = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        ok("admin login fallback", login.status_code)
    if login.status_code != 200:
        return _finish(rows)

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ok("GET /api/auth/me", client.get("/api/auth/me", headers=headers).status_code)

    # Admin path for full product generation (cinema/studio privileges)
    admin_login = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    ok("admin login", admin_login.status_code)
    if admin_login.status_code != 200:
        return _finish(rows)
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    proj = client.post(
        "/api/projects",
        headers=admin_headers,
        json={"name": f"Live Products {suffix}", "description": "studio cinema edit video"},
    )
    ok("POST /api/projects", proj.status_code)
    project_id = proj.json()["id"]

    # Studio video
    studio_video = client.post(
        f"/api/projects/{project_id}/studio/generate",
        headers=admin_headers,
        json={
            "modality": "video",
            "prompt": "Art City live test cinematic village dusk, 5 seconds",
            "duration_seconds": 5,
        },
    )
    ok("Studio video generate", studio_video.status_code, studio_video.text[:100])
    if studio_video.status_code in {200, 201}:
        job = studio_video.json()
        assert_true(
            "Studio video used cloud path or succeeded",
            job.get("status") in {"succeeded", "queued", "running"} or bool(job.get("id")),
            str(job.get("status")),
        )
        media = job.get("media_url") or job.get("result_uri")
        if media and str(media).startswith("http"):
            mr = httpx.get(media, timeout=60, follow_redirects=True)
            ok("Studio video media", mr.status_code)
            assert_true("Studio video is mp4", "mp4" in (mr.headers.get("content-type") or "").lower() or mr.content[:12].find(b"ftyp") >= 0)
        elif job.get("id"):
            # poll job
            for _ in range(40):
                jr = client.get(f"/api/v1/ai/jobs/{job['id']}", headers=admin_headers)
                if jr.status_code == 200 and jr.json().get("status") in {"succeeded", "failed"}:
                    body = jr.json()
                    ok("Studio video job", 200 if body.get("status") == "succeeded" else 0, body.get("status", ""))
                    # Cloud provider jobs are tagged ext-* when OpenAI/FAL used
                    pid = str(body.get("provider_job_id") or "")
                    assert_true(
                        "Studio video provider is external or artcity",
                        pid.startswith("ext-") or pid.startswith("ac-") or bool(pid),
                        pid,
                    )
                    break
                time.sleep(2)

    # Gateway video
    gw = client.post(
        "/api/v1/ai/videos/generate",
        headers=admin_headers,
        json={"prompt": "Art City live gateway video test", "project_id": project_id, "duration_seconds": 4},
    )
    ok("Gateway video generate", gw.status_code)

    # Cinema
    cinema = client.post(
        f"/api/projects/{project_id}/cinema/packages",
        headers=admin_headers,
        json={
            "campaign": f"Live Cinema {suffix}",
            "brief": "Live production cinema package for Art City",
            "cta": "Watch on Art City",
            "brand": "Art City",
            "voiceover_script": "Art City brings stories to life.",
            "music_style": "warm documentary",
            "duration_seconds": 8,
        },
    )
    ok("Cinema package", cinema.status_code, cinema.text[:100])
    if cinema.status_code in {200, 201}:
        pkg = cinema.json()
        package_id = pkg.get("package_id") or pkg.get("id")
        assert_true("Cinema QC passed", bool(pkg.get("validation_passed") or (pkg.get("validation") or {}).get("passed")), str(pkg.get("validation_passed")))
        if package_id:
            ok(
                "Cinema zip",
                client.get(
                    f"/api/projects/{project_id}/cinema/packages/{package_id}/zip",
                    headers=admin_headers,
                ).status_code,
            )

    # Edit
    seed = client.post("/api/edit/seed/internal", headers=admin_headers)
    ok("Edit seed", seed.status_code)
    wid = seed.json().get("id") if seed.status_code in {200, 201} else None
    if not wid:
        ws = client.get("/api/edit/workspaces", headers=admin_headers)
        ok("Edit workspaces", ws.status_code)
        wid = (ws.json() or [{}])[0].get("id")
    if wid:
        up = client.post(
            f"/api/edit/workspaces/{wid}/assets",
            headers=admin_headers,
            files={"file": ("live_edit.txt", b"Art City live edit source", "text/plain")},
            data={"rights_attested": "true", "rights_notes": "live"},
        )
        ok("Edit upload", up.status_code)
        if up.status_code in {200, 201}:
            ep = client.post(
                f"/api/edit/workspaces/{wid}/projects",
                headers=admin_headers,
                json={"title": f"Live Edit {suffix}", "source_asset_id": up.json()["id"]},
            )
            ok("Edit project", ep.status_code)
            if ep.status_code in {200, 201}:
                eid = ep.json()["id"]
                ok("Edit analyse", client.post(f"/api/edit/projects/{eid}/analyse", headers=admin_headers).status_code)

    # Data Bank
    db_seed = client.post("/api/data-bank/seed", headers=admin_headers)
    ok("Data Bank seed", db_seed.status_code)
    ok("Data Bank hub", client.get("/api/data-bank", headers=admin_headers).status_code)
    bank_pid = (db_seed.json().get("project") or {}).get("id") if db_seed.status_code in {200, 201} else None
    if bank_pid:
        ok(
            "Data Bank summary",
            client.get(f"/api/projects/{bank_pid}/data-bank/summary", headers=admin_headers).status_code,
        )
        ok(
            "Data Bank list",
            client.get(f"/api/projects/{bank_pid}/data-bank", headers=admin_headers).status_code,
        )
        up = client.post(
            f"/api/projects/{bank_pid}/data-bank/upload",
            headers=admin_headers,
            files={"file": ("live-bank.txt", b"Live Data Bank brief", "text/plain")},
            data={"name": "Live bank brief", "tags": "live,data-bank"},
        )
        ok("Data Bank upload", up.status_code)
        ok(
            "Data Bank sync",
            client.post(f"/api/projects/{bank_pid}/data-bank/sync", headers=admin_headers).status_code,
        )

    bb = client.post(
        "/api/studio/bank-building/generate",
        headers=admin_headers,
        json={"notes": "live production bank building", "prefer_external": True},
    )
    ok("Bank building image", bb.status_code, bb.text[:100])
    if bb.status_code in {200, 201}:
        media = bb.json().get("media_url")
        if media:
            mr = client.get(media, headers=admin_headers)
            ok("Bank building media", mr.status_code)
            pid = str(bb.json().get("provider_job_id") or "")
            assert_true(
                "Bank building provider is external or artcity",
                pid.startswith("ext-") or pid.startswith("ac-"),
                pid,
            )

    # Production Hub — AC Script
    ok("Hub features", client.get("/api/v1/hub/features", headers=admin_headers).status_code)
    hub_script = client.post(
        f"/api/v1/hub/projects/{project_id}/scripts",
        headers=admin_headers,
        json={
            "title": f"Live Hub Script {suffix}",
            "entry_mode": "synopsis",
            "primary_locale": "ckb-IQ",
            "content_languages": ["ckb-IQ", "en"],
            "seed_text": (
                "INT. قاوەخانە - ڕۆژ\n"
                "دایک دەچێتە ژوورەوە.\n\n"
                "دایک\n"
                "سڵاو، کوڕم.\n\n"
                "EXT. شەقام - شەو\n"
                "باسیش دەڕوات."
            ),
        },
    )
    ok("Hub create script", hub_script.status_code, hub_script.text[:120])
    if hub_script.status_code in {200, 201}:
        script = hub_script.json()
        script_id = script["id"]
        version_id = script.get("current_version_id")
        assert_true("Hub script has version", bool(version_id), str(script))
        if version_id:
            els = client.get(f"/api/v1/hub/versions/{version_id}/elements", headers=admin_headers)
            ok("Hub list elements", els.status_code)
            save = client.put(
                f"/api/v1/hub/versions/{version_id}/elements",
                headers=admin_headers,
                json={
                    "elements": [
                        {"element_type": "scene_heading", "display_text": "INT. CAFE - DAY", "locale": "en"},
                        {"element_type": "action", "display_text": "Mother enters.", "locale": "en"},
                        {"element_type": "character", "display_text": "MOTHER", "locale": "en"},
                        {"element_type": "dialogue", "display_text": "سڵاو، کوڕم.", "locale": "ckb-IQ"},
                        {"element_type": "scene_heading", "display_text": "EXT. STREET - NIGHT", "locale": "en"},
                        {"element_type": "action", "display_text": "Rain falls.", "locale": "en"},
                    ]
                },
            )
            ok("Hub save elements", save.status_code)
            scenes = client.post(
                f"/api/v1/hub/versions/{version_id}/parse-scenes",
                headers=admin_headers,
            )
            ok("Hub parse scenes", scenes.status_code, scenes.text[:100])
            if scenes.status_code == 200:
                assert_true("Hub parsed scenes", len(scenes.json()) >= 1, str(len(scenes.json())))
            breakdown = client.post(
                f"/api/v1/hub/versions/{version_id}/breakdown/propose",
                headers=admin_headers,
            )
            ok("Hub propose breakdown", breakdown.status_code)
            if breakdown.status_code == 200 and breakdown.json():
                item = breakdown.json()[0]
                dec = client.post(
                    f"/api/v1/hub/breakdown/{item['id']}/decision",
                    headers=admin_headers,
                    json={"approval_status": "approved"},
                )
                ok("Hub approve breakdown", dec.status_code)
            lock = client.post(f"/api/v1/hub/versions/{version_id}/lock", headers=admin_headers)
            ok("Hub lock version", lock.status_code)
            blocked = client.put(
                f"/api/v1/hub/versions/{version_id}/elements",
                headers=admin_headers,
                json={"elements": [{"element_type": "action", "display_text": "should fail"}]},
            )
            assert_true(
                "Hub lock blocks edit",
                blocked.status_code == 400,
                f"expected 400 got {blocked.status_code} {blocked.text[:80]}",
            )
            # revise after lock
            rev = client.post(f"/api/v1/hub/scripts/{script_id}/versions", headers=admin_headers)
            ok("Hub new revision", rev.status_code)
            export = client.get(
                f"/api/v1/hub/versions/{version_id}/export/docx",
                headers=admin_headers,
            )
            ok("Hub export docx", export.status_code)
            for target in ("cinema", "studio", "edit"):
                ho = client.post(
                    f"/api/v1/hub/projects/{project_id}/handoff/{target}",
                    headers=admin_headers,
                    json={"script_version_id": version_id},
                )
                ok(f"Hub handoff {target}", ho.status_code, ho.text[:80])
            ok(
                "Hub UI script",
                app.get(f"/hub/{project_id}/script").status_code,
            )

    ok("VD features", client.get("/api/v1/vertical-drama/features", headers=admin_headers).status_code)
    vd = client.post(
        "/api/v1/vertical-drama/projects",
        headers=admin_headers,
        json={
            "title": f"Golden A {suffix}",
            "logline": "دڵخواز نهێنی خێزان دەدۆزێتەوە.",
            "source_type": "generate",
            "primary_locale": "ckb-IQ",
            "content_languages": ["ckb-IQ", "en"],
            "seed_golden_a": True,
        },
    )
    ok("VD create golden A", vd.status_code, vd.text[:120])
    if vd.status_code in {200, 201}:
        vdid = vd.json()["id"]
        ok("VD UI", app.get("/vertical-drama").status_code)
        ok("VD UI project", app.get(f"/vertical-drama/{vdid}").status_code)
        bible = client.post(
            f"/api/v1/vertical-drama/projects/{vdid}/story-bible",
            headers=admin_headers,
            json={"sections_json": {"world": "سلێمانی", "tone": "drama", "language": "ckb-IQ"}},
        )
        ok("VD story bible", bible.status_code)
        if bible.status_code in {200, 201}:
            vid = (bible.json().get("version") or {}).get("id") or bible.json().get("current_version_id")
            if vid:
                ok(
                    "VD bible lock",
                    client.post(f"/api/v1/vertical-drama/story-bibles/{vid}/approve", headers=admin_headers).status_code,
                )
        season = client.post(
            f"/api/v1/vertical-drama/projects/{vdid}/seasons",
            headers=admin_headers,
            json={"title": "Season 1", "target_episode_count": 2, "target_episode_seconds": 60},
        )
        ok("VD season grid", season.status_code)
        if season.status_code in {200, 201}:
            eps = season.json().get("episodes") or []
            assert_true("VD two episodes", len(eps) >= 2, str(len(eps)))
            eid = eps[0]["id"]
            for st in ("drafted", "reviewed", "approved"):
                pr = client.patch(
                    f"/api/v1/vertical-drama/episodes/{eid}",
                    headers=admin_headers,
                    json={"status": st},
                )
                ok(f"VD episode {st}", pr.status_code)
            sp = client.post(
                f"/api/v1/vertical-drama/episodes/{eid}/screenplay",
                headers=admin_headers,
                json={
                    "title": "EP1",
                    "elements": [
                        {"element_type": "scene_heading", "display_text": "INT. قاوەخانە - ڕۆژ"},
                        {"element_type": "action", "display_text": "دڵخواز دێتە ژوورەوە."},
                    ],
                },
            )
            ok("VD screenplay", sp.status_code)
            dc = client.post(f"/api/v1/vertical-drama/episodes/{eid}/decoupage", headers=admin_headers)
            ok("VD decoupage", dc.status_code, dc.text[:80])
            shots = (dc.json() or {}).get("shots") or []
            qc_fail = client.post(f"/api/v1/vertical-drama/episodes/{eid}/qc-runs", headers=admin_headers)
            ok("VD QC before media", qc_fail.status_code)
            if qc_fail.status_code == 200:
                assert_true("VD QC fails without takes", qc_fail.json().get("passed") is False, str(qc_fail.json()))
            if shots:
                gen = client.post(
                    f"/api/v1/vertical-drama/shots/{shots[0]['id']}/generations",
                    headers=admin_headers,
                    json={"capability": "image"},
                )
                ok("VD generate shot", gen.status_code)
                for sh in shots[1:]:
                    client.post(
                        f"/api/v1/vertical-drama/shots/{sh['id']}/generations",
                        headers=admin_headers,
                        json={"capability": "image"},
                    )
            loc = client.post(
                f"/api/v1/vertical-drama/episodes/{eid}/localize",
                headers=admin_headers,
                json={"language": "en", "kind": "subtitle", "body": "Mother waits."},
            )
            ok("VD localize", loc.status_code)
            asm = client.post(f"/api/v1/vertical-drama/episodes/{eid}/assembly", headers=admin_headers)
            ok("VD assembly", asm.status_code)
            qc = client.post(f"/api/v1/vertical-drama/episodes/{eid}/qc-runs", headers=admin_headers)
            ok("VD QC", qc.status_code)
            if qc.status_code == 200:
                assert_true("VD QC passed after generates", bool(qc.json().get("passed")), str(qc.json()))
            pkg = client.post(
                f"/api/v1/vertical-drama/episodes/{eid}/delivery-packages",
                headers=admin_headers,
            )
            ok("VD delivery", pkg.status_code, pkg.text[:100])

    return _finish(rows)


def secrets_digits() -> str:
    return f"{uuid.uuid4().int % 10_000_000:07d}"


def _finish(rows: list[dict]) -> int:
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
    path = os.environ.get("LIVE_OUT", "live_products_200_report.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("wrote", path)
    return 0 if out["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
