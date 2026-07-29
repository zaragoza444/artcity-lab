# Art City AI Studio

**Private Art City project.** Standalone local MVP for Art City’s proprietary AI content-generation platform (video, image, audio, voice, music).

Not part of Nova. Not part of Alltra. No shared stack with either.

## Prerequisites

- Docker Desktop (for PostgreSQL, Redis, MinIO)
- Python 3.11+
- Node.js 20+
- Windows CMD or PowerShell

## Quick start

### 1. Infrastructure

```bat
cd C:\Users\novac\Documents\art-city-ai-studio
copy .env.example .env
docker compose up -d
```

Services:

| Service        | URL                         |
|----------------|-----------------------------|
| Frontend       | http://localhost:3000       |
| Backend API    | http://localhost:8000       |
| API Docs       | http://localhost:8000/docs  |
| MinIO Console  | http://localhost:9001       |

MinIO login: `artcity_minio` / `artcity_minio_secret`

### 2. Backend

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bat
cd frontend
npm install
npm run dev
```

## Publish (delivery pipeline)

Open **http://localhost:3000/publish**

1. Select a cinema package  
2. Package masters (16:9 / 9:16 / 1:1 + stems)  
3. Pass delivery checklist + checksums  
4. Release to Art City channel  

Outputs: `MASTER_MANIFEST.json`, `DELIVERY_REPORT.md`, published masters in MinIO.

## Art City Cinema · Studio · Edit · Publish

| Product | Purpose | Outputs |
|---------|---------|---------|
| **Art City Cinema** | Complete advertising campaigns | Hero film, social cutdowns, music, VO, end card, campaign manifest, technical QC, ZIP |
| **Art City Studio** | Individual production assets | Single image / video / voice / music / scene takes |
| **Art City Edit** | Long-form editing & social repurposing | Upload → analyse → candidate clips → timeline → multi-ratio export + QC (Art City approval + entitlements) |
| **Art City Publish** | Delivery packaging | Masters, checklist, checksums, channel release |

### Art City Edit (local)

Open **http://localhost:3000/edit**

```bat
cd backend
venv\Scripts\activate
alembic upgrade head
python scripts\seed_edit.py
```

1. Seed the internal Art City Edit workspace (or call `POST /api/edit/seed/internal` as admin)  
2. Upload long-form video with rights attestation  
3. Run analysis (start worker: `python -m app.worker`)  
4. Pin candidates → timeline → approve → render multi-ratio package  

PRD: [`docs/ART_CITY_EDIT_PRD.md`](docs/ART_CITY_EDIT_PRD.md)

## Cinema technical QC

Every Cinema render automatically runs deep validation:

- Video duration · aspect ratio (true 16:9 / 9:16 / 1:1) · resolution presets (1920×1080, 1080×1920, 1080×1080)
- Frame rate documented (24 fps) · audio sync · loudness · voice clarity proxy
- End card branding/CTA · SHA-256 · package completeness (six outputs)
- Provider cost + generation history (prompt, model, version)

Demo campaign (real Art City brand brief):

```bat
cd backend
venv\Scripts\activate
python scripts\demo_art_city_campaign.py
```

ZIP + manifest land in `backend/demo_output/`.

## Cloud deploy (Railway)

Private stack: **Postgres + Redis + S3 bucket + FastAPI + Next.js**.

1. `railway login` (if needed)
2. From repo root: `railway init -n art-city-ai-studio -y`
3. Add data: `railway add --database postgres` and `railway add --database redis`
4. Create bucket: `railway bucket create art-city-assets`
5. Deploy API: `railway up backend --path-as-root -s backend -y`
6. Generate API domain: `railway domain -s backend`
7. Set frontend `NEXT_PUBLIC_API_URL` to the API domain, deploy: `railway up frontend --path-as-root -s frontend -y`
8. Generate frontend domain and set backend `CORS_ORIGINS` to that URL

GitHub autodeploy (optional): connect each service to `zaragoza444/artcity-lab` on `main`.
Gitea mirror: `https://gitea.d-bis.org/zaragoza444/artcity-lab`.

## Project layout

- `frontend/` — Next.js, React, TypeScript, Tailwind CSS
- `backend/` — FastAPI, SQLAlchemy, Alembic
- `docker-compose.yml` — PostgreSQL, Redis, MinIO

## Branch policy

`feature/*` → `development` → `staging` → `main`

Production deploys only from `main` after approval. Never commit `.env`, datasets, or model weights.

## API documentation

- **Complete reference:** [docs/API.md](docs/API.md)
- **Swagger UI:** http://localhost:8000/docs · https://backend-production-9533.up.railway.app/docs
- **ReDoc:** http://localhost:8000/redoc

## AI Core

Art City AI Core adds Model Gateway, Data Lab, Rights, Model Registry, Training, Evaluations, and async inference workers under Cinema / Studio / Publish. See [docs/ART_CITY_AI_CORE_DIRECTIVE.md](docs/ART_CITY_AI_CORE_DIRECTIVE.md).

Local worker (after Redis is up):

```bat
cd backend
venv\Scripts\activate
python -m app.worker
```

Default admin (after seed): set `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` in the environment — do not commit credentials.

## Ownership principle

Art City owns the platform, source code, data, characters, workflows, datasets, fine-tuned models, and IP. External AI models are optional replaceable providers only.
