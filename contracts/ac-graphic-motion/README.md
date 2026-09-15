# AC Graphic Motion — Motion Scene Graph Contracts

Canonical MSG schema version **1.0.0** for Art City AI Platform.

## Files

| File | Purpose |
|------|---------|
| `motion-scene-graph.schema.json` | JSON Schema Draft 2020-12 |
| `openapi.yaml` | REST API contracts (`/api/v1/graphic-motion`) |
| `examples/example-scene.ckb.json` | Sorani RTL reference scene |
| `../docs/AC_GRAPHIC_MOTION_MSG_SPEC.md` | Developer specification (markdown) |
| `../docs/source/AC_Graphic_Motion_MSG_API_Developer_Specification_v1.docx` | Original DOCX |

## Rules (v1)

- REST is canonical; GraphQL must not replace render/revision/idempotency/billing.
- Every preview/production render references an immutable `scene_revision_id`.
- Every edit creates a new revision; stored revisions are never mutated.
- Kurdish Sorani text stays Unicode until HarfBuzz-class shaping — never AI-rasterized.
- Protected logos (`preserve_exact_pixels=true`) forbid generative redraw.
- ACX reserve/settle/reverse is Art City–owned and keyed to `job_id`.

Breaking schema changes require a new `schema_version`.
