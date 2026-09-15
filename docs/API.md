# Art City AI Studio — Complete API Documentation

**Version:** 1.2.0  
**Base URLs**

| Environment | Base URL |
|-------------|----------|
| Production | `https://backend-production-9533.up.railway.app` |
| Local | `http://localhost:8000` |

**Interactive docs (OpenAPI)**

| Surface | URL |
|---------|-----|
| Swagger UI | `{BASE}/docs` |
| ReDoc | `{BASE}/redoc` |
| OpenAPI JSON | `{BASE}/openapi.json` |

Live Swagger: https://backend-production-9533.up.railway.app/docs

---

## Authentication

Most endpoints require a Bearer JWT.

1. `POST /api/auth/login` with email + password  
2. Send header: `Authorization: Bearer {access_token}`

**Public (no auth):** `GET /`, `GET /health`, `POST /api/auth/login`, `POST /api/auth/refresh`  
**Media file GETs** (`/api/media/...`, `/api/assets/file/...`, cinema zip/manifest binary GETs under protected routers) — cinema/publishing routes require auth; studio media file routes are currently open for preview embedding.

Default seeded admin (change immediately via env `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD`):

- Email: value of `DEFAULT_ADMIN_EMAIL`
- Password: value of `DEFAULT_ADMIN_PASSWORD` (never commit real passwords to git)

### Roles

| Role | Notes |
|------|--------|
| `super_admin` | Full access |
| `administrator` | Admin + user management |
| `producer` | Privileged production / training / rights |
| `project_manager` | Dataset upload (with AI ops) |
| `ai_operator` | Datasets, training, model register |
| `creative_director` / `writer` / `animator` / `editor` / `reviewer` / `viewer` | Standard production roles |

Privileged actions (datasets upload, rights approve, training, model promote) require elevated roles — see endpoint notes below.

---

## Quick start

```bash
# Login
curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$DEFAULT_ADMIN_EMAIL\",\"password\":\"$DEFAULT_ADMIN_PASSWORD\"}"

# Use token
export TOKEN=...

# List projects
curl -s "$BASE/api/projects" -H "Authorization: Bearer $TOKEN"

# Generate Kardokh image via Model Gateway
curl -s -X POST "$BASE/api/v1/ai/images/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id":"PROJECT_UUID",
    "prompt":"Kardokh on a Zagros ridge at golden hour",
    "character_key":"kardokh",
    "character_name":"Kardokh"
  }'
```

---

## 1. System

### `GET /`

Service metadata.

**Response**

```json
{
  "name": "Art City AI Studio",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "gateway": "/api/v1/ai"
}
```

### `GET /health`

Dependency health check. **Public.**

**Response**

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "minio": "ok"
}
```

`status` is `ok` when all three are ok; otherwise `degraded`.

---

## 2. Auth — `/api/auth`

### `POST /api/auth/login` — Public

**Body**

| Field | Type | Required |
|-------|------|----------|
| email | string | yes |
| password | string | yes |

**Response `200` — TokenResponse**

| Field | Type |
|-------|------|
| access_token | string |
| refresh_token | string |
| token_type | `"bearer"` |
| role | string |
| email | string |
| full_name | string |
| user_id | string |

**Errors:** `401` invalid credentials

### `POST /api/auth/refresh` — Public

**Body:** `{ "refresh_token": "..." }`  
**Response:** same as login

### `GET /api/auth/me`

Current user profile.

### `GET /api/auth/users`

List users. **Admin / super_admin only.**

### `POST /api/auth/users`

Create user. **Admin / super_admin only.**

**Body**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| email | string | yes | |
| full_name | string | yes | |
| password | string | yes (min 8) | |
| role | string | no | `viewer` |

---

## 3. Model Gateway — `/api/v1/ai`

Single entry point for Art City–controlled generation. Cinema/Studio should call Gateway (Studio also wraps Gateway internally).

### Generate

| Method | Path | Modality |
|--------|------|----------|
| POST | `/api/v1/ai/images/generate` | image |
| POST | `/api/v1/ai/videos/generate` | video |
| POST | `/api/v1/ai/voices/generate` | voice |
| POST | `/api/v1/ai/audio/generate` | audio |
| POST | `/api/v1/ai/music/generate` | music |

**Status:** `201`  
**Body (GenerateRequest)**

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| project_id | UUID string | yes | | Must exist |
| prompt | string | yes | | |
| model | string | no | routed | Optional override |
| character_key | string | no | | e.g. `kardokh`, `kurdiya` |
| character_name | string | no | | Display / VO brand |
| duration_seconds | float | no | `4.0` | 0.5–60 |
| dialogue_lines | string[] | no | | Voice conversations |
| prefer_external | bool | no | `false` | Force external fallback |
| params | object | no | | Extra metadata |

**Response:** `GenerationJobOut` (see Shared models)

Routing uses Model Registry + route rules. Character keys prefer Art City adapters (`AC-KARDOKH-IMAGE-v1`, `AC-KURDIYA-IMAGE-v1`).

### Jobs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ai/jobs/{job_id}` | Job status + media URLs |
| POST | `/api/v1/ai/jobs/{job_id}/cancel` | Cancel queued/running |
| POST | `/api/v1/ai/jobs/{job_id}/retry` | New job from prior params (`201`) |

### Models & providers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ai/models` | Registered models (gateway view) |
| GET | `/api/v1/ai/models/{model_id}` | One model |
| GET | `/api/v1/ai/providers` | `{ name, healthy }` list |

**Providers:** `stub`, `artcity-image`, `artcity-video`, `artcity-asr`, `external-fallback`

### Speech (production ASR)

Kurdish ASR pipeline: MinIO audio required, pluggable engine (`ASR_ENGINE=pilot` default), persisted `GenerationJob` (`modality=speech`, provider `artcity-asr`, model `AC-KURDISH-ASR-v1`), transcript JSON + VTT/SRT assets, optional Data Lab annotation.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ai/speech/dialects` | Supported dialects + model/engine |
| POST | `/api/v1/ai/speech/detect` | Text dialect/script detect |
| POST | `/api/v1/ai/speech/upload` | Multipart `file` → MinIO key |
| POST | `/api/v1/ai/speech/asr` | Transcribe existing MinIO key; persist job |
| GET | `/api/v1/ai/speech/jobs/{job_id}` | Job + manifest |
| GET | `/api/v1/ai/speech/jobs/{job_id}/transcript` | Transcript JSON |
| GET | `/api/v1/ai/speech/jobs/{job_id}/subtitles?format=vtt\|srt` | Subtitles |
| POST | `/api/v1/ai/speech/subtitles` | Ephemeral VTT/SRT from key (no new job) |

### `POST /api/v1/ai/speech/upload`

Multipart form: `file` (required), `project_id` (optional).

**Response:** `{ audio_storage_key, project_id, asset_id, checksum, bytes, duration_seconds }`

### `POST /api/v1/ai/speech/asr`

**Body**

```json
{
  "audio_storage_key": "projects/.../voice.wav",
  "dialect": "sorani",
  "project_id": null,
  "create_annotation": true
}
```

Missing or empty MinIO keys return **404** / **422**. Response includes `job_id`, `media_urls` (`transcript`, `vtt`, `srt`), segments, and engine metadata.

Cinema advertising packages auto-run ASR on VO audio and attach `transcript` / subtitle URLs to the voiceover deliverable. Studio voice generate accepts `run_asr` (default `true`) and returns `transcript_job_id` / `asr_summary`.

---

## 4. Projects — `/api/projects`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{project_id}` | Get project |
| PATCH | `/api/projects/{project_id}` | Update project |
| GET | `/api/projects/{project_id}/characters` | List characters |
| POST | `/api/projects/{project_id}/characters` | Create character |
| GET | `/api/projects/{project_id}/scripts` | List scripts |
| POST | `/api/projects/{project_id}/scripts` | Create script |
| GET | `/api/projects/{project_id}/generations` | List generation jobs |
| POST | `/api/projects/{project_id}/generations` | Submit generation (via Gateway) |

### Create project body

| Field | Type | Required |
|-------|------|----------|
| name | string | yes |
| description | string | no |
| budget_limit | number | no |

### Create character body

| Field | Type | Required |
|-------|------|----------|
| name | string | yes |
| description | string | no |
| identity_rules | object | no |
| costume_notes | string | no |
| voice_profile | object | no |
| reference_paths | string[] | no |

### Create script body

| Field | Type | Required | Default |
|-------|------|----------|---------|
| title | string | yes | |
| body | string | yes | |
| language | string | no | `ku` |

### Submit generation body (`GenerationSubmit`)

| Field | Type | Default |
|-------|------|---------|
| modality | `image\|video\|voice\|audio\|music` | `image` |
| prompt | string | required |
| model | string | `artcity-local-v1` |
| provider | string | `stub` (use `external-fallback` to force fallback) |
| duration_seconds | float | `4.0` |
| dialogue_lines | string[] | |
| character_name | string | maps to `kardokh` / `kurdiya` keys when named |

---

## 5. Studio

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects/{project_id}/studio/summary` | Totals, approvals, spend |
| POST | `/api/projects/{project_id}/studio/generate` | Generate (Gateway) |
| GET | `/api/projects/{project_id}/assets` | List assets |
| POST | `/api/projects/{project_id}/generations/{job_id}/reviews` | Add review |
| GET | `/api/projects/{project_id}/generations/{job_id}/reviews` | List reviews |
| GET | `/api/media/{project_id}/{job_id}/{kind}` | Media bytes (`primary` \| `audio`) |
| GET | `/api/assets/file/{asset_id}` | Asset file bytes |

### Review body

| Field | Type | Required |
|-------|------|----------|
| decision | `approve\|reject\|request_changes` | yes |
| notes | string | no |
| quality_score | number 0–10 | no |

### Studio summary response

```json
{
  "project_id": "...",
  "totals": { "image": 2, "video": 1 },
  "approved": 1,
  "pending_review": 1,
  "spent": 0.045
}
```

---

## 6. Cinema — `/api/projects/{project_id}/cinema`

| Method | Path | Description |
|--------|------|-------------|
| POST | `.../cinema/packages` | Build campaign package (`201`) |
| GET | `.../cinema/packages` | List packages |
| GET | `.../cinema/packages/{package_id}` | Get package |
| POST | `.../cinema/packages/{package_id}/validate` | Re-run technical QC |
| GET | `.../cinema/packages/{package_id}/manifest` | Campaign manifest JSON file |
| GET | `.../cinema/packages/{package_id}/validation` | Validation report JSON file |
| GET | `.../cinema/packages/{package_id}/zip` | Download master ZIP |

### Create cinema package body

| Field | Type | Default |
|-------|------|---------|
| campaign | string | required |
| brief | string | required |
| cta | string | `Discover more` |
| brand | string | `Art City` |
| voiceover_script | string | optional |
| music_style | `epic\|warm\|pulse\|soft` | `epic` |
| duration_seconds | float 5–60 | `15` |
| initiated_by | string | `art-city-producer` |

Outputs include hero 16:9, social 9:16 / 1:1, music, VO, end card, QC, manifest.

---

## 7. Publishing

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects/{project_id}/publications` | Create publication from cinema package |
| GET | `/api/projects/{project_id}/publications` | List |
| GET | `/api/projects/{project_id}/publications/{publication_id}` | Get |
| POST | `/api/projects/{project_id}/publications/{publication_id}/publish` | Finalize release |
| GET | `/api/publications/{project_id}/{publication_id}/manifest` | Master manifest |
| GET | `/api/publications/{project_id}/{publication_id}/report` | Delivery report |
| GET | `/api/publications/{project_id}/{publication_id}/masters/{filename}` | Master file |

### Create publication body

| Field | Type | Default |
|-------|------|---------|
| cinema_package_id | string | required |
| channel | string | optional |
| auto_approve_missing | bool | optional |
| publisher_note | string | optional |

---

## 8. Data Lab (production)

Production ingest → file inventory → annotate → rights gate → export loop. Local multipart upload is the default source (sync). Uploading is never training — `training_ready` requires approved rights.

| Method | Path | Auth notes | Description |
|--------|------|------------|-------------|
| POST | `/api/data-lab/ingest` | upload roles | Multipart ingest → MinIO + `dataset_files` |
| GET | `/api/data-lab/ingestions` | auth | List ingest runs |
| GET | `/api/data-lab/ingestions/{run_id}` | auth | One ingest run + report |
| GET | `/api/data-lab/datasets/{id}` | auth | Dataset detail + counts + rights |
| GET | `/api/data-lab/datasets/{id}/files` | auth | File inventory |
| GET | `/api/data-lab/datasets/{id}/export?format=jsonl\|csv` | auth | Approved annotations export (`persist=true` stores in MinIO) |
| GET | `/api/data-lab/datasets/{id}/manifest` | auth | Training manifest JSON |
| GET | `/api/media/datasets/{id}/files/{file_id}` | auth | Authenticated file preview |
| GET | `/api/data-lab/annotations` | auth | List (`dataset_id`, `status`, `media_type` filters) |
| GET | `/api/data-lab/annotations/stats` | auth | Workspace counts by status/media/source |
| GET | `/api/data-lab/annotations/{task_id}` | auth | One task + comments + revision history |
| POST | `/api/data-lab/annotations` | auth | Create task |
| PATCH | `/api/data-lab/annotations/{task_id}` | auth | Update labels/payload/status/comment |

### Ingest (`multipart/form-data`)

| Field | Type | Required |
|-------|------|----------|
| files | file[] | yes |
| dataset_id | string | no |
| dataset_name | string | no (creates dataset if no id) |
| language | string | no (`ku`) |
| dialect | string | no |

Persists per-file rows (`checksum`, `media_type`, `rights_status`, duration for WAV). Dedupes within batch and against existing dataset files. Auto-creates annotation tasks for text/subtitle/speech. Dataset status → `needs_review`.

**Report fields:** `imported`, `duplicates`, `failed`, `unknown_rights`, `needs_review`, `total_bytes`, `duration_seconds`, `operator`, `language`, `dialect`, `media_counts`, `file_ids`

### Annotation create body

```json
{
  "dataset_id": "UUID",
  "media_type": "text",
  "payload": { "text": "..." },
  "labels": {}
}
```

### Annotation patch body

```json
{
  "labels": {},
  "payload": { "text": "corrected transcript" },
  "status": "approved",
  "comment": "ok"
}
```

Statuses: `pending`, `in_review`, `approved`, `rejected`, `conflict`. Reject requires a non-empty `comment`. Responses include `comments`, `revision_history`, and `assignee_id`.

### Dataset status gate

`PATCH /api/datasets/{id}/status` with `training_ready` calls the rights gate (`ai_training_permission` + approved `RightsRecord`). Without rights → **400**.

---

## 9. Datasets — `/api/datasets`

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/datasets` | List |
| POST | `/api/datasets` | Create (upload roles) |
| PATCH | `/api/datasets/{dataset_id}/status` | Status change |

### Create body (selected fields)

| Field | Type | Default |
|-------|------|---------|
| name | string | required |
| description | string | |
| category | string | `images` |
| media_type | string | `image` |
| language / dialect | string | |
| owner | string | `Art City` |
| licence | string | |
| commercial_use | bool | false |
| ai_training_permission | bool | false |
| voice_cloning_permission | bool | false |
| version | string | `v1` |
| intended_model_use | string | |

### Dataset statuses

`raw` → `ingesting` → `processing` → `needs_review` → `verified` → `training_ready`  
Also: `evaluation_only`, `reference_only`, `blocked`, `archived`

Only `training_ready` + approved AI-training rights may attach to training jobs.

---

## 10. Rights — `/api/rights`

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/rights` | List |
| POST | `/api/rights` | Create (approve roles) |

### Create body

| Field | Type | Default |
|-------|------|---------|
| dataset_id | UUID | optional |
| asset_id | UUID | optional |
| copyright_owner | string | required |
| performer | string | |
| source_organisation | string | |
| contract_reference | string | |
| commercial_use | bool | false |
| ai_training | bool | false |
| fine_tuning | bool | false |
| voice_cloning | bool | false |
| image_generation | bool | false |
| legal_status | string | `unknown` |
| legal_notes | string | |

### Rights legal statuses

`approved_for_training`, `approved_for_reference`, `approved_for_commercial_use`, `approved_for_voice_cloning`, `restricted`, `expired`, `unknown`, `blocked`

---

## 11. Model Registry — `/api/models/registry`

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/models/registry` | List |
| POST | `/api/models/registry` | Register |
| PATCH | `/api/models/registry/{model_id}/status` | Promote / change status |

### Create body

| Field | Type | Default |
|-------|------|---------|
| name | string | required (unique) |
| version | string | required |
| model_type | string | `lora` |
| base_model | string | |
| licence | string | |
| commercial_use | bool | false |
| training_dataset_id | UUID | |
| character_key | string | e.g. `kardokh` |
| modality | string | `image` |
| checkpoint_path | string | |
| checksum | string | required for `production` |

### Model statuses

`draft`, `registered`, `training`, `evaluating`, `approved`, `staging`, `production`, `deprecated`, `blocked`, `archived`

---

## 12. Training — `/api/training`

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/training` | List jobs |
| POST | `/api/training` | Create (rights-gated) |
| POST | `/api/training/{job_id}/approve` | Approve + simulated train → register model |

### Create body

| Field | Type | Default |
|-------|------|---------|
| base_model | string | required |
| dataset_id | UUID | required (`training_ready` + rights) |
| evaluation_dataset_id | UUID | |
| method | string | `lora` |
| epochs | int | `1` |
| learning_rate | float | `1e-4` |
| batch_size | int | `1` |
| seed | int | `42` |
| gpu_type | string | `cloud-a10` |
| estimated_cost | float | |
| model_name | string | resulting registry name |
| character_key | string | |

**Hard rule:** backend rejects training if dataset is not `training_ready` or lacks approved AI-training rights.

---

## 13. Knowledge — `/api/knowledge`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/knowledge?q=&dialect=` | Search / list |
| POST | `/api/knowledge` | Create entry |
| GET | `/api/knowledge/query?terms=a,b` | Prompt helper (approved only) |
| PATCH | `/api/knowledge/{entry_id}/approve` | Approve entry |

### Create body

| Field | Type | Default |
|-------|------|---------|
| term | string | required |
| language | string | `ku` |
| dialect | string | |
| definition | string | required |
| child_friendly_definition | string | |
| translation | string | |
| example_sentence | string | |
| category | string | `terminology` |
| source / licence / cultural_notes | string | |

---

## 14. Evaluations — `/api/evaluations`

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/evaluations` | List |
| POST | `/api/evaluations` | Start candidate vs production eval |
| POST | `/api/evaluations/{run_id}/decision` | Human approve/reject (promote roles) |

### Create body

```json
{
  "candidate_model_id": "UUID",
  "production_model_id": "UUID",
  "modality": "image"
}
```

### Decision body

```json
{
  "decision": "approve",
  "notes": "Passes cultural QC"
}
```

`decision`: `approve` | `reject`

---

## Shared models

### GenerationJobOut

| Field | Type |
|-------|------|
| id | UUID |
| project_id | UUID |
| modality | string |
| provider | string |
| model | string \| null |
| model_version | string \| null |
| registered_model_id | string \| null |
| character_key | string \| null |
| prompt | string \| null |
| status | `pending\|queued\|running\|succeeded\|failed\|cancelled` |
| result_uri | storage key \| null |
| error_message | string \| null |
| estimated_cost / actual_cost | number \| null |
| provider_job_id | string \| null |
| created_at / updated_at | ISO datetime |
| media_url | relative API path \| null |
| audio_url | relative API path \| null |

Absolute media URL = `{BASE}{media_url}`

### Common HTTP errors

| Code | Meaning |
|------|---------|
| 400 | Validation / rights / business rule |
| 401 | Missing or invalid token |
| 403 | Insufficient role |
| 404 | Resource not found |
| 422 | Request body schema error |

---

## End-to-end flows

### A. Studio image (Gateway)

1. Login → token  
2. `POST /api/projects`  
3. `POST /api/v1/ai/images/generate` with `character_key`  
4. `GET /api/v1/ai/jobs/{id}` until `succeeded`  
5. Fetch `{BASE}{media_url}`  
6. `POST .../reviews` with `approve`

### B. Cinema campaign → Publish

1. `POST .../cinema/packages`  
2. `POST .../validate` (optional)  
3. Download ZIP / manifest  
4. `POST .../publications` with `cinema_package_id`  
5. `POST .../publish`

### C. Train character adapter

1. Ingest / create dataset  
2. `POST /api/rights` with `ai_training=true`, `legal_status=approved_for_training`  
3. `PATCH` dataset status → `training_ready`  
4. `POST /api/training`  
5. `POST /api/training/{id}/approve`  
6. `POST /api/evaluations` → decision `approve`  
7. `PATCH` model status → `staging` / `production`

---

## OpenAPI tags (Swagger groups)

| Tag | Area |
|-----|------|
| auth | Login, users |
| model-gateway | `/api/v1/ai` |
| speech | ASR pilot |
| projects | Projects, characters, scripts |
| studio | Studio generate / assets / reviews |
| cinema | Campaign packages |
| edit | Art City Edit — access, entitlements, media, timelines, render |
| publishing | Delivery pipeline |
| data-lab | Ingest + annotations |
| registries | Datasets, rights, models, training |
| knowledge | Kurdish KB |
| evaluations | Model eval lab |
| production-hub | AC Script / breakdown |
| vertical-drama | Vertical Drama IP Factory |
| graphic-motion | AC Graphic Motion MSG |

---

## Art City Edit (`/api/edit`)

Editing and repurposing layer. External processing requires Art City approval + active entitlements. See [`docs/ART_CITY_EDIT_PRD.md`](ART_CITY_EDIT_PRD.md).

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/edit/summary` | Workspace/project counts + feature flags |
| GET | `/api/edit/plans` | Subscription plans |
| POST | `/api/edit/access-applications` | Submit access request |
| GET | `/api/edit/access-applications` | Admin queue |
| POST | `/api/edit/access-applications/{id}/review` | approve / reject / request_info / suspend |
| POST | `/api/edit/organisations/{id}/activate` | Invoice/manual subscription activation |
| POST | `/api/edit/seed/internal` | Seed Art City Group internal workspace (admin) |
| GET | `/api/edit/workspaces` | Membership-scoped workspaces |
| POST | `/api/edit/workspaces/{id}/assets` | Multipart upload + rights attestation |
| POST | `/api/edit/workspaces/{id}/projects` | Create edit project |
| POST | `/api/edit/projects/{id}/analyse` | Queue analysis job |
| GET | `/api/edit/projects/{id}/candidates` | Ranked clip candidates |
| POST | `/api/edit/candidates/{id}/decision` | pin / reject / pending |
| POST | `/api/edit/projects/{id}/timelines` | Build timeline from candidates |
| POST | `/api/edit/timelines/{id}/decide` | approve / reject / request_changes |
| POST | `/api/edit/projects/{id}/renders` | Multi-ratio render job |
| GET | `/api/edit/renders/{id}/package` | Export package + QC |

Feature flags (env): `EDIT_FEATURE_PUBLISHING`, `EDIT_FEATURE_TREND_INTELLIGENCE`, `EDIT_FEATURE_MULTI_CAM`.

---

## AC Graphic Motion (`/api/v1/graphic-motion`)

Motion Scene Graph (MSG) scenes with immutable revisions, RFC 6902 patch + `If-Match`, Sorani/RTL validation, preview/render jobs, and Art City–owned ACX reserve/settle/reverse.

Contracts: [`contracts/ac-graphic-motion/`](../contracts/ac-graphic-motion/). Spec: [`docs/AC_GRAPHIC_MOTION_MSG_SPEC.md`](AC_GRAPHIC_MOTION_MSG_SPEC.md).

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/graphic-motion/features` | Module flags |
| POST | `/api/v1/graphic-motion/acx/quote` | Art City ACX quote (not Nova/Alltra) |
| GET | `/api/v1/graphic-motion/projects/{id}/scenes` | List scenes |
| POST | `/api/v1/graphic-motion/scenes` | Create scene + rev1 (`Idempotency-Key`) |
| GET | `/api/v1/graphic-motion/scenes/{id}` | Head revision |
| PATCH | `/api/v1/graphic-motion/scenes/{id}` | JSON Patch → new revision (`If-Match`) |
| DELETE | `/api/v1/graphic-motion/scenes/{id}` | Soft archive |
| GET | `/api/v1/graphic-motion/scenes/{id}/revisions` | Immutable history |
| POST | `/api/v1/graphic-motion/validate` | Validate unsaved graph |
| POST | `/api/v1/graphic-motion/scenes/{id}/validate` | Validate stored |
| POST | `/api/v1/graphic-motion/scenes/{id}/preview` | Queue preview (202) |
| POST | `/api/v1/graphic-motion/scenes/{id}/render` | Queue production render (202) |
| GET | `/api/v1/graphic-motion/jobs/{id}` | Job status |
| DELETE | `/api/v1/graphic-motion/jobs/{id}` | Cancel |
| POST | `/api/v1/graphic-motion/jobs/{id}/retry` | Retry same revision |
| GET | `/api/v1/graphic-motion/jobs/{id}/events` | SSE progress |

---

## Changelog

| Version | Notes |
|---------|-------|
| 1.0.0 | AI Core: auth, Gateway, Data Lab, Rights, Models, Training, Knowledge, Evaluations, speech ASR scaffold |
| 1.1.0 | Production Kurdish ASR: MinIO upload, persisted speech jobs, Cinema/Studio VO transcripts, VTT/SRT |
| 1.2.0 | Production Data Lab: file inventory, ingest UI path, export manifests, rights-gated training_ready |
| 1.2.1 | Annotations workspace production: stats, get-by-id, payload edits, conflict, revision history |
| 1.3.0 | Art City Edit: tenancy, access applications, entitlements, media pipeline, timelines, multi-ratio render/QC |
| 1.4.0 | AC Graphic Motion: MSG contracts, scenes/revisions, preview/render, Art City ACX |
