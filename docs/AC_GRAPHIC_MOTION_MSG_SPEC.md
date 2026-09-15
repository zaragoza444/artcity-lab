# AC Graphic Motion — MSG Developer Specification v1.0.0

Imported from DOCX. Contracts live under `contracts/ac-graphic-motion/`.

---}

AC GRAPHIC MOTIONMotion Scene Graph JSON Schema & REST API Contracts
Developer Specification v1.0.0 • Art City AI Platform
Purpose: define the canonical, versioned Motion Scene Graph (MSG) and backend contracts for creating, validating, editing, previewing, and rendering AC Graphic Motion scenes inside the existing Art City AI Platform.
1. Architectural Decision
REST is the canonical operational API for v1. GraphQL may later be added for editor-oriented reads, discovery, templates, and collaborative UI queries, but it must not replace the render-job, revision, idempotency, or billing contracts.
Every preview and production render MUST reference an immutable scene_revision_id.
Every edit MUST create a new revision; stored revisions are never mutated in place.
Scene editing uses RFC 6902 JSON Patch plus If-Match optimistic concurrency.
Preview and production render use the same canonical scene graph and animation evaluator.
Kurdish Sorani/Arabic-script typography is deterministic: HarfBuzz-class shaping, Unicode BiDi, grapheme boundaries, and NFC normalization.
Protected channel logos are existing Art City Asset UUIDs; generative redraw is forbidden.
ACX reserve/settle/reverse is keyed to render job_id.
2. Service Boundary in Existing Art City AI
Existing / Service
Responsibility
Art City Auth
JWT, team/user/project permissions.
Projects & Assets
Authority for project_id and asset_id; storage remains shared.
AC Graphic Motion Scene Service
Scene heads, immutable revisions, JSON Patch, validation.
AC Typography Service
HarfBuzz/FreeType/ICU shaping, Sorani glyph coverage, BiDi.
Brand DNA Service
Approved fonts, palettes, logo constraints, protected assets.
Render Orchestrator
Queueing, workers, retries, progress, output registration.
Existing AI Router
Optional generation of image/video/audio assets; never typography/logo authority.
ACX Utility Engine / Wallet
Quote, reserve, settle, reverse, audit.
3. Motion Scene Graph — Root Contract
JSON Schema: Draft 2020-12. Canonical schema version: 1.0.0.
Field
Type
Rule / Purpose
schema_version
const "1.0.0"
Required schema compatibility marker.
scene_id
UUID
Scene identity.
project_id
UUID
Existing Art City project.
name
string 1–160
Human-readable scene name.
locale
BCP-47 string
Default ckb-IQ.
direction
rtl | ltr | auto
Default text/layout direction.
canvas
object
Resolution, fps, duration, background, color space, safe areas.
timeline
object
Timebase and play range.
brand_context
object|null
Brand DNA binding and enforcement.
variables
map
Bindable strings/numbers/colors/assets/JSON.
nodes
array
Scene objects/layers.
markers
array
Beat/cue/chapter/comment/sync markers.
audio
array
Audio tracks.
metadata
object
Extensible non-render-authoritative metadata.
4. Canvas & Timeline
Canvas supports width/height up to 16384 px, standard cinema/broadcast frame rates (23.976, 24, 25, 29.97, 30, 50, 59.94, 60), duration up to 1 hour, Rec.709/sRGB/Display-P3/Rec.2020, pixel aspect ratio, and title/action safe percentages. Timeline v1 uses millisecond timestamps as the canonical interchange representation.
5. Node Model
Supported v1 node types:
text • image • video • logo • shape • svg • group • camera • particle • chart • map • precomp
id: Stable node ID; unique inside graph.
type: One of the supported node primitives.
parent_id: Optional hierarchy parent; cycles forbidden.
z_index: Layer ordering.
start_ms / end_ms: Active interval; must fit canvas duration.
visible / locked: Authoring and render state.
transform: x/y/z, anchors, scale, rotation, opacity.
payload: Type-specific content.
animations: Property tracks + keyframes.
effects: Deterministic effects.
bindings: Variable/data bindings.
tags: Classification/search metadata.
6. Kurdish Sorani / RTL Text Payload
Text MUST remain real Unicode text until deterministic shaping/render. The AI planner may choose layout, timing, style and animation, but it MUST NOT raster-generate or redraw Kurdish lettering.
Property
Contract
language
ckb by default; BCP-47 compatible.
direction
rtl/ltr/auto.
unicode_bidi
normal/embed/isolate/bidi-override/plaintext; plaintext recommended for mixed user content.
font.asset_id
Existing Art City font asset UUID.
font.weight/style/features
OpenType selection.
font_size / line_height / letter_spacing
Typography metrics.
align
start/center/end/justify; use logical start/end, not hard-coded left/right.
wrap
none/word/character.
overflow
clip/ellipsis/shrink/expand.
shaping_engine
Fixed to harfbuzz in v1.
normalization
NFC default.
animation_unit
block/line/word/grapheme. Word is recommended for Sorani motion; never naïvely animate code points.
7. Protected Logo / Asset Contract
Image/video/logo nodes reference Art City asset UUIDs. A logo payload with preserve_exact_pixels=true is protected: no generative redraw, geometry rewrite, recoloring, destructive crop, or unapproved effect may alter the logo. Brand DNA validation may impose clear-space, size, color, and placement rules.
8. Animation Model
Animation tracks target explicit property paths (for example transform.x or transform.opacity). Keyframes contain time_ms, value, easing and optional hold. Supported easing includes linear, ease-in/out/in-out, step variants, and cubic Bézier [x1,y1,x2,y2]. Keyframes must be sorted and valid for the target property.
9. Mandatory Validation Pipeline
1. JSON Schema validation.
2. Graph integrity: unique node IDs, valid parents, no parent cycles.
3. Timeline integrity: 0 ≤ start < end ≤ canvas.duration_ms.
4. Animation integrity: valid property paths, ordered keyframes, compatible value types.
5. Asset integrity: asset exists, project/user authorized, supported media type.
6. Typography: Sorani glyph coverage, shaping success, Unicode BiDi correctness, safe grapheme/word animation.
7. Brand DNA: locked logo/font/color constraints and protected geometry.
8. Output profile: resolution, fps, codec, alpha and color-space compatibility.
9. Renderer capability: every node/effect supported by selected renderer.
10. Security/resource limits: expression allowlist, graph complexity, duration, pixel count, effect limits.
10. REST API — Canonical Endpoints
Method
Path
Purpose
POST
/v1/graphic-motion/scenes
Create scene + revision 1.
GET
/v1/graphic-motion/scenes/{scene_id}
Get scene head/current revision.
PATCH
/v1/graphic-motion/scenes/{scene_id}
RFC 6902 patch; creates new revision; requires If-Match.
DELETE
/v1/graphic-motion/scenes/{scene_id}
Soft archive.
GET
/v1/graphic-motion/scenes/{scene_id}/revisions
List immutable revisions.
GET
/v1/graphic-motion/scenes/{scene_id}/revisions/{revision_id}
Fetch exact revision.
POST
/v1/graphic-motion/validate
Validate unsaved graph.
POST
/v1/graphic-motion/scenes/{scene_id}/validate
Validate stored revision/profile.
POST
/v1/graphic-motion/scenes/{scene_id}/preview
Queue preview from revision.
POST
/v1/graphic-motion/scenes/{scene_id}/render
Queue production render from revision.
GET
/v1/graphic-motion/jobs/{job_id}
Job status, progress, outputs, billing.
DELETE
/v1/graphic-motion/jobs/{job_id}
Request cancellation.
POST
/v1/graphic-motion/jobs/{job_id}/retry
Retry same immutable input.
GET
/v1/graphic-motion/jobs/{job_id}/events
SSE progress stream.
11. Create / Edit Concurrency Contract
POST /scenes may accept Idempotency-Key. PATCH /scenes/{scene_id} MUST use Content-Type application/json-patch+json and If-Match containing the current scene ETag/content hash. If the head revision changed, return HTTP 409 AGM_REVISION_CONFLICT; never silently overwrite another editor's changes.
12. Preview Contract
Preview requests require revision_id and support still/range/full modes, optional at_ms or range, reduced dimensions, preview fps, MP4/WebM/PNG/JPEG, and draft/standard quality. Return HTTP 202 with job_id, status_url and events_url.
13. Production Render Contract
Production render requests require revision_id and an output profile. Supported v1 containers: MP4, MOV, WebM, PNG sequence, EXR sequence. Codecs: H.264, H.265, ProRes 422, ProRes 4444, VP9, AV1, PNG, EXR. Alpha is allowed only with compatible codecs/containers. Broadcast validation runs before queue admission.
14. Render Job State Machine
queued → validating → preparing → rendering → muxing → uploading → completedFailure path: any active state → failed. Cancellation path: active state → cancel_requested → cancelled.
Job progress is 0.0–1.0. Completed outputs are registered back into the existing Art City Asset system and returned as asset_id, role, content_type, size_bytes and SHA-256. Public storage URLs should not be the canonical output identity.
15. ACX Billing Contract
A production render may carry acx_quote_id. The backend reserves ACX before expensive work begins, associates the reservation with job_id, settles actual usage on successful completion, and reverses/reconciles reservation on eligible failure/cancellation. Idempotent retries must never double-charge.
16. Error Namespace
AGM_SCHEMA_INVALID • AGM_GRAPH_DUPLICATE_NODE • AGM_GRAPH_PARENT_CYCLE • AGM_TIMELINE_OUT_OF_RANGE • AGM_ASSET_NOT_FOUND • AGM_ASSET_FORBIDDEN • AGM_FONT_GLYPH_MISSING • AGM_RTL_SHAPING_FAILED • AGM_BRAND_LOGO_MUTATION • AGM_RENDER_UNSUPPORTED_EFFECT • AGM_RENDER_PROFILE_INVALID • AGM_REVISION_CONFLICT • AGM_ACX_RESERVATION_FAILED
17. Reference Sorani Scene
{  "schema_version": "1.0.0",  "locale": "ckb-IQ",  "direction": "rtl",  "canvas": {    "width": 1920,    "height": 1080,    "fps": 25,    "duration_ms": 8000,    "background": "#00000000",    "color_space": "rec709"  },  "nodes": [    {      "id": "headline",      "type": "text",      "start_ms": 250,      "end_ms": 8000,      "payload": {        "text": "هەواڵی گرنگ",        "language": "ckb",        "direction": "rtl",        "unicode_bidi": "plaintext",        "font": {"asset_id": "<ART_CITY_FONT_UUID>", "weight": 700},        "font_size": 72,        "fill": "#FFFFFFFF",        "shaping_engine": "harfbuzz",        "normalization": "NFC",        "animation_unit": "word"      }    }  ]}
18. Release Blockers / Definition of Done
Schema validation test suite passes for valid/invalid fixtures.
Revision immutability and If-Match conflict tests pass.
Sorani shaping tests include Kurdish-specific letters, mixed Kurdish/English/numbers, punctuation, multiline text and word reveals.
Protected-logo mutation tests fail closed.
Preview-to-final frame parity is verified for the same revision and timestamp.
Render cancellation/retry is idempotent.
ACX reserve/settle/reverse tests prove no double charging.
Output assets are registered in existing Art City Asset storage with checksums.
Broadcast profile test produces valid 1920×1080/25 Rec.709 and alpha-capable ProRes 4444 output.
API contract is generated into server/client types in CI and breaking schema changes require a new version.
19. Files Developers Should Keep in Repository
/contracts/ac-graphic-motion/motion-scene-graph.schema.json/contracts/ac-graphic-motion/openapi.yaml/contracts/ac-graphic-motion/examples/example-scene.ckb.json/contracts/ac-graphic-motion/README.md
ART CITY AI • AC GRAPHIC MOTION • DEVELOPER CONTRACT v1.0.0
