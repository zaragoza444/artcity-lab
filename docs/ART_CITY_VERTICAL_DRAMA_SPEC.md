# Art City AI Vertical Drama IP Factory

Imported from:

- `docs/source/Art_City_AI_Vertical_Drama_IP_Factory_Master_Developer_Specification_v1.0.docx`
- `docs/source/Art_City_AI_Vertical_Drama_IP_Factory_Developer_Sprint_Backlog_v1.0.docx`

Working extracts: `docs/source/*.extract.txt`.

## Product

Public name: **Art City AI Vertical Drama IP Factory**. UI label: **AC Vertical Drama**. Promise: create a series, build an IP, produce episode by episode.

This is a **separate domain** on the shared Art City AI core. It is not a prompt-to-video page and does not duplicate accounts, billing, storage, or AI providers.

## Architecture freeze (ADR)

| Decision | Rule |
|---|---|
| Boundary | `/vertical-drama` under existing Art City auth and project shell |
| Project identity | Shared `project_id` plus domain `vd_project_id` |
| Assets | Shared `assets` / MinIO; VD stores semantic links |
| AI | All inference via Model Gateway / AI Router — never from UI |
| Canon | Structured entities + versioned JSON; AI proposes; humans approve |
| Locks | Approved canon/script/master never silently overwritten |
| Localization | Original language is canonical; translations are linked variants |
| Deletion | Soft-delete + audit |

## Shared vs domain-owned

**Shared:** auth, `projects`, Data Bank/assets, Model Gateway, cost ledger, Hub Script, Cinema/Studio/Edit, ckb-IQ/RTL, QC/delivery primitives.

**Domain-owned:** IP titles, rights/provenance, canon, story bible, seasons/episodes, découpage/shots, VD generation jobs, assemblies, QC runs, delivery packages.

## MVP (Sprints 0–4)

Governed IP → Story Bible → season/episode factory → découpage → router generation → Edit handoff → QC → delivery.

Sprint 5 analytics learning loop is **deferred**.
