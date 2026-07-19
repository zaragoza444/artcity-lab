# Staging and deploy controls

## Environments

| Environment | Purpose |
|-------------|---------|
| development | Local Docker + uvicorn |
| staging | Railway `staging` environment — separate Postgres/Redis/MinIO vars |
| production | Railway `production` — deploy from `main` only |

## Railway staging

1. In the Art City Railway project, create environment `staging`.
2. Duplicate Postgres / Redis / MinIO (or add new plugins) into staging.
3. Set per-environment variables:
   - `SECRET_KEY` (unique)
   - `CORS_ORIGINS` (staging frontend URL)
   - `NEXT_PUBLIC_API_URL` (staging API URL)
   - `EXTERNAL_PROVIDERS_ENABLED=true|false`
   - `AUTH_REQUIRED=true`
4. Deploy backend/frontend into `staging` before promoting to production.

## GitHub

- Protect `main`: PR required, ≥1 reviewer, no force push
- CI: `.github/workflows/ci.yml` (pytest + Next lint/build)
- Never commit `.env`, datasets, or model weights

## Branch flow

`feature/*` → `development` → `staging` → `main`
