"""Export Art City AI Studio first-party source into an HTML + PDF report."""

from __future__ import annotations

import html
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML_OUT = ROOT / "Art-City-AI-Studio-Full-Source-Code-Report.html"
PDF_OUT = ROOT / "Art-City-AI-Studio-Full-Source-Code-Report.pdf"

SKIP_DIRS = {
    ".git",
    ".next",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "coverage",
    ".cursor",
    "agent-transcripts",
    "terminals",
}
SKIP_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    ".env",
    ".env.local",
    "live_products_200_report.json",
    "smoke_200_report.json",
}
SKIP_SUFFIXES = {
    ".pdf",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".mp4",
    ".zip",
    ".woff",
    ".woff2",
    ".ico",
    ".bin",
    ".pt",
    ".safetensors",
    ".pkl",
}
INCLUDE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".css",
    ".json",
    ".md",
    ".toml",
    ".yml",
    ".yaml",
    ".ini",
    ".txt",
    ".sql",
    ".bat",
    ".ps1",
    ".sh",
    ".css",
}
INCLUDE_NAMES = {
    "Dockerfile",
    "docker-compose.yml",
    "railway.toml",
    ".gitignore",
    "AGENTS.md",
    "README.md",
}
MAX_BYTES = 400_000


def collect_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_NAMES or path.name.startswith(".env"):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.name not in INCLUDE_NAMES and path.suffix.lower() not in INCLUDE_SUFFIXES:
            continue
        if path.stat().st_size > MAX_BYTES:
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(ROOT)).replace("\\", "/").lower())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def section_files(files: list[Path], prefix: str) -> list[Path]:
    return [p for p in files if rel(p).startswith(prefix)]


def main() -> int:
    files = collect_files()
    backend = section_files(files, "backend/")
    frontend = section_files(files, "frontend/")
    docs = section_files(files, "docs/")
    other = [p for p in files if p not in backend and p not in frontend and p not in docs]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    parts: list[str] = []
    parts.append(
        """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<title>Art City AI Studio — Full Source Code Report</title>
<style>
  @page { size: A4; margin: 16mm 14mm; }
  body { font-family: Calibri, "Segoe UI", sans-serif; color: #111; font-size: 11px; line-height: 1.45; }
  h1 { font-size: 26px; margin: 0 0 8px; letter-spacing: 0.04em; }
  h2 { font-size: 16px; margin: 28px 0 10px; border-bottom: 1px solid #c5a15e; padding-bottom: 4px; color: #3a2e16; }
  h3 { font-size: 13px; margin: 18px 0 6px; color: #222; }
  .gold { color: #8a6a2a; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0 16px; }
  th, td { border: 1px solid #ddd; padding: 5px 7px; text-align: left; vertical-align: top; }
  th { background: #f6f1e6; }
  .cover { margin-bottom: 28px; }
  .muted { color: #555; }
  ul.toc { columns: 2; column-gap: 24px; }
  pre { background: #f7f7f5; border: 1px solid #e4e0d6; padding: 8px; font-size: 8.2px; line-height: 1.35;
        white-space: pre-wrap; word-break: break-word; font-family: Consolas, "Courier New", monospace; }
  .file { page-break-inside: avoid; }
  .file h3 { font-family: Consolas, monospace; font-size: 11px; }
</style></head><body>
"""
    )
    parts.append(
        f"""<div class="cover">
<h1>ART CITY AI STUDIO</h1>
<p class="gold"><strong>Full source code report — backend and frontend</strong></p>
<p>Private Art City product. Cinema · Studio · Vertical Drama · Edit · Hub · Publish.</p>
<p class="muted">Generated: {html.escape(generated)}<br/>
Workspace: {html.escape(str(ROOT))}<br/>
Files in this export: {len(files)} (excludes node_modules, venv, .git, secrets, binaries)<br/>
Production app: https://frontend-production-6380.up.railway.app<br/>
Production API: https://backend-production-9533.up.railway.app</p>
</div>
"""
    )
    parts.append(
        """<h2>1. Product map</h2>
<table><tr><th>Product</th><th>UI</th><th>API</th><th>Role</th></tr>
<tr><td>Art City Cinema</td><td>/cinema</td><td>/api/cinema, /api/v1/ai</td><td>Advertising campaigns, QC, ZIP</td></tr>
<tr><td>Art City Studio</td><td>/studio</td><td>/api/studio, /api/projects</td><td>Single image/video/voice/music takes</td></tr>
<tr><td>AC Vertical Drama</td><td>/vertical-drama</td><td>/api/v1/vertical-drama</td><td>IP factory: vault, bible, episodes, 9:16, QC, delivery</td></tr>
<tr><td>Art City Edit</td><td>/edit</td><td>/api/edit</td><td>Long-form analyse, timeline, multi-ratio export</td></tr>
<tr><td>Production Hub</td><td>/hub</td><td>/api/v1/hub</td><td>AC Script, breakdown, handoff</td></tr>
<tr><td>Publish</td><td>/publish</td><td>/api/publications</td><td>Masters, checksums, channel release</td></tr>
<tr><td>Model Gateway</td><td>—</td><td>/api/v1/ai</td><td>Sole inference entry; cost ledger</td></tr>
<tr><td>Data Bank / Data Lab</td><td>/data-bank, /data-lab</td><td>/api/data-bank, /api/data-lab</td><td>Assets, ingest, annotation, rights</td></tr>
</table>
<p>Shared core: auth/RBAC, projects, MinIO assets, Postgres, Redis, ckb-IQ/RTL, Model Gateway. Domain modules own their tables and routes. AI is never called from the UI.</p>
"""
    )
    parts.append(
        """<h2>2. Architecture freeze</h2>
<table><tr><th>Layer</th><th>Implementation</th></tr>
<tr><td>Frontend</td><td>Next.js App Router under frontend/src (TypeScript)</td></tr>
<tr><td>Backend</td><td>FastAPI under backend/app; Alembic migrations 0001–0007</td></tr>
<tr><td>Data</td><td>PostgreSQL (projects + domain tables), Redis queue, MinIO/S3 assets</td></tr>
<tr><td>Auth</td><td>JWT access + refresh; session validate/refresh in frontend/src/lib/auth.ts and api.ts</td></tr>
<tr><td>Vertical Drama identity</td><td>Shared project_id + domain vd_project_id; flag VD_FEATURE_ENABLED</td></tr>
<tr><td>Deploy</td><td>Railway Docker: railway up backend|frontend --path-as-root</td></tr>
<tr><td>Out of scope</td><td>Nova, Alltra, foreign chains, shared monorepos</td></tr>
</table>
<h3>Alembic</h3>
<ul>
<li>0001_initial — platform projects, users, generations, costs</li>
<li>0002_ai_core — datasets, models, knowledge, evaluations</li>
<li>0003_data_lab_files — Data Lab file inventory</li>
<li>0004_art_city_edit — Edit workspaces and timelines</li>
<li>0005_customer_signup — signup verification</li>
<li>0006_production_hub — Hub scripts, versions, breakdown, events</li>
<li>0007_vertical_drama — IP vault, canon, bible, seasons, shots, QC, delivery</li>
</ul>
"""
    )
    parts.append("<h2>3. File inventory</h2>")
    for title, group in (
        ("Backend", backend),
        ("Frontend", frontend),
        ("Docs", docs),
        ("Root / deploy", other),
    ):
        parts.append(f"<h3>{html.escape(title)} ({len(group)} files)</h3><ul class='toc'>")
        for p in group:
            parts.append(f"<li>{html.escape(rel(p))}</li>")
        parts.append("</ul>")

    parts.append("<h2>4. Full source listing</h2>")
    parts.append("<p class='muted'>Each first-party text file follows. Binary, lockfiles, caches, and secrets are omitted.</p>")
    for p in files:
        body = html.escape(read_text(p))
        parts.append(
            f"<div class='file'><h3>{html.escape(rel(p))}</h3><pre>{body}</pre></div>"
        )

    parts.append("</body></html>")
    HTML_OUT.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {HTML_OUT} ({len(files)} files)")

    edge_candidates = [
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ]
    browser = next((c for c in edge_candidates if c.exists()), None)
    if not browser:
        print("No Edge/Chrome found; HTML report is ready.", file=sys.stderr)
        return 2

    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        f"--print-to-pdf={PDF_OUT}",
        "--no-pdf-header-footer",
        HTML_OUT.resolve().as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not PDF_OUT.exists():
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        print("PDF conversion failed; HTML report is ready.", file=sys.stderr)
        return 3
    print(f"Wrote {PDF_OUT} ({PDF_OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
