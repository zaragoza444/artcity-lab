#!/usr/bin/env python3
"""Apply Cloudflare DNS for ai.artcity.group → Railway frontend."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ZONE_NAME = "artcity.group"
CNAME_NAME = "ai"
CNAME_TARGET = "uzddkjs6.up.railway.app"
TXT_NAME = "_railway-verify.ai"
TXT_VALUE = (
    "railway-verify=d438cc6d54fa7fc2c6721f3ccd2f09990730d80621c913b2a3e764d4a0322fdb"
)

ROOT = Path(__file__).resolve().parent
TOKEN_FILES = (
    ROOT / ".cloudflare.artcity.local",
    Path.home() / "nova" / ".cloudflare.artcity.local",
    Path(r"C:\Users\novac\nova\.cloudflare.artcity.local"),
)


def load_token() -> str:
    import os

    token = (os.environ.get("ARTCITY_CF_TOKEN") or os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()
    if token:
        return token
    for path in TOKEN_FILES:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() in ("CLOUDFLARE_API_TOKEN", "ARTCITY_CF_TOKEN"):
                return v.strip().strip('"').strip("'")
    raise SystemExit(
        "Missing token. Set ARTCITY_CF_TOKEN or create .cloudflare.artcity.local "
        "with CLOUDFLARE_API_TOKEN=..."
    )


def cf(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {url} -> {e.code} {e.read().decode()}") from e


def main() -> None:
    token = load_token()
    zones = cf("GET", f"https://api.cloudflare.com/client/v4/zones?name={ZONE_NAME}", token)
    if not zones.get("result"):
        raise SystemExit(f"Zone {ZONE_NAME} not found for this token")
    zone_id = zones["result"][0]["id"]
    print(f"zone={ZONE_NAME} id={zone_id}")

    recs = cf(
        "GET",
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?per_page=100",
        token,
    )["result"]

    # CNAME ai → Railway
    ai = [r for r in recs if r["name"] == "ai.artcity.group"]
    for r in list(ai):
        if r["type"] != "CNAME":
            cf("DELETE", f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{r['id']}", token)
            print(f"deleted {r['type']} {r['name']}")
            ai.remove(r)
    cname_body = {
        "type": "CNAME",
        "name": CNAME_NAME,
        "content": CNAME_TARGET,
        "ttl": 1,
        "proxied": True,
    }
    if ai:
        out = cf(
            "PUT",
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{ai[0]['id']}",
            token,
            cname_body,
        )
        print("updated CNAME ai ->", out["result"]["content"], "proxied=", out["result"]["proxied"])
    else:
        out = cf(
            "POST",
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
            token,
            cname_body,
        )
        print("created CNAME ai ->", out["result"]["content"])

    # TXT verify
    txts = [
        r
        for r in recs
        if r["name"] == "_railway-verify.ai.artcity.group" and r["type"] == "TXT"
    ]
    txt_body = {
        "type": "TXT",
        "name": TXT_NAME,
        "content": TXT_VALUE,
        "ttl": 1,
        "proxied": False,
    }
    if txts:
        out = cf(
            "PUT",
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{txts[0]['id']}",
            token,
            txt_body,
        )
        print("updated TXT", out["result"]["name"])
        for extra in txts[1:]:
            cf("DELETE", f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{extra['id']}", token)
            print("deleted extra TXT", extra["id"])
    else:
        out = cf(
            "POST",
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
            token,
            txt_body,
        )
        print("created TXT", out["result"]["name"])

    print("done — wait 1–5 min, then check https://ai.artcity.group")


if __name__ == "__main__":
    main()
