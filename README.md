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

## Art City Cinema vs Art City Studio

| Product | Purpose | Outputs |
|---------|---------|---------|
| **Art City Cinema** | Complete advertising campaigns | Hero film, social cutdowns, music, VO, end card, campaign manifest, technical QC, ZIP |
| **Art City Studio** | Individual production assets | Single image / video / voice / music / scene takes |

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

## Project layout

- `frontend/` — Next.js, React, TypeScript, Tailwind CSS
- `backend/` — FastAPI, SQLAlchemy, Alembic
- `docker-compose.yml` — PostgreSQL, Redis, MinIO

## Ownership principle

Art City owns the platform, source code, data, characters, workflows, and IP. External AI models are replaceable providers only.
