# Art City AI — Complete Production Hub

Master Technical & Development Specification (imported from DOCX v2.0, 20 August 2026).

Source: docs/source/Art_City_AI_Complete_Production_Hub_Master_Specification.docx

## Implementation status (this repo)

- **In scope now:** Pre-production Hub with full-fidelity **AC Script** + Scene Breakdown Core + Cinema/Studio/Edit handoff hooks.
- **Deferred:** Full AC Storyboard, AC Budget, AC Call, Mastering/QC/Delivery.

## Spec extract (sections)

- Project setup and multilingual production metadata.
- Script creation, import, editing, AI-assisted rewriting, translation and version control.
- Structured scene parsing and script breakdown.
- Character, cast, location, prop, wardrobe, vehicle, VFX/SFX, stunt and production-element registries.
- AI découpage and editable shot list.
- AI storyboard generation with character/location consistency references.
- Production budget calculator with versions, rate cards, scenarios and spreadsheet export.
- Shooting schedule core sufficient to drive call sheets.
- Call sheet generation, revisions, distribution and crew/cast confirmation.
- Kurdish Sorani first-class UI, content, search, AI and export support.
- Integration hooks into Cinema, Studio and Edit.
- Role-based permissions, audit trails, subscriptions/credits and AI usage-cost logging.
- Use CSS logical properties (margin-inline-start/end, padding-inline-start/end) instead of hard-coded left/right where possible.
- Use dir="rtl" at the appropriate layout root, not on every child indiscriminately.
- For mixed-direction tokens use <bdi>, Unicode bidi isolation or component-level dir="ltr" as appropriate.
- Icons with semantic direction (chevrons, back/forward, timeline arrows) must mirror in RTL; non-directional icons must not.
- Spreadsheet row headers, numeric columns and account codes can remain LTR while descriptive cells are RTL.
- Modal placement, sidebars, drawers, tab order and keyboard navigation must feel native in RTL.
- Do not infer language from direction. Arabic and Sorani are separate locales even though both are RTL.
- Every AI text endpoint must accept language and output_language explicitly.
- Do not automatically translate Kurdish character/location names unless the user asks.
- Preserve Sorani punctuation, spelling and paragraph direction.
- Support Kurdish-only, English-only and bilingual script projects.
- Allow per-scene or per-dialogue translation while retaining the original as a parallel version.
- If generating JSON, text direction must never change the JSON schema; values are Unicode strings.
- Prompt templates should contain locale-aware instructions and examples tested with Sorani.
- Run automated regression tests using real Sorani strings, mixed Kurdish-English text, numbers, punctuation and filenames.
- Start from idea
- Start from logline
- Start from synopsis
- Start from treatment
- Create from beat sheet
- Upload/import an existing screenplay
- Continue a script
- Rewrite or polish a script
- Adapt user-owned/source-cleared material
- Translate an existing script
- Create an episode, commercial, music video, documentary or social/AI drama
- Rewrite / shorten / expand
- Improve dialogue
- Make dialogue more natural
- Increase/decrease suspense
- Increase/decrease comedy or darkness
- Add conflict
- Improve pacing
- Generate alternative scene
- Change location while preserving intent
- Translate selected range
- Convert dialogue to Sorani / English / Arabic
- Maintain character voice
- Reduce production complexity
- “Make this scene cheaper to produce” with explicit assumptions
- Draft 1 / Draft 2 / Revision A / Revision B / Shooting Script / Locked Script.
- Never overwrite an approved/locked version.
- Maintain scene-level change records.
- Support compare/diff between versions.
- Any downstream module that depends on changed scenes receives a stale/out-of-date flag until reviewed.
- Locking a shooting script generates immutable revision metadata and an audit event.
- Scene text and dramatic intention
- Characters present and blocking
- Dialogue and action beats
- Location geometry/references
- Visual style and genre
- Desired pacing
- Camera package/lens constraints
- Aspect ratio
- Continuity constraints
- Budget/production constraints
- Director/DP custom instruction
- Generate
- Regenerate while preserving selected locks
- Change lens
- Change shot size
- Change camera angle
- Change camera height
- Change movement
- Change character pose/expression
- Change blocking
- Change lighting/time-of-day
- Change wardrobe state
- Change background/reference
- Replace only one frame
- Drag/reorder shots
- Duplicate shot
- Mark approved/hold/rejected
- Storyboard PDF
- Contact sheet
- Shot list XLSX/CSV
- Director’s board
- DP shot list
- JSON/API data
- Push approved visual references to Art City AI Cinema
- Open selected frame/reference in Art City AI Studio
- Push shot metadata and intended order to Art City AI Edit
## 10. Module 3 — AC Budget

## 10.1 Goal

## 10.2 Budget modes

- Quick Estimate
- Preliminary / Investor Budget
- Detailed Production Budget
- Locked Approved Budget
- Actual vs Budget (future/accounting integration-ready)
## 10.3 Generation flow

## 10.4 Recommended account groups

## 10.5 Budget line schema

## 10.6 Calculation engine

## 10.7 Rate cards

## 10.8 Budget scenarios

- Micro
- Standard
- Premium
- Custom
- Duplicate current budget as scenario
- Compare two versions by department and total
- Target reduction: e.g., reduce 15% and show operational consequences
## 10.9 AI production-cost intelligence

## 10.10 Spreadsheet UX

- Keyboard-friendly data entry
- Add/delete/duplicate/move row
- Add department/account
- Formula-derived totals
- Attach quotation/PO/reference
- Notes/comments
- Approval and lock
- Filter by department
- Search by item
- Multi-currency display with controlled base-currency conversion logic
- RTL-friendly descriptive columns and LTR numeric columns
- Export XLSX, CSV and PDF
## 11. Shared Production Schedule Core

## 11.1 Scheduling inputs

- Scene page count and estimated shoot time
- INT/EXT and day/night
- Cast availability
- Location availability
- Location cluster/company move
- Child/minor constraints entered by production
- Equipment constraints
- Stunt/VFX/SFX requirements
- Travel/turnaround constraints
- Director/producer priority and manual locks
## 11.2 Shooting day schema

## 11.3 Future optimizer queries

- Minimize company moves
- Minimize actor holding days
- Group all scenes at one location
- Reduce total shoot days
- Respect fixed actor/location dates
- Find schedule conflicts
- Estimate cost delta between 20-day and 25-day schedules
## 12. Module 4 — AC Call

## 12.1 Goal

## 12.2 Call sheet sections

## 12.3 Call sheet status and revision logic

- Draft
- Pending approval
- Approved
- Published
- Superseded
- Final/archived
## 12.4 Recipient status

## 12.5 Weather rule

## 12.6 Call sheet exports and delivery

- Responsive web view
- PDF
- DOCX if required
- Email distribution
- Secure share link
- Optional SMS/WhatsApp integration in a future connector layer
- QR code to latest approved version
- Localized Sorani/English output or bilingual template
## 13. Cross-Module Dependency and Change Intelligence

## 13.1 Event examples

## 13.2 Stale-state handling

## 14. Integration with Art City AI Cinema, Studio and Edit

## 14.1 Cinema handoff

- Send approved scene/script context to Cinema.
- Send Character Lock and Location Lock references.
- Send approved storyboard/shot sequence.
- Send target aspect ratio, runtime and visual style.
- Maintain originating project_id, scene_id and shot_id in generated Cinema assets.
- Returned Cinema assets appear in the same project asset library and may be linked back to the originating shot.
## 14.2 Studio handoff

- Open character/location/prop/wardrobe reference in Studio without re-upload.
- Create or refine a reference asset and return the new version to Pre-Production.
- Maintain asset lineage and version.
- Allow “Set as Character Lock” or “Set as Location Lock” from approved Studio output.
## 14.3 Edit handoff

- Export scene and shot metadata to Edit.
- Expose intended sequence/order, shot IDs, dialogue references and continuity notes.
- Allow uploaded production media to be tagged to project → shooting day → scene → shot → take.
- Enable Edit to compare captured media against planned shot list in future.
- Retain target deliverable ratios and campaign metadata already used by the Art City ecosystem.
## 14.4 Shared Asset Library

## 15. Recommended Product Navigation

## 15.1 Locale switch behavior

## 16. Roles, Permissions and Approval

## 16.1 Permission model

## 17. Subscription, Credits and Art City Authorization

## 18. Database Blueprint

## 18.1 Core tables

## 18.2 Important database rules

- All tenant-owned records contain workspace_id and project_id where applicable.
- Use UUID primary keys internally; human-readable codes may be separate.
- Use NUMERIC/Decimal for money.
- Use JSONB for flexible metadata only when the fields are not important relational/reporting dimensions.
- Do not put large image/document binaries in PostgreSQL. Store object-storage keys and metadata.
- Version immutable production documents rather than updating rows in place.
- Record created_by, updated_by, created_at, updated_at on production records.
- Use optimistic concurrency/version numbers for collaborative edits where appropriate.
- Audit log must be append-only from the application perspective.
## 19. API Blueprint

## 19.1 API conventions

- Version APIs (/api/v1).
- Always enforce authorization in FastAPI dependencies/service layer.
- Return machine-readable error codes plus localized display messages.
- Use idempotency keys for publish/export/generation actions where duplicates are costly.
- Long-running jobs return job_id and status endpoint/WebSocket/SSE updates.
- Validate structured AI responses before persistence.
- Use request locale for UI/error messaging, not for internal enum values.
- Enums and API field names remain English/stable; localized labels are presentation-layer concerns.
## 20. Suggested Backend Structure

## 20.1 AI provider abstraction

## 20.2 Structured AI output rule

## 21. Suggested Frontend Structure

## 21.1 Reusable components

- LocaleAwareField
- DirectionAwareTextArea
- ScreenplayEditor
- SceneNavigator
- CharacterPicker
- LocationPicker
- BreakdownPanel
- ShotCard
- StoryboardGrid
- VisualLockPicker
- BudgetGrid
- MoneyInput
- RateCardPicker
- ScheduleBoard
- CallSheetPreview
- ApprovalBar
- VersionSelector
- StaleDependencyBanner
- AssetPicker
- AIJobStatus
- AuditTimeline
## 21.2 Editing strategy

## 22. AI Generation Audit and Cost Control

## 23. Security, Privacy and Data Ownership

- Workspace/tenant isolation on every query.
- Signed/time-limited object-storage URLs for private assets.
- Server-side authorization for all production data and exports.
- Encrypt secrets and external provider credentials.
- Do not expose AI provider API keys to the browser.
- Configurable data-retention policy for prompts/generations.
- Audit sensitive actions: publish call sheet, change budget, lock script, change permissions, export.
- Allow project deletion/archive according to Art City policy and contractual obligations.
- Do not use customer scripts/assets for model training unless an explicit product/legal policy permits it and the customer has agreed.
- Mark generated content lineage so users can distinguish authored, AI-suggested and approved production data.
## 24. Reliability and Background Jobs

- Use Redis-backed job processing for storyboards, long script operations and document exports.
- Jobs must be retryable and idempotent where possible.
- UI must show queued/running/succeeded/failed/cancelled.
- A browser refresh must not lose job state.
- Prevent duplicate charge/generation when the user double-clicks.
- Autosave textual/structured edits separately from expensive AI generation.
- Use transactional boundaries when locking/publishing production versions.
## 25. Acceptance Criteria — Release Gate

## 25.1 Global / ecosystem

- A user signs in once and can move among Pre-Production, Cinema, Studio and Edit within the same project.
- All modules preserve project_id and workspace_id.
- Entitlements can enable/disable Pre-Production modules without code deployment.
- Assets created in Studio/Cinema can be linked in Pre-Production without duplicate upload.
- Approved Pre-Production metadata is available to Edit through internal API/data layer.
## 25.2 Sorani / RTL

- Full application shell mirrors correctly in ckb-IQ.
- Kurdish text entry works in every form, screenplay element, breakdown item, budget description and call sheet.
- Mixed Kurdish/English scene headings do not reorder incorrectly.
- Character and location names round-trip through API/DB/export unchanged.
- Search handles configured Kurdish/Arabic letter equivalences without destructive storage changes.
- PDF/DOCX export shows joined Kurdish glyphs and correct RTL paragraphs/tables.
- Budget numeric fields remain usable and correctly calculated under RTL.
- All localization strings are externalized; no visible hard-coded English remains in ckb-IQ mode except approved industry terms/brand names.
## 25.3 AC Script

- Create/import a script and edit screenplay semantic elements.
- Generate a structured scene list.
- Generate/edit breakdown and approve items.
- Create new version, compare and lock.
- Changed locked-script dependencies are flagged downstream.
- Export a Sorani screenplay to PDF and DOCX without direction/glyph defects.
## 25.4 AC Storyboard

- Generate editable découpage from a selected scene.
- Store shots as structured records.
- Generate one or multiple storyboard frames.
- Regenerate one frame while retaining character/location lock references.
- Reorder shots and retain stable IDs/revision history.
- Export storyboard PDF and shot list XLSX/CSV.
- Send approved references to Cinema/Studio with lineage.
## 25.5 AC Budget

- Generate budget draft from breakdown/schedule assumptions.
- All totals are deterministic and backend-authoritative.
- Edit quantities/rates and see recalculated totals.
- Create/compare/lock budget versions.
- Use ckb-IQ UI while numeric calculations remain correct.
- Export XLSX/PDF.
- AI-estimated rates are clearly marked unverified until approved.
## 25.6 AC Call

- Generate call sheet only from a shooting day/schedule context.
- Populate scene and cast calls from canonical project data.
- Weather values are from an external weather source with timestamp.
- Publish a version and track recipients.
- Create a revision that supersedes the old version.
- Display latest version in Sorani, English or configured bilingual template.
- PDF export is production-readable on desktop and mobile.
## 26. Testing Plan

## 26.1 Automated tests

- Unit tests for budget formulas, page/eighth calculations and version rules.
- API permission tests for every privileged endpoint.
- Schema validation tests for AI structured outputs.
- RTL snapshot/visual regression tests for key screens.
- Sorani Unicode round-trip tests through DB/API/export.
- Mixed bidi test strings including INT./EXT., 24mm, T2.8, emails, phone numbers and Kurdish names.
- Dependency-event tests: script change → downstream stale flags.
- Concurrency tests for autosave/version locking.
- Job idempotency tests for storyboard/export generation.
- Tenant-isolation tests.
## 26.2 Required Sorani QA dataset

## 27. Recommended Development Sequence

## 28. Do Not Build These as Four Independent AI Pages

## 29. AC Producer Copilot — Recommended Cross-Module Layer

- Which scene costs the most?
- Which actors have the most shooting days?
- Show all night exteriors.
- Show all scenes with children/minors.
- Which scenes require VFX?
- Can we group all Citadel scenes together?
- What changes if Scene 71 is removed?
- Reduce the draft budget by 15% and show the operational consequences.
- Which storyboard shots are out of date after the latest script revision?
- Generate a draft call sheet for tomorrow’s approved shooting day.
## 30. Developer Definition of Done

- Feature has backend and frontend tests.
- Feature has ckb-IQ and en localization strings.
- Feature passes RTL visual QA.
- Feature enforces server-side permissions.
- AI actions record provider/model/cost/status.
- Expensive actions are idempotent and job-tracked.
- Production data is versioned where required.
- Exports are visually verified for Kurdish and English.
- Cross-module links retain project/scene/shot/asset lineage.
- Audit log records privileged state changes.
- No approved production artifact is silently overwritten by AI.
## 31. Pre-Production Foundation Vision

## 32. Pre-Production Foundation Handoff Checklist

## 33. Master Production Hub Scope and Operating Principle

## 34. AC Production — Live Production Command Centre

- Producer / Executive Producer
- Director
- 1st Assistant Director
- Production Manager / Coordinator
- Script Supervisor
- Director of Photography / Camera team
- Sound team
- DIT / Data Manager
- Department heads with scoped permissions
- Crew call actual
- First setup ready
- First shot
- Meal start/end
- Company move start/end
- Scene start/end
- Actor wrap
- Camera wrap
- Production wrap
- Incident or delay event
- Weather interruption
- Equipment failure
- Unplanned overtime trigger
## 35. AC Slate + Shot / Take Tracker

- NG / False start
- Technical issue
- Performance hold
- Good
- Circle take
- Director select
- Editor select
- Pickup required
## 36. AC Continuity — Script Supervisor Workspace

- Costume / wardrobe state
- Hair and makeup
- Props and prop position
- Food/drink levels
- Actor blocking and body/hand position
- Eyelines and screen direction
- Vehicle position/damage/state
- Blood, dirt, wetness, injuries and practical effects
- Dialogue changes / ad-libs
- Action changes
- Scene timing
- Camera axis / coverage notes
- Continuity reference photos
## 37. Camera, Sound and Department Reports

- Camera body / serial or unit ID
- Card/reel/media ID
- Clip filename
- Scene / shot / take
- FPS / shutter / resolution / codec
- Lens / focal length / filtration
- LUT / look reference
- Timecode
- Technical notes
- Good/NG/Select status
- Media offload and checksum state
- Recorder / media ID
- Audio filename / roll
- Scene / shot / take
- Timecode
- Track names and channel assignments
- Sample rate / bit depth
- Mic/source notes
- Wild tracks / room tone
- Technical/continuity notes
- Sync status
## 38. AC Dailies + Media Ingest

- Use cryptographic checksum verification for copy validation.
- Record source card/media ID and destination object/storage key.
- Never mark BACKED UP based only on upload completion; verification must succeed.
- Track at least primary copy and backup-copy status as separate fields.
- Prevent media deletion while retention/backup policy is unsatisfied unless privileged override is logged.
- Store proxy as derivative of original asset, not as an unrelated upload.
- Secure streaming proxy
- Burn-in overlays configurable by role
- Scene/shot/take navigation
- Favourites / Director Select
- Frame/timecode comments
- Private notes vs shared notes
- Watermark per viewer when required
- Download permission
- Approval / hold / pickup flag
## 39. AC Media Asset Management (MAM)

## 40. AC Daily Production Report (DPR)

- Production day/date/location
- Crew call / first shot / meal / last shot / wrap
- Scenes scheduled / completed / partial / moved
- Pages planned vs completed
- Cast worked and wrap times
- Extras and special participants
- Equipment / vehicles / special resources
- Weather summary from verified source
- Incidents / delays / damage
- Overtime
- Media cards/rolls and ingest/backup summary
- Notes for next shooting day
- Authorized sign-off
## 41. Production Crew, Cast and Equipment Operations

- Person / contact identity
- Production role and department
- Character/cast relationship if applicable
- Project availability
- Production day calls and actual work times
- Production documents/releases status
- Emergency contact visibility governed by permissions
- Communication preference
- Project-specific rate/reference only where authorized
- Portal/account invitation status
## 42. AC Review — Frame-Accurate Review and Approval

- Frame/timecode-accurate comments
- Threaded replies and @mentions
- Annotations/drawings where technically supported
- Version selector and side-by-side/overlay comparison where appropriate
- Approval / changes requested / rejected / locked states
- Private comments by permission
- Secure external review link
- Expiry, passcode and download controls
- Viewer watermarking
- Read/approval audit trail
- Sorani RTL comments and bilingual review
## 43. AC Edit — Post-Production Core Integration

- Locked/active script version
- Scene and shot IDs
- Découpage/shot order
- Director selects and circle takes
- Camera/sound metadata
- Continuity notes and script changes
- Synced proxies and original-media lineage
- Music/graphic/reference assets from Studio/Cinema
- Deliverable aspect-ratio targets
- Rights/status flags for restricted media
## 44. AC VFX — Shot Tracking and Review

- VFX shot code
- Scene/shot/take linkage
- Plate/source asset
- Edit in/out/timecode reference
- Task/type: cleanup, comp, key, tracking, CG, sky, screen, etc.
- Vendor/artist assignment
- Brief and reference files
- Target resolution/color pipeline
- Version history
- Review comments
- Status/deadline/priority
- Final render asset and checksum
## 45. AC Color — Color Workflow Management

- Camera color metadata / log/gamut
- On-set LUT/look reference
- Approved creative look references
- Color turnover asset/version
- Conform status
- Grade version and reviewer
- Display/master target (e.g., SDR/HDR when supported)
- Review/approval status
- Final graded master lineage
## 46. AC Sound Post — Dialogue, ADR, Foley, Music and Mix

## 47. AC Localization — Subtitles, Captions, Dubbing and Multilingual Masters

- Cue ID
- Start/end timecode
- Text
- Language / locale
- Speaker when required
- Style/type: subtitle, SDH/CC, forced narrative
- Line count / characters / reading-speed metrics
- RTL/LTR direction metadata if needed for renderer
- Review state
- Source translation/version
- Export format
- Correct RTL rendering and glyph shaping in preview/export
- Mixed Kurdish/English names and numbers without visual reordering
- Unicode normalization only for search/indexing; preserve authored display text
- Kurdish punctuation and line-breaking regression tests
- Bilingual subtitle comparison view
- Human linguistic approval before final delivery status
## 48. AC Mastering — Final Master Builder

- Approved picture/version
- Approved full mix
- Stereo/5.1/etc. audio tracks as required
- M&E
- Subtitle/caption tracks
- Textless elements where required
- Credits/version information
- Technical specification profile
- Artwork/metadata references
- Checksum and manifest
## 49. AC QC — Automated and Human Quality Control

- Resolution/dimensions
- Frame rate and cadence metadata
- Codec/container/profile
- Aspect ratio / active image
- Duration
- Black/freeze/flash heuristics
- Dropped/corrupt frame detection where supported
- Color-space/HDR metadata consistency where applicable
- Bars/slate/leader rules per delivery profile
- Expected track count and channel mapping
- Sample rate / bit depth / codec
- Silence/near-silence anomalies
- Clipping / true peak
- Integrated loudness against configured target
- A/V sync checks where measurable
- Language/role labeling
- M&E presence and configuration
- Cue timing / zero or negative duration
- Overlap/collision rules
- Reading-speed threshold
- Line/character limits by profile
- Out-of-bounds timing beyond program duration
- Missing/duplicate cue IDs
- RTL render validation for Sorani
- Forced/SDH labeling consistency
## 50. AC Delivery — Packaging, Readiness and Delivery Control

- Recipient/platform/client
- Profile/specification version
- Package version and checksum
- Method / endpoint / transfer reference
- Submitted by / date
- Status: prepared/sent/received/rejected/accepted
- Rejection reason / QC feedback
- Resubmission relationship
- Receipt/confirmation evidence
## 51. AC Rights, Releases and Production Documents

- Script/story rights
- Writer/director/producer agreements
- Cast release / performance rights
- Extra/minor/guardian consent where applicable
- Location release
- Music composition/master rights
- Archive footage / stock footage / still-image rights
- Artwork/logo/trademark permission where applicable
- Voice/likeness/AI-use permissions where applicable
- Territory/platform/language/window restrictions
- Cast/extra release
- Location release
- Crew deal memo/production acknowledgement
- NDA/confidentiality document
- Equipment checkout/return
- Vehicle request/use form
- Incident report
- Expense/petty-cash reference if enabled in project
- Production consent/authorization forms
- Call-sheet acknowledgement
## 52. Production and Post Readiness Scores

## 53. AC Production Copilot — Full Project Intelligence Layer

- What are we shooting tomorrow?
- Which actors have not confirmed tomorrow’s call?
- Which scenes are behind schedule?
- Which planned shots have no captured takes?
- Show Director Selects from Scene 21.
- Which media cards are not verified in two locations?
- Which scenes have unresolved continuity warnings?
- Which VFX shots are still in review?
- What is blocking picture lock?
- Which Sorani subtitles failed reading-speed or RTL QC?
- Is the delivery package ready for the selected client profile?
- What changed after Script Revision C?
## 54. Notifications, Approvals and Activity Centre

- Script revision affects downstream artifacts
- Storyboard/shot list ready for approval
- Budget threshold/variance warning
- Call sheet published/revised
- Cast/crew confirmation missing
- Schedule delay/overtime risk
- Media backup incomplete
- Continuity/VFX/post review comment assigned
- Review approval/changes requested
- QC failure
- Rights document expiring/missing
- Delivery accepted/rejected
## 55. Global Search and Production Knowledge Graph

- Exact ID/code search
- Full-text keyword search
- Sorani normalized search index
- Filters by project/module/status/date/person/language
- Semantic search over approved textual content where enabled
- Natural-language project query through Copilot
## 56. Storage, Media Security and Access Architecture

- Workspace/tenant isolation
- Project/role scoped permissions
- Signed expiring media URLs
- No public object-bucket access
- Encryption in transit and at rest using deployment-standard controls
- Server-side secrets management
- Viewer watermarking for sensitive review assets
- Audit download/share/publish actions
- Optional IP/device/session controls for high-security workspaces
- Retention/archival states
- Soft-delete and privileged purge workflows
- Backup and disaster-recovery policy
## 57. Expanded Service Architecture

## 58. Expanded API Blueprint

- AI generation status
- Media transcode/ingest progress
- QC progress
- Export/package build progress
- Live production dashboard updates
- Review comment/activity updates
## 59. Expanded Database Blueprint

- Use immutable version rows for approved scripts, call sheets, review versions, masters and delivery packages.
- Store measured technical metadata separately from user-entered/declared metadata where possible.
- Store checksums for media/master/delivery integrity.
- Do not cascade-delete production lineage records silently.
- Use explicit stale/superseded states for downstream artifacts after source changes.
- Indexes must include project/status/date and common relational lookup paths.
- Sorani text uses Unicode-capable storage and search normalization as a derived index.
## 60. Complete Frontend Navigation and Workspace UX

- Desktop: full project/navigation and dense production tables.
- Tablet: on-set production dashboard, slate/takes, continuity, call sheet and dailies prioritized.
- Phone: call-sheet view/confirmation, cast/crew call details, quick take/continuity status, notifications, secure review.
- RTL: navigation, drawers, breadcrumbs and forms mirror correctly in ckb-IQ while technical codes/timecodes remain readable LTR.
## 61. Expanded Roles and Permissions

## 62. Cross-Phase State Machines and Dependency Rules

## 63. Complete Release-Gate Acceptance Criteria

- Start an approved ShootingDay and see planned scenes/shots.
- Record multiple takes against stable shot IDs.
- Mark circle/director selects and expose them to AC Edit.
- Create continuity records with images and take/scene linkage.
- Create camera and sound reports.
- Generate DPR from actual day events.
- Show schedule variance without AI arithmetic.
- Create ingest session and verify checksum.
- Track primary/backup status separately.
- Generate and stream proxy derivative.
- Link source media to scene/shot/take.
- Open dailies review with Sorani/English comments.
- Prevent “verified backup” status when checksum verification has failed or is missing.
- Create edit version and send it to review.
- Frame/timecode comment survives new UI session and retains author/time.
- Approval is tied to immutable version.
- Picture lock emits dependency events.
- Create VFX task/version and approve final.
- Track color/audio/localization versions.
- Sorani subtitles render correctly RTL in web preview and export.
- Mixed Kurdish-English names/numbers remain in intended visual order.
- Timed-text QC correctly evaluates timings without corrupting RTL text.
- Kurdish review comments, notifications and production documents export correctly.
- Assemble immutable master candidate from approved components.
- Run configured QC profile and persist findings/measurements.
- Failed QC blocks delivery package approval unless authorized override policy explicitly permits it.
- Build delivery package against a versioned delivery profile.
- Readiness view lists exact missing requirements.
- Record delivery submission and accepted/rejected outcome without overwriting prior attempts.
## 64. Complete Testing Strategy

- Shot/take numbering and duplicate/slate collision rules
- Offline/queued on-set updates reconciliation where implemented
- Checksum and ingest-finalization tests
- Media derivative lineage tests
- Picture-lock → stale dependency tests
- Review approval immutable-version tests
- Subtitle timecode/readability/QC rules
- Audio track/channel declaration validation
- Master component/version integrity
- QC profile version tests
- Delivery package completeness rules
- Permission tests for external reviewer and delivery roles
- Large-upload signed-session expiry/retry behavior
- Concurrent on-set users updating production status
- Large media ingest sessions
- Many review comments on a long-form asset
- Long-running QC/package jobs
- Redis/job retry and idempotency
- Object-storage temporary outage behavior
- PostgreSQL fail/retry and transaction boundaries
- Recovery after browser/app reconnect
## 65. One Master Build — Recommended Engineering Sequence

## 66. Updated Developer Definition of Done

- Implements required backend domain model and frontend workflow.
- Uses canonical project/scene/shot/take/asset/version identifiers.
- Has ckb-IQ + English localization strings and passes RTL visual QA.
- Has server-side permissions and audit logging.
- Has deterministic rules for calculations/status validation; AI is advisory unless explicitly authorized.
- Has version/immutability behavior for approved artifacts.
- Emits/consumes required domain events and stale flags.
- Supports job idempotency/progress for long work.
- Handles Sorani Unicode round-trip through DB/API/export.
- Has unit/API/integration tests and relevant media/large-file tests.
- Has responsive behavior for intended desktop/tablet/mobile use.
- Does not expose secrets or private object-storage assets publicly.
- Has acceptance-test evidence before feature flag is enabled for customers.
## 67. Immediate Master Developer Handoff Checklist

- Freeze canonical IDs and shared schemas for Project, Scene, Shot, Take, MediaAsset, Version, Approval and DeliveryProfile.
- Implement ckb-IQ/RTL platform infrastructure globally before module-specific UI expansion.
- Add feature-flag/entitlement controls for every new module.
- Finalize domain-event contracts and stale-dependency behavior across the full lifecycle.
- Complete the pre-production modules already specified in Sections 7–12 on the shared architecture.
- Build AC Production dashboard plus Shot/Take and Continuity as the first production wave.
- Implement verified media ingest/checksum/derivative lineage before production-scale dailies.
- Connect Dailies and production selects directly into AC Edit.
- Implement immutable AC Review/version approval framework before VFX/color/sound workflows.
- Add localization/timed-text data model with Sorani RTL tests before subtitle automation.
- Implement Master + QC as separate but connected services.
- Implement delivery profiles/packages/readiness as versioned configuration, not hard-coded one-platform logic.
- Add rights/releases as readiness dependencies and secure document records.
- Expand Production Copilot only after structured services and permissions are reliable.
- Run the complete bilingual regression production from idea through delivery before public launch.
## 68. Final Product Vision — Art City AI: From Idea to Delivery

4. Kurdish Sorani / Central Kurdish Requirements (Non-Negotiable)

4.1 Language and direction model

4.2 RTL component rules

• Use CSS logical properties (margin-inline-start/end, padding-inline-start/end) instead of hard-coded left/right where possible.

• Use dir="rtl" at the appropriate layout root, not on every child indiscriminately.

• For mixed-direction tokens use <bdi>, Unicode bidi isolation or component-level dir="ltr" as appropriate.

• Icons with semantic direction (chevrons, back/forward, timeline arrows) must mirror in RTL; non-directional icons must not.

• Spreadsheet row headers, numeric columns and account codes can remain LTR while descriptive cells are RTL.

• Modal placement, sidebars, drawers, tab order and keyboard navigation must feel native in RTL.

• Do not infer language from direction. Arabic and Sorani are separate locales even though both are RTL.

4.3 Sorani screenplay formatting

The screenplay editor must support Kurdish dialogue and action while preserving industry screenplay semantics. Formatting is stored structurally, not by relying on spaces or tabs.

4.4 Kurdish text normalization policy

Maintain two values where necessary: display_text (exact authored form) and search_normalized (derived index form). The normalization layer may map common Arabic-script variants for search equivalence, remove optional tatweel and normalize Unicode composition. It must not silently rewrite a user’s stored character name, dialogue or legally meaningful text.

4.5 Localization keys

All UI text must come from localization keys. Do not hard-code English strings inside React components.

4.6 Example Sorani UI terms

4.7 AI behavior for Sorani

• Every AI text endpoint must accept language and output_language explicitly.

• Do not automatically translate Kurdish character/location names unless the user asks.

• Preserve Sorani punctuation, spelling and paragraph direction.

• Support Kurdish-only, English-only and bilingual script projects.

• Allow per-scene or per-dialogue translation while retaining the original as a parallel version.

• If generating JSON, text direction must never change the JSON schema; values are Unicode strings.

• Prompt templates should contain locale-aware instructions and examples tested with Sorani.

• Run automated regression tests using real Sorani strings, mixed Kurdish-English text, numbers, punctuation and filenames.

5. Target System Architecture

5.1 Existing stack alignment

The recommended implementation assumes the existing Art City AI architecture based on Next.js, FastAPI, PostgreSQL, Redis and MinIO/object storage. The pre-production suite should extend that stack instead of introducing an independent runtime unless a scaling requirement later justifies service extraction.

5.2 Source-of-truth principle

6. Canonical Project Model

6.1 Example project payload

7. Module 1 — AC Script

7.1 Goal

AC Script is a professional, multilingual screenplay workspace with AI assistance. It must support screenplay semantics, structured scene data and versioning rather than functioning as a generic rich-text editor.

7.2 Entry modes

• Start from idea

• Start from logline

• Start from synopsis

• Start from treatment

• Create from beat sheet

• Upload/import an existing screenplay

• Continue a script

• Rewrite or polish a script

• Adapt user-owned/source-cleared material

• Translate an existing script

• Create an episode, commercial, music video, documentary or social/AI drama

7.3 Guided generation pipeline

Each stage must be independently editable and approvable. The user can skip stages, but the system should encourage controlled development rather than generating an entire feature screenplay in one opaque operation.

7.4 Screenplay element types

7.5 Character Bible object

7.6 AI editor commands

• Rewrite / shorten / expand

• Improve dialogue

• Make dialogue more natural

• Increase/decrease suspense

• Increase/decrease comedy or darkness

• Add conflict

• Improve pacing

• Generate alternative scene

• Change location while preserving intent

• Translate selected range

• Convert dialogue to Sorani / English / Arabic

• Maintain character voice

• Reduce production complexity

• “Make this scene cheaper to produce” with explicit assumptions

7.7 Scene object created by parser

Recommendation: store script page length as eighths or another deterministic representation for scheduling, not only as floating-point values.

7.8 Version control

• Draft 1 / Draft 2 / Revision A / Revision B / Shooting Script / Locked Script.

• Never overwrite an approved/locked version.

• Maintain scene-level change records.

• Support compare/diff between versions.

• Any downstream module that depends on changed scenes receives a stale/out-of-date flag until reviewed.

• Locking a shooting script generates immutable revision metadata and an audit event.

7.9 Script import/export

8. Shared Scene Breakdown Core

This internal service is the central production data extractor. Budget and Call Sheet accuracy depend on it. The breakdown must be editable by production staff; AI extraction is only an initial proposal.

8.1 Breakdown categories

8.2 Breakdown item schema

25.3 AC Script

• Create/import a script and edit screenplay semantic elements.

• Generate a structured scene list.

• Generate/edit breakdown and approve items.

• Create new version, compare and lock.

• Changed locked-script dependencies are flagged downstream.

• Export a Sorani screenplay to PDF and DOCX without direction/glyph defects.

25.4 AC Storyboard

• Generate editable découpage from a selected scene.

• Store shots as structured records.

• Generate one or multiple storyboard frames.

• Regenerate one frame while retaining character/location lock references.

• Reorder shots and retain stable IDs/revision history.

• Export storyboard PDF and shot list XLSX/CSV.

• Send approved references to Cinema/Studio with lineage.

25.5 AC Budget

• Generate budget draft from breakdown/schedule assumptions.

• All totals are deterministic and backend-authoritative.

• Edit quantities/rates and see recalculated totals.

• Create/compare/lock budget versions.

• Use ckb-IQ UI while numeric calculations remain correct.

• Export XLSX/PDF.

• AI-estimated rates are clearly marked unverified until approved.

25.6 AC Call

• Generate call sheet only from a shooting day/schedule context.

• Populate scene and cast calls from canonical project data.

• Weather values are from an external weather source with timestamp.

• Publish a version and track recipients.

• Create a revision that supersedes the old version.

• Display latest version in Sorani, English or configured bilingual template.

• PDF export is production-readable on desktop and mobile.

26. Testing Plan

26.1 Automated tests

• Unit tests for budget formulas, page/eighth calculations and version rules.

• API permission tests for every privileged endpoint.

• Schema validation tests for AI structured outputs.

• RTL snapshot/visual regression tests for key screens.

• Sorani Unicode round-trip tests through DB/API/export.

• Mixed bidi test strings including INT./EXT., 24mm, T2.8, emails, phone numbers and Kurdish names.

• Dependency-event tests: script change → downstream stale flags.

• Concurrency tests for autosave/version locking.

• Job idempotency tests for storyboard/export generation.

• Tenant-isolation tests.

26.2 Required Sorani QA dataset

Maintain a small internal test project containing Sorani-only dialogue, bilingual dialogue, Kurdish names with ی/ک, punctuation, numbers, long paragraphs, right-to-left tables, mixed lens/technical notation, and exports. This project should run in every release regression.

27. Recommended Development Sequence

28. Do Not Build These as Four Independent AI Pages

The durable design is a shared production graph: structured project → script → scenes → elements → shots → schedule → budget/call sheets → creation/editing. AI should operate on that graph, not replace it.

29. AC Producer Copilot — Recommended Cross-Module Layer

After the four modules share structured data, add an “Ask AC Producer” side panel that performs project-aware queries and controlled actions.

• Which scene costs the most?

• Which actors have the most shooting days?

• Show all night exteriors.

• Show all scenes with children/minors.

• Which scenes require VFX?

• Can we group all Citadel scenes together?

• What changes if Scene 71 is removed?

• Reduce the draft budget by 15% and show the operational consequences.

• Which storyboard shots are out of date after the latest script revision?

• Generate a draft call sheet for tomorrow’s approved shooting day.

The Copilot should query structured project services and pass compact verified context to the AI. Do not dump the entire project into a prompt for every question.

30. Developer Definition of Done

• Feature has backend and frontend tests.

• Feature has ckb-IQ and en localization strings.

• Feature passes RTL visual QA.

• Feature enforces server-side permissions.

• AI actions record provider/model/cost/status.

• Expensive actions are idempotent and job-tracked.

• Production data is versioned where required.

• Exports are visually verified for Kurdish and English.

• Cross-module links retain project/scene/shot/asset lineage.

• Audit log records privileged state changes.

• No approved production artifact is silently overwritten by AI.

31. Pre-Production Foundation Vision

With this implementation, Art City AI becomes a continuous production environment rather than a collection of AI utilities:

Recommended product statement: “Art City AI — From Idea to Delivery.” The strategic value comes from continuity of data: every creative and production decision remains connected from screenplay through final edit.

32. Pre-Production Foundation Handoff Checklist

☐ Confirm the existing project/account/entitlement APIs that Pre-Production will extend.

☐ Add ckb-IQ localization and RTL infrastructure before building module UIs.

☐ Define canonical schemas for ScriptVersion, Scene, BreakdownItem, Character, Location and Asset.

☐ Implement domain events and stale-dependency flags.

☐ Build AC Script MVP with structured editor + scene parser.

☐ Build Breakdown Core and approval flow.

☐ Build shot/découpage schema and Storyboard MVP.

☐ Build deterministic budget engine and versioned budget grid.

☐ Build minimum viable shooting schedule core.

☐ Build call sheet version, publish and recipient-confirmation flow.

☐ Connect shared assets with Cinema and Studio; connect metadata handoff with Edit.

☐ Run English + Sorani regression project through the complete workflow before release.

Appendix A — Example Bilingual Scene

EXT. قەڵای هەولێر - NIGHT

ئارا بە هێواشی بەرەو دەروازەکە دەڕوات. دەنگی با لە ناو کۆڵانە کۆنەکاندا دەبیسترێت.

ئارا

ئێمە ئامادەین؟

کوردیا

لە سەرەتاوە ئامادە بووین.

Technical note: the editor must preserve the LTR token “EXT.” and “NIGHT” while the Kurdish location/action/dialogue remain RTL. Do not reorder the scene heading by string manipulation.

Appendix B — Example Budget Formula Contract

Appendix C — Minimal FastAPI Découpage Contract

Appendix D — Suggested Internal Service Names

END OF PRE-PRODUCTION FOUNDATION SECTION — COMPLETE HUB SPECIFICATION CONTINUES

33. Master Production Hub Scope and Operating Principle

This section expands the earlier Pre-Production specification into the complete Art City AI Production Hub. Everything defined in Sections 1–32 remains part of the master scope unless explicitly superseded below.

33.1 Complete module map

33.2 Single production graph

Stable IDs and lineage are mandatory. A media file imported during production must be traceable back to project → shooting day → scene → shot → take, and a final master must be traceable forward from those source records through edit, post, QC and delivery.

34. AC Production — Live Production Command Centre

AC Production is the operational command centre used while the project is actively shooting. It converts the approved schedule, call sheet, shot list and breakdown into live status and feeds actual results back into the project graph.

34.1 Users

• Producer / Executive Producer

• Director

• 1st Assistant Director

• Production Manager / Coordinator

• Script Supervisor

• Director of Photography / Camera team

• Sound team

• DIT / Data Manager

• Department heads with scoped permissions

34.2 Live dashboard

34.3 Scene state machine

All state changes must be timestamped and attributed. AI may recommend a state or identify risk, but only authorized users may finalize production-status changes.

34.4 Production timeline events

• Crew call actual

• First setup ready

• First shot

• Meal start/end

• Company move start/end

• Scene start/end

• Actor wrap

• Camera wrap

• Production wrap

• Incident or delay event

• Weather interruption

• Equipment failure

• Unplanned overtime trigger

35. AC Slate + Shot / Take Tracker

This module bridges the planned shot list and the footage actually captured. It should be usable on tablet/phone on set and remain functional under unstable connectivity with offline queue/synchronization where practical.

35.1 Take schema

35.2 Take ratings

• NG / False start

• Technical issue

• Performance hold

• Good

• Circle take

• Director select

• Editor select

• Pickup required

35.3 AC Edit handoff

AC Edit must receive shot/take metadata, select flags, scene/shot order, script references, continuity notes and linked proxy/original media. The editor should be able to filter instantly for Director Selects, Circle Takes, missing shots and pickups.

36. AC Continuity — Script Supervisor Workspace

AC Continuity manages script changes and visual/action continuity during shooting. The data must be scene-aware and take-aware rather than stored as free-form daily notes only.

36.1 Continuity categories

• Costume / wardrobe state

• Hair and makeup

• Props and prop position

• Food/drink levels

• Actor blocking and body/hand position

• Eyelines and screen direction

• Vehicle position/damage/state

• Blood, dirt, wetness, injuries and practical effects

• Dialogue changes / ad-libs

• Action changes

• Scene timing

• Camera axis / coverage notes

• Continuity reference photos

36.2 AI-assisted continuity

AI may compare approved continuity reference images and metadata and flag possible mismatches. It must label findings as POSSIBLE CONTINUITY ISSUE and provide the source frames/records. Human confirmation is mandatory; the system must not silently alter continuity records.

37. Camera, Sound and Department Reports

Production metadata must not depend on handwritten reports that are later retyped. Art City AI should provide structured digital reports with exportable PDF/CSV and links to media assets.

37.1 Camera report

• Camera body / serial or unit ID

• Card/reel/media ID

• Clip filename

• Scene / shot / take

• FPS / shutter / resolution / codec

• Lens / focal length / filtration

• LUT / look reference

• Timecode

• Technical notes

• Good/NG/Select status

• Media offload and checksum state

37.2 Sound report

• Recorder / media ID

• Audio filename / roll

• Scene / shot / take

• Timecode

• Track names and channel assignments

• Sample rate / bit depth

• Mic/source notes

• Wild tracks / room tone

• Technical/continuity notes

• Sync status

37.3 Department quick reports

Art, wardrobe, makeup, locations, VFX and SFX departments should have lightweight forms for scene completion, continuity state, consumed materials, special notes, damage/incident flags and next-day preparation.

38. AC Dailies + Media Ingest

AC Dailies is the controlled bridge between set media and AC Edit. The ingest system must prioritize data integrity, provenance and speed. Generative AI is not authoritative for checksum or file-integrity validation.

38.1 Required ingest pipeline

38.2 Integrity requirements

• Use cryptographic checksum verification for copy validation.

• Record source card/media ID and destination object/storage key.

• Never mark BACKED UP based only on upload completion; verification must succeed.

• Track at least primary copy and backup-copy status as separate fields.

• Prevent media deletion while retention/backup policy is unsatisfied unless privileged override is logged.

• Store proxy as derivative of original asset, not as an unrelated upload.

38.3 Dailies review features

• Secure streaming proxy

• Burn-in overlays configurable by role

• Scene/shot/take navigation

• Favourites / Director Select

• Frame/timecode comments

• Private notes vs shared notes

• Watermark per viewer when required

• Download permission

• Approval / hold / pickup flag

39. AC Media Asset Management (MAM)

The Production Hub requires a versioned media and document registry. Object storage holds binaries; PostgreSQL holds authoritative metadata, relationships, versions, rights/status and checksums.

39.1 Asset types

39.2 Asset schema essentials

39.3 Naming convention

Provide a configurable canonical naming policy. Example: PROJECT-SCENE-SHOT-TAKE-CAMERA-DATE-VERSION. The system must preserve the original filename separately and must not rely on filename parsing as the sole source of truth.

40. AC Daily Production Report (DPR)

At wrap, Art City AI should generate a structured Daily Production Report from actual production events rather than asking the production office to rebuild the day manually.

40.1 DPR sections

• Production day/date/location

• Crew call / first shot / meal / last shot / wrap

• Scenes scheduled / completed / partial / moved

• Pages planned vs completed

• Cast worked and wrap times

• Extras and special participants

• Equipment / vehicles / special resources

• Weather summary from verified source

• Incidents / delays / damage

• Overtime

• Media cards/rolls and ingest/backup summary

• Notes for next shooting day

• Authorized sign-off

40.2 Planned vs actual

The example is illustrative only. Actual values are derived from project records. Cost impacts must use the deterministic budget/cost engine and configured rates.

41. Production Crew, Cast and Equipment Operations

The hub needs production-specific people and equipment records to drive schedules, call sheets, permissions and on-set status. This is not a general corporate HR system.

41.1 Production participant object

• Person / contact identity

• Production role and department

• Character/cast relationship if applicable

• Project availability

• Production day calls and actual work times

• Production documents/releases status

• Emergency contact visibility governed by permissions

• Communication preference

• Project-specific rate/reference only where authorized

• Portal/account invitation status

41.2 Equipment operations

Découpage/shot requirements should be able to generate a proposed equipment list. Department heads approve or adjust it; AI suggestions do not reserve equipment automatically.

42. AC Review — Frame-Accurate Review and Approval

AC Review provides secure review, commenting and approval across dailies, rough cuts, VFX, color, sound, trailers and masters. This is a key collaboration layer across the entire Production Hub.

42.1 Core features

• Frame/timecode-accurate comments

• Threaded replies and @mentions

• Annotations/drawings where technically supported

• Version selector and side-by-side/overlay comparison where appropriate

• Approval / changes requested / rejected / locked states

• Private comments by permission

• Secure external review link

• Expiry, passcode and download controls

• Viewer watermarking

• Read/approval audit trail

• Sorani RTL comments and bilingual review

42.2 Review state machine

43. AC Edit — Post-Production Core Integration

AC Edit remains the principal editing layer. The Complete Production Hub must extend it with production-aware metadata, review/version workflow and downstream handoffs rather than replacing its existing editing functions.

43.1 Inputs AC Edit should receive automatically

• Locked/active script version

• Scene and shot IDs

• Découpage/shot order

• Director selects and circle takes

• Camera/sound metadata

• Continuity notes and script changes

• Synced proxies and original-media lineage

• Music/graphic/reference assets from Studio/Cinema

• Deliverable aspect-ratio targets

• Rights/status flags for restricted media

43.2 Edit version object

43.3 Picture lock rule

PICTURE_LOCKED is a privileged state that creates an immutable version reference and triggers downstream readiness checks for VFX, color, sound, music, localization and mastering. Any subsequent picture change must create a new version and mark dependent post assets as potentially stale.

44. AC VFX — Shot Tracking and Review

VFX management should be shot-centric and linked directly to the originating production shot and edit version.

44.1 VFX shot lifecycle

44.2 VFX shot fields

• VFX shot code

• Scene/shot/take linkage

• Plate/source asset

• Edit in/out/timecode reference

• Task/type: cleanup, comp, key, tracking, CG, sky, screen, etc.

• Vendor/artist assignment

• Brief and reference files

• Target resolution/color pipeline

• Version history

• Review comments

• Status/deadline/priority

• Final render asset and checksum

Script Breakdown and Storyboard may flag potential VFX shots early, but VFX production records are created/approved by authorized users.

45. AC Color — Color Workflow Management

The hub should manage color references, turnovers, versions and approvals while allowing grading work to occur in specialist tools. It does not need to recreate a professional grading engine unless that is an explicit separate product objective.

45.1 Required records

• Camera color metadata / log/gamut

• On-set LUT/look reference

• Approved creative look references

• Color turnover asset/version

• Conform status

• Grade version and reviewer

• Display/master target (e.g., SDR/HDR when supported)

• Review/approval status

• Final graded master lineage

46. AC Sound Post — Dialogue, ADR, Foley, Music and Mix

Sound post should be managed as structured deliverables and approvals with strong channel-layout metadata because sound configuration directly affects final delivery acceptance.

46.1 Sound workstreams

46.2 Channel-layout metadata

QC must validate declared vs measured channel structure and flag suspicious content routing. The platform should never infer a passed delivery merely because a file has six channels.

47. AC Localization — Subtitles, Captions, Dubbing and Multilingual Masters

Localization is a first-class post-production module, especially for Kurdish projects. Sorani support must include both the application interface and professional audiovisual text workflows.

47.1 Languages and scripts

At minimum, the data model must be language-agnostic and support Kurdish Sorani (ckb), Kurdish Badini/Kurmanji where configured, English, Arabic, Turkish, Persian and additional languages without schema changes.

47.2 Subtitle/caption workflow

47.3 Required timed-text fields

• Cue ID

• Start/end timecode

• Text

• Language / locale

• Speaker when required

• Style/type: subtitle, SDH/CC, forced narrative

• Line count / characters / reading-speed metrics

• RTL/LTR direction metadata if needed for renderer

• Review state

• Source translation/version

• Export format

47.4 Sorani-specific requirements

• Correct RTL rendering and glyph shaping in preview/export

• Mixed Kurdish/English names and numbers without visual reordering

• Unicode normalization only for search/indexing; preserve authored display text

• Kurdish punctuation and line-breaking regression tests

• Bilingual subtitle comparison view

• Human linguistic approval before final delivery status

47.5 Formats

Support SRT and WebVTT at minimum, with extensible support for TTML/IMSC, STL, ASS/SSA and platform-specific XML where contractually required. Export adapters must be versioned and tested independently.

48. AC Mastering — Final Master Builder

Mastering creates controlled, immutable final-output candidates from approved picture, sound, text and metadata components. It should be workflow-aware and template-driven.

48.1 Master components

• Approved picture/version

• Approved full mix

• Stereo/5.1/etc. audio tracks as required

• M&E

• Subtitle/caption tracks

• Textless elements where required

• Credits/version information

• Technical specification profile

• Artwork/metadata references

• Checksum and manifest

48.2 Master states

An APPROVED_MASTER must be immutable. Corrections generate a new master version and preserve prior QC reports for auditability.

49. AC QC — Automated and Human Quality Control

QC is both automated inspection and human approval. Automated checks must distinguish objective measured failures from heuristic warnings. The system should support delivery-profile-specific rule sets.

49.1 Video checks

• Resolution/dimensions

• Frame rate and cadence metadata

• Codec/container/profile

• Aspect ratio / active image

• Duration

• Black/freeze/flash heuristics

• Dropped/corrupt frame detection where supported

• Color-space/HDR metadata consistency where applicable

• Bars/slate/leader rules per delivery profile

49.2 Audio checks

• Expected track count and channel mapping

• Sample rate / bit depth / codec

• Silence/near-silence anomalies

• Clipping / true peak

• Integrated loudness against configured target

• A/V sync checks where measurable

• Language/role labeling

• M&E presence and configuration

49.3 Subtitle checks

• Cue timing / zero or negative duration

• Overlap/collision rules

• Reading-speed threshold

• Line/character limits by profile

• Out-of-bounds timing beyond program duration

• Missing/duplicate cue IDs

• RTL render validation for Sorani

• Forced/SDH labeling consistency

49.4 QC result model

50. AC Delivery — Packaging, Readiness and Delivery Control

Delivery turns approved masters and metadata into platform/cinema/broadcast/social packages. The engine must be profile-driven because requirements differ by client, platform, territory and contract.

50.1 Delivery Matrix

50.2 Delivery readiness score

The UI may display a readiness percentage, but it must also list every missing/failed requirement. Example: 84% READY — missing Arabic subtitles, M&E QC, 2000×3000 artwork and approved music cue sheet.

50.3 Delivery attempt records

• Recipient/platform/client

• Profile/specification version

• Package version and checksum

• Method / endpoint / transfer reference

• Submitted by / date

• Status: prepared/sent/received/rejected/accepted

• Rejection reason / QC feedback

• Resubmission relationship

• Receipt/confirmation evidence

50.4 Cinema / OTT / broadcast / social profiles

Implement delivery as configurable profiles rather than hard-coded brand rules. Profiles should define required components, technical limits, naming patterns, metadata fields, package manifests and validation rules. Platform requirements change over time; administrators must be able to version profiles.

51. AC Rights, Releases and Production Documents

Rights and releases are production-readiness and delivery-readiness dependencies. The hub should track evidence and status; it is not a substitute for legal advice or contract review.

51.1 Rights categories

• Script/story rights

• Writer/director/producer agreements

• Cast release / performance rights

• Extra/minor/guardian consent where applicable

• Location release

• Music composition/master rights

• Archive footage / stock footage / still-image rights

• Artwork/logo/trademark permission where applicable

• Voice/likeness/AI-use permissions where applicable

• Territory/platform/language/window restrictions

51.2 Rights object

51.3 Production forms

• Cast/extra release

• Location release

• Crew deal memo/production acknowledgement

• NDA/confidentiality document

• Equipment checkout/return

• Vehicle request/use form

• Incident report

• Expense/petty-cash reference if enabled in project

• Production consent/authorization forms

• Call-sheet acknowledgement

E-signature support may be added through a pluggable signing provider. Signed-document immutability, audit timestamp and signer identity must be preserved.

52. Production and Post Readiness Scores

Readiness is an executive decision-support layer over explicit project requirements. It must not hide blockers behind an averaged percentage.

52.1 Production Readiness

52.2 Post / Delivery Readiness

53. AC Production Copilot — Full Project Intelligence Layer

The Copilot becomes the natural-language interface over structured production services. It must retrieve verified project data through permission-aware service calls and cite the records used in its answer inside the product UI.

53.1 Example questions

• What are we shooting tomorrow?

• Which actors have not confirmed tomorrow’s call?

• Which scenes are behind schedule?

• Which planned shots have no captured takes?

• Show Director Selects from Scene 21.

• Which media cards are not verified in two locations?

• Which scenes have unresolved continuity warnings?

• Which VFX shots are still in review?

• What is blocking picture lock?

• Which Sorani subtitles failed reading-speed or RTL QC?

• Is the delivery package ready for the selected client profile?

• What changed after Script Revision C?

53.2 Copilot action policy

53.3 Evidence model

Copilot answers should reference internal record links (Scene 21, Call Sheet V3, QC Report #12, etc.) so a producer can inspect the underlying source. The model must not invent project status when a source record is absent.

54. Notifications, Approvals and Activity Centre

A complete hub needs a unified notification and approval inbox across all modules.

54.1 Notification events

• Script revision affects downstream artifacts

• Storyboard/shot list ready for approval

• Budget threshold/variance warning

• Call sheet published/revised

• Cast/crew confirmation missing

• Schedule delay/overtime risk

• Media backup incomplete

• Continuity/VFX/post review comment assigned

• Review approval/changes requested

• QC failure

• Rights document expiring/missing

• Delivery accepted/rejected

54.2 Approval object

Notifications must be localized by user locale (including ckb-IQ) and preserve the original project/asset names without forced translation.

55. Global Search and Production Knowledge Graph

Search should work across project metadata, scripts, scenes, characters, locations, shots, takes, call sheets, comments, assets, rights, post tasks, QC reports and delivery records, subject to permissions.

55.1 Search modes

• Exact ID/code search

• Full-text keyword search

• Sorani normalized search index

• Filters by project/module/status/date/person/language

• Semantic search over approved textual content where enabled

• Natural-language project query through Copilot

55.2 Sorani search

Store original text unchanged. Generate a separate search-normalized form for common Kurdish/Arabic Unicode variants according to the policy already defined in Section 4. Search results must display authored text, not the normalized index string.

56. Storage, Media Security and Access Architecture

Production footage and unreleased scripts are high-value confidential assets. Security controls must be designed as core platform requirements.

56.1 Required controls

• Workspace/tenant isolation

• Project/role scoped permissions

• Signed expiring media URLs

• No public object-bucket access

• Encryption in transit and at rest using deployment-standard controls

• Server-side secrets management

• Viewer watermarking for sensitive review assets

• Audit download/share/publish actions

• Optional IP/device/session controls for high-security workspaces

• Retention/archival states

• Soft-delete and privileged purge workflows

• Backup and disaster-recovery policy

56.2 Media access tiers

57. Expanded Service Architecture

The existing Next.js + FastAPI + PostgreSQL + Redis + MinIO/object-storage architecture remains suitable, but the service boundaries should now cover the complete production lifecycle.

57.1 Recommended application services

57.2 Event bus/domain events

Use an internal domain-event mechanism so dependent services can react without hard-wiring every module to every other module. Events may be implemented with the current infrastructure initially, but the event contract should be explicit and versioned.

58. Expanded API Blueprint

The existing API conventions in Section 19 remain mandatory. Add endpoints/services for the production and post-production scope.

58.1 Media APIs

Large media must use multipart/direct-to-object-storage upload patterns with server-issued signed upload sessions rather than proxying multi-gigabyte files through ordinary application request bodies. Finalization must verify size/checksum and create the MediaAsset record transactionally.

58.2 WebSocket/SSE events

• AI generation status

• Media transcode/ingest progress

• QC progress

• Export/package build progress

• Live production dashboard updates

• Review comment/activity updates

59. Expanded Database Blueprint

Add the following tables/entities to the existing Section 18 model. Naming may follow the project’s established conventions, but relationships and immutability rules are required.

59.1 Critical database rules

• Use immutable version rows for approved scripts, call sheets, review versions, masters and delivery packages.

• Store measured technical metadata separately from user-entered/declared metadata where possible.

• Store checksums for media/master/delivery integrity.

• Do not cascade-delete production lineage records silently.

• Use explicit stale/superseded states for downstream artifacts after source changes.

• Indexes must include project/status/date and common relational lookup paths.

• Sorani text uses Unicode-capable storage and search normalization as a derived index.

60. Complete Frontend Navigation and Workspace UX

The user should experience one project workspace with phase-oriented navigation. Cinema, Studio and Edit remain visible as native Art City AI creation/post tools, not external links.

60.1 Responsive requirements

• Desktop: full project/navigation and dense production tables.

• Tablet: on-set production dashboard, slate/takes, continuity, call sheet and dailies prioritized.

• Phone: call-sheet view/confirmation, cast/crew call details, quick take/continuity status, notifications, secure review.

• RTL: navigation, drawers, breadcrumbs and forms mirror correctly in ckb-IQ while technical codes/timecodes remain readable LTR.

61. Expanded Roles and Permissions

Extend Section 16 with post and delivery roles. Permissions remain granular and server-enforced.

62. Cross-Phase State Machines and Dependency Rules

The platform’s real advantage comes from knowing what becomes stale when a source changes.

62.1 Stale behavior

Never delete or silently regenerate approved downstream work. Mark it OUT_OF_DATE / REVIEW_REQUIRED, show the source change, and let an authorized user choose regenerate, update manually, accept unchanged, or supersede.

63. Complete Release-Gate Acceptance Criteria

All earlier acceptance criteria remain in force. The following criteria are added for the Complete Production Hub.

63.1 Production

• Start an approved ShootingDay and see planned scenes/shots.

• Record multiple takes against stable shot IDs.

• Mark circle/director selects and expose them to AC Edit.

• Create continuity records with images and take/scene linkage.

• Create camera and sound reports.

• Generate DPR from actual day events.

• Show schedule variance without AI arithmetic.

63.2 Dailies / media

• Create ingest session and verify checksum.

• Track primary/backup status separately.

• Generate and stream proxy derivative.

• Link source media to scene/shot/take.

• Open dailies review with Sorani/English comments.

• Prevent “verified backup” status when checksum verification has failed or is missing.

63.3 Post and review

• Create edit version and send it to review.

• Frame/timecode comment survives new UI session and retains author/time.

• Approval is tied to immutable version.

• Picture lock emits dependency events.

• Create VFX task/version and approve final.

• Track color/audio/localization versions.

63.4 Sorani localization

• Sorani subtitles render correctly RTL in web preview and export.

• Mixed Kurdish-English names/numbers remain in intended visual order.

• Timed-text QC correctly evaluates timings without corrupting RTL text.

• Kurdish review comments, notifications and production documents export correctly.

63.5 Master/QC/delivery

• Assemble immutable master candidate from approved components.

• Run configured QC profile and persist findings/measurements.

• Failed QC blocks delivery package approval unless authorized override policy explicitly permits it.

• Build delivery package against a versioned delivery profile.

• Readiness view lists exact missing requirements.

• Record delivery submission and accepted/rejected outcome without overwriting prior attempts.

64. Complete Testing Strategy

Testing must include deterministic domain logic, media integrity, RTL/UI visual regression, production concurrency and workflow state transitions.

64.1 Additional automated tests

• Shot/take numbering and duplicate/slate collision rules

• Offline/queued on-set updates reconciliation where implemented

• Checksum and ingest-finalization tests

• Media derivative lineage tests

• Picture-lock → stale dependency tests

• Review approval immutable-version tests

• Subtitle timecode/readability/QC rules

• Audio track/channel declaration validation

• Master component/version integrity

• QC profile version tests

• Delivery package completeness rules

• Permission tests for external reviewer and delivery roles

• Large-upload signed-session expiry/retry behavior

64.2 End-to-end regression project

Maintain one internal bilingual Sorani/English test production that progresses through: script → breakdown → storyboard → budget → schedule → call sheet → production day → takes/continuity → ingest/dailies → AC Edit → review → VFX/color/sound/localization → master → QC → delivery package. The test project must include mixed-direction scene headings, Kurdish subtitles, multiple audio layouts and at least one intentionally failing QC item.

64.3 Load and resilience

• Concurrent on-set users updating production status

• Large media ingest sessions

• Many review comments on a long-form asset

• Long-running QC/package jobs

• Redis/job retry and idempotency

• Object-storage temporary outage behavior

• PostgreSQL fail/retry and transaction boundaries

• Recovery after browser/app reconnect

65. One Master Build — Recommended Engineering Sequence

The entire scope should be approved and architected now, but engineering should proceed in dependency order so teams can work concurrently against stable contracts.

66. Updated Developer Definition of Done

• Implements required backend domain model and frontend workflow.

• Uses canonical project/scene/shot/take/asset/version identifiers.

• Has ckb-IQ + English localization strings and passes RTL visual QA.

• Has server-side permissions and audit logging.

• Has deterministic rules for calculations/status validation; AI is advisory unless explicitly authorized.

• Has version/immutability behavior for approved artifacts.

• Emits/consumes required domain events and stale flags.

• Supports job idempotency/progress for long work.

• Handles Sorani Unicode round-trip through DB/API/export.

• Has unit/API/integration tests and relevant media/large-file tests.

• Has responsive behavior for intended desktop/tablet/mobile use.

• Does not expose secrets or private object-storage assets publicly.

• Has acceptance-test evidence before feature flag is enabled for customers.

67. Immediate Master Developer Handoff Checklist

• Freeze canonical IDs and shared schemas for Project, Scene, Shot, Take, MediaAsset, Version, Approval and DeliveryProfile.

• Implement ckb-IQ/RTL platform infrastructure globally before module-specific UI expansion.

• Add feature-flag/entitlement controls for every new module.

• Finalize domain-event contracts and stale-dependency behavior across the full lifecycle.

• Complete the pre-production modules already specified in Sections 7–12 on the shared architecture.

• Build AC Production dashboard plus Shot/Take and Continuity as the first production wave.

• Implement verified media ingest/checksum/derivative lineage before production-scale dailies.

• Connect Dailies and production selects directly into AC Edit.

• Implement immutable AC Review/version approval framework before VFX/color/sound workflows.

• Add localization/timed-text data model with Sorani RTL tests before subtitle automation.

• Implement Master + QC as separate but connected services.

• Implement delivery profiles/packages/readiness as versioned configuration, not hard-coded one-platform logic.

• Add rights/releases as readiness dependencies and secure document records.

• Expand Production Copilot only after structured services and permissions are reliable.

• Run the complete bilingual regression production from idea through delivery before public launch.

68. Final Product Vision — Art City AI: From Idea to Delivery

The target product is a unified film and media Production Operating System in which AI assists creative and operational decisions while structured production data remains authoritative. Cinema and Studio provide generative creation capabilities; AC Script and the pre-production modules plan the work; AC Production records what actually happened; AC Edit and post modules transform the captured media; Mastering/QC validate the result; Delivery packages and tracks the approved outputs.

Appendix E — Production Status Enums

Appendix F — Example Production Event Payload

Appendix G — Sorani / RTL Production QA Samples

Use these as regression concepts; the QA team should expand them into real fixtures and screenshots.

Appendix H — Delivery Profile Contract (Conceptual)

Appendix I — Non-Scope Boundary

This master specification is intentionally focused on the Art City AI filmmaking and media-production lifecycle. General corporate administration, enterprise HR/payroll, company-wide accounting, unrelated procurement, and unrelated CRM/ERP functions are outside this Production Hub specification. Production-specific budgets, actual-cost references, crew participation, equipment usage, releases and delivery records remain in scope where they directly support a film/media project.

END OF COMPLETE PRODUCTION HUB MASTER SPECIFICATION

Art City AI — From Idea to Delivery.

=== TABLE 0 ===

Core product decision / Build one connected production operating system. Script, scene breakdown, storyboard/découpage, budget, shooting schedule and call sheet must use the same project data. Any approved change should propagate as a dependency event rather than forcing users to re-enter data.

=== TABLE 1 ===

IDEA / CONCEPT /       ↓ / AC SCRIPT → SCENE BREAKDOWN → AC STORYBOARD / DÉCOUPAGE /       ↓                         ↓ / AC BUDGET ← PRODUCTION SCHEDULE → AC CALL /       ↓                         ↓ / ART CITY AI STUDIO / CINEMA → PRODUCTION → ART CITY AI EDIT /       ↓ / MASTERING / DELIVERY / DISTRIBUTION

=== TABLE 2 ===

Product | Role in ecosystem | Required Pre-Production connection

Art City AI Platform | Account, projects, subscriptions, permissions, assets and AI orchestration | Pre-Production becomes a new workspace/module inside the same authenticated product.

Art City AI Cinema | Campaign/cinematic generation and larger AI-film workflows | Receives approved scripts, character/location references, shot plans, storyboards and production metadata.

Art City AI Studio | Single-asset and creative generation workflows | Receives character, prop, wardrobe, location and visual-reference objects created during pre-production.

Art City AI Edit | AI-assisted editing and repurposing | Receives script, scene/shot IDs, continuity metadata, slate/take metadata, intended shot order and delivery targets.

=== TABLE 3 ===

project_id = AC-PROD-YYYY-NNNN / workspace_id = tenant/workspace UUID / owner_user_id = UUID / locale = ckb-IQ | en | ar-IQ | ... / default_currency = USD | IQD | ...

=== TABLE 4 ===

Locale requirement / Use BCP 47 locale ckb-IQ for Sorani/Central Kurdish in Iraq. Do not model Sorani merely as generic “ku” and do not treat RTL as a visual afterthought.

=== TABLE 5 ===

Requirement | Implementation rule | Acceptance test

Locale | Use ckb-IQ in user profile, project locale and localization files. | A user can switch English and Sorani without losing project data.

Direction | Set document/root direction to RTL for Sorani surfaces; allow local LTR islands for codes, emails, lens values and filenames. | Mixed “INT. / EXT.”, scene numbers and Kurdish text display in correct order.

Unicode | Store Unicode UTF-8 end-to-end; normalize canonical text for indexing without destructively changing display strings. | Kurdish names retain exact user spelling after save/export/reload.

Fonts | Ship/web-load a Kurdish-capable font family and define robust Arabic-script fallback. | No missing glyphs in UI, PDF, DOCX or generated boards.

Numbers | Allow project preference for Latin 0-9 or Arabic-Indic/Persian-style display while storing numeric values as numbers. | Budget calculations are unaffected by display digit style.

Dates/time | Store ISO timestamps in UTC; render dates/times in project/user locale and timezone. | Call sheet date and call times display correctly for Erbil timezone.

Search | Implement normalized search aliases for common Arabic/Kurdish letter variants, but never overwrite original names. | Search finds expected Kurdish names even with common ي/ی or ك/ک variant input.

Exports | PDF/DOCX/print layouts must preserve RTL, table alignment and Kurdish glyph shaping. | No reversed text, detached letters or left-aligned Kurdish paragraphs.

=== TABLE 6 ===

Element | Stored type | Sorani behavior

Scene Heading | scene_heading | Can contain Kurdish location text plus LTR production tokens such as INT./EXT.

Action | action | RTL paragraph for Sorani; normal prose wrapping.

Character | character | RTL or centered/positioned according to screenplay template; preserve exact name.

Dialogue | dialogue | RTL text with punctuation and mixed numbers preserved.

Parenthetical | parenthetical | RTL content within screenplay element constraints.

Transition | transition | May be localized or use conventional English token; user/project setting controls output.

Shot | shot | Supports Kurdish description plus LTR technical values (35mm, T2.8, 24fps).

=== TABLE 7 ===

display_text:      "کوردستان" / search_normalized: derived searchable representation /  / Rule: normalization is for search/indexing, NOT destructive editing.

=== TABLE 8 ===

locales/ /   en/common.json /   ckb-IQ/common.json /   ar-IQ/common.json /  / Example keys: /   project.title /   script.newDraft /   scene.sceneNumber /   storyboard.generate /   budget.total /   callsheet.crewCall /   action.approve /   action.lock

=== TABLE 9 ===

English key | Suggested Sorani display | Note

Project | پڕۆژە | Terminology should be editable by localization administrators.

Script / Screenplay | سیناریۆ / سکرین‌پلەی | Use product-approved terminology consistently.

Scene | دیمەن | 

Characters | کارەکتەرەکان | 

Locations | شوێنەکان | 

Storyboard | ستۆریبۆرد | 

Découpage | دیکوپاژ | Retain industry term if preferred by Art City.

Budget | بودجە | 

Shooting Schedule | خشتەی وێنەگرتن | 

Call Sheet | خشتەی بانگهێشت / Call Sheet | Allow bilingual label if production teams prefer it.

Approve | پەسەندکردن | 

Lock | قفڵکردن | 

Export | هەناردەکردن | 

=== TABLE 10 ===

ART CITY AI /                                 │ /                    ┌────────────▼────────────┐ /                    │   PROJECT / WORKSPACE    │ /                    │ Auth • Plan • Credits    │ /                    └────────────┬────────────┘ /                                 │ /        ┌────────────────────────┼────────────────────────┐ /        │                        │                        │ /   PRE-PRODUCTION             CINEMA                   STUDIO /        │                        │                        │ /        ├─ AC Script             │                        │ /        ├─ Breakdown Core ◄──────┼──── shared assets ─────┤ /        ├─ AC Storyboard         │                        │ /        ├─ Schedule Core         │                        │ /        ├─ AC Budget             │                        │ /        └─ AC Call               │                        │ /        │                        │                        │ /        └────────────────────────┼────────────────────────┘ /                                 ▼ /                            ART CITY AI EDIT /                        Edit • Repurpose • Deliver

=== TABLE 11 ===

Layer | Recommended responsibility

Next.js | App Router pages, localized UI, screenplay editor shell, storyboard grid, budget sheet, call sheet preview, project navigation.

FastAPI | Domain APIs, permission checks, business rules, deterministic calculations, AI orchestration and exports.

PostgreSQL | Canonical structured production data, versions, permissions, approvals, schedule, budgets and audit metadata.

Redis | Background job state, queues, rate limiting, locks, cached derived data and AI-generation status.

MinIO/Object Storage | Storyboard frames, uploaded scripts, reference images, documents, generated PDFs/DOCX/XLSX and production attachments.

AI Provider Layer | Provider-agnostic text/image inference adapters with structured output validation and cost logging.

=== TABLE 12 ===

Database first / AI output becomes production data only after schema validation and, where required, human approval. Never let a raw model response directly overwrite an approved screenplay, budget, shooting schedule or call sheet.

=== TABLE 13 ===

Project / ├── Project Metadata / ├── Script(s) / │   └── Script Versions / │       └── Scenes / │           ├── Breakdown Items / │           ├── Characters / Cast / │           ├── Locations / │           └── Shots / Storyboard Frames / ├── Production Schedule / │   └── Shooting Days / ├── Budget / │   └── Budget Versions / Lines / ├── Call Sheets / ├── Assets / References / ├── Documents / ├── Approvals / Comments / ├── Audit Log / └── AI Generation Log

=== TABLE 14 ===

{ /   "project_id": "AC-PROD-2026-0001", /   "title": "Project Title", /   "project_type": "feature_film", /   "primary_locale": "ckb-IQ", /   "content_languages": ["ckb-IQ", "en"], /   "production_country": "IQ", /   "timezone": "Asia/Baghdad", /   "currency": "USD", /   "status": "pre_production", /   "owner_user_id": "uuid", /   "workspace_id": "uuid" / }

=== TABLE 15 ===

IDEA → LOGLINE → PREMISE → CHARACTER BIBLE → WORLD/LOCATION BIBLE /      → SYNOPSIS → TREATMENT → BEAT SHEET → ACT STRUCTURE /      → SCENE OUTLINE → SCREENPLAY → STRUCTURED BREAKDOWN

=== TABLE 16 ===

Type | Required behavior

scene_heading | INT/EXT, location, time-of-day; generates/links Scene object.

action | Normal action description.

character | Links to Character object when matched/selected.

dialogue | Dialogue body; locale-aware RTL/LTR.

parenthetical | Actor/performance note.

transition | CUT TO, DISSOLVE, localized equivalent or custom.

shot | Technical shot cue.

general | Non-standard text/comment when needed.

=== TABLE 17 ===

{ /   "character_id": "CHAR-001", /   "name": "ئارا", /   "name_latin": "Ara", /   "age": 32, /   "role": "protagonist", /   "description": "...", /   "background": "...", /   "motivation": "...", /   "conflict": "...", /   "relationships": [], /   "visual_description": "...", /   "wardrobe_refs": [], /   "voice_description": "...", /   "character_arc": "..." / }

=== TABLE 18 ===

{ /   "scene_number": 21, /   "slugline": "EXT. قەڵای هەولێر - NIGHT", /   "int_ext": "EXT", /   "location_id": "LOC-004", /   "time_of_day": "night", /   "characters": ["CHAR-001", "CHAR-003"], /   "extras": 20, /   "props": [], /   "vehicles": [], /   "special_effects": [], /   "vfx": [], /   "wardrobe": [], /   "script_pages_eighths": 10, /   "estimated_screen_time_seconds": 94 / }

=== TABLE 19 ===

Format | Direction | Requirement

PDF | Import/Export | Import may require parser review; export must preserve RTL.

DOCX | Import/Export | Preserve Unicode and bilingual text.

TXT | Import/Export | UTF-8.

Fountain | Import/Export | Map screenplay semantics; test RTL carefully.

FDX | Import/Export | Implement where compatible; document any third-party RTL limitations.

JSON / AC Project | Import/Export | Lossless internal exchange format.

=== TABLE 20 ===

Department | Elements

Cast | Principal, supporting, day players, children, extras, stunt performers.

Locations | Location, set, interior/exterior, permits, parking, unit base.

Art | Set construction, dressing, props, graphics, practical elements.

Costume | Wardrobe, changes, duplicates, special costume.

Hair/Makeup | Hair, beauty makeup, prosthetics, blood/dirt/continuity.

Vehicles/Animals | Picture vehicles, transport vehicles, animals, handlers.

Camera/Grip/Lighting | Special camera, lenses, motion, rigging, lighting, generators.

Sound | Playback, special microphones, music playback, noisy conditions.

SFX/VFX/Stunts | Practical effects, VFX, green/blue screen, stunt needs.

Logistics | Transport, accommodation, catering, security, medics, permits.

Safety/Special | Weapons/replicas, minors, water, heights, fire, traffic, etc.; always human-reviewed.

=== TABLE 21 ===

{ /   "id": "uuid", /   "project_id": "uuid", /   "scene_id": "uuid", /   "category": "prop", /   "name": "دەمانچەی ساختە", /   "quantity": 1, /   "department": "art", /   "source": "ai_suggested", /   "approved": false, /   "notes": "Human safety review required", /   "linked_asset_ids": [] / }

=== TABLE 22 ===

{ /   "shot_id": "21A", /   "scene_id": "uuid", /   "shot_number": 1, /   "shot_size": "EWS", /   "lens_mm": 24, /   "camera_angle": "eye_level", /   "movement": "crane_down", /   "duration_seconds": 6, /   "characters": ["CHAR-001"], /   "action": "...", /   "dialogue_reference": "...", /   "lighting_notes": "...", /   "sound_notes": "...", /   "equipment": [], /   "continuity_notes": "...", /   "storyboard_prompt": "..." / }

=== TABLE 23 ===

Code | Meaning

ECU | Extreme Close-Up

CU | Close-Up

MCU | Medium Close-Up

MS | Medium Shot

MLS | Medium Long Shot

FS | Full Shot

WS | Wide Shot

EWS | Extreme Wide Shot

OTS | Over-the-Shoulder

POV | Point of View

INSERT | Insert

CUTAWAY | Cutaway

2S | Two Shot

EST | Establishing Shot

DRONE | Drone/Aerial

=== TABLE 24 ===

Critical requirement / Generated storyboard frames must reference persistent Character Lock and Location Lock data. Do not regenerate each frame from unstructured prose; this causes identity, costume and spatial continuity drift.

=== TABLE 25 ===

Lock | Fields/examples

Character Lock | Face/reference IDs, hair, apparent age, body proportions, height, wardrobe, accessories, palette, voice reference.

Location Lock | Architecture, doors/windows, furniture, axis/orientation, lighting sources, palette, reference images.

Wardrobe Lock | Character, costume ID, scene range, continuity state, damage/dirt/blood state.

Prop Lock | Object appearance, scale, ownership, scene continuity.

=== TABLE 26 ===

SCENE 21 — EXT. قەڵای هەولێر — NIGHT /  / 21A             21B             21C             21D / [FRAME]         [FRAME]         [FRAME]         [FRAME] / EWS • 24mm      MS • 50mm       CU • 85mm       OTS • 50mm / 6 sec • Crane   8 sec • Dolly   4 sec • Static  7 sec • Handheld

=== TABLE 27 ===

SCRIPT → BREAKDOWN → SCENES / CAST / LOCATIONS / EQUIPMENT / CREW /       → SHOOTING SCHEDULE → RATE CARDS → BUDGET ENGINE → VERSIONED BUDGET

=== TABLE 28 ===

Group | Examples

1000 Development | Rights, writer, research, script editing, legal, development office.

2000 Above the Line | Producer, executive producer, director, writer, lead cast, rights.

3000 Production Crew | Production, AD, camera, lighting, grip, sound, art, costume, HMU, locations, transport, DIT.

4000 Equipment | Camera, lenses, lighting, grip, sound, DIT, generators, drone, specialty equipment.

5000 Locations & Art | Rental, permits, construction, dressing, props, security, cleaning.

6000 Cast & Extras | Cast fees, extras, stunt performers, rehearsals, fittings.

7000 Travel & Logistics | Flights, hotel, ground transport, per diem, catering.

8000 Post Production | Edit, VFX, grade, sound, ADR, Foley, music, subtitles, mastering, QC, deliverables.

9000 Other | Insurance, legal, contingency, administration, taxes/fees as configured.

=== TABLE 29 ===

{ /   "account_code": "3210", /   "department": "camera", /   "item": "Director of Photography", /   "quantity": 20, /   "unit": "shooting_day", /   "rate": "500.00", /   "currency": "USD", /   "tax_rate": "0.00", /   "fringe_rate": "0.00", /   "source": "rate_card", /   "notes": "" / }

=== TABLE 30 ===

subtotal = quantity × rate / tax      = subtotal × tax_rate / fringe   = subtotal × fringe_rate / total    = subtotal + tax + fringe /  / Budget totals are calculated on the backend and persisted/recomputed from canonical lines.

=== TABLE 31 ===

Field | Example

territory | Kurdistan Region / Iraq

currency | USD

department | camera

role_or_item | 1st AC

unit | day

rate | 150.00

effective_from | 2026-01-01

source | Art City approved card

approved_by | user UUID

=== TABLE 32 ===

{ /   "shooting_day": 7, /   "date": "2026-10-21", /   "scene_ids": ["21", "22", "24"], /   "primary_location_id": "LOC-004", /   "crew_call": "06:00", /   "camera_call": "07:00", /   "first_shot": "07:30", /   "estimated_wrap": "18:00", /   "status": "approved" / }

=== TABLE 33 ===

Section | Required data

Header | Company, production title, call sheet number, date, production day X of Y, revision/version.

Production Contacts | Producer, director, 1st AD, production manager, production office/emergency contact.

Day Schedule | Crew call, breakfast if used, first shot, lunch, estimated wrap.

Locations | Set/location name, address, map/GPS link, parking, basecamp, HMU, wardrobe.

Weather | Weather API data, sunrise/sunset, temperature, precipitation/wind; source/time shown.

Emergency | Medic, security, emergency procedure/contacts and nearest hospital when production provides/validates it.

Scene Schedule | Scene, synopsis, cast IDs, pages, D/N, INT/EXT, estimated time.

Cast Calls | Actor, character, pickup, HMU, wardrobe, rehearsal, on-set time.

Crew Calls | Department and individual call times/notes.

Equipment/Special | Equipment, props, vehicles, SFX/VFX, stunts, extras, special notes.

Distribution | Sent/delivered/opened/confirmed/declined/updated status.

=== TABLE 34 ===

SENT → DELIVERED → OPENED → CONFIRMED / OR: DECLINED / NEEDS RESPONSE /  / Any material revision → UPDATED / RECONFIRM REQUIRED

=== TABLE 35 ===

No AI weather / Weather must come from a real weather API/provider and include the data timestamp. Generative AI may summarize the forecast, but must not invent forecast values.

=== TABLE 36 ===

Change | Potential impact

Scene INT → EXT | Storyboard, lighting, equipment, location, schedule, budget, call sheet.

DAY → NIGHT | Lighting, crew hours, schedule, permits, budget, call sheet.

Cast added/removed | Casting, schedule, budget, call sheet, storyboard.

Location changed | Storyboard/background, transport, permits, schedule, budget, call sheet.

Shot adds crane/drone | Equipment, permits/safety review, budget, schedule, call sheet.

Shoot days 25 → 20 | Crew/equipment/logistics costs, pages/day, schedule risk, call sheets.

=== TABLE 37 ===

script.scene.updated / script.version.locked / breakdown.item.approved / storyboard.shot.updated / budget.version.locked / schedule.day.approved / callsheet.published / asset.reference.updated

=== TABLE 38 ===

PROJECT / ├── Overview / ├── DEVELOPMENT / │   ├── AC Script / │   ├── Characters / │   └── Locations / ├── PRE-PRODUCTION / │   ├── Script Breakdown / │   ├── AC Storyboard / │   ├── Découpage / Shot List / │   ├── Shooting Schedule / │   ├── AC Budget / │   └── AC Call / ├── CREATE / │   ├── Art City AI Studio / │   └── Art City AI Cinema / ├── POST / │   └── Art City AI Edit / └── PROJECT CONTROL /     ├── Assets /     ├── Documents /     ├── Team / Permissions /     ├── Activity / Approvals /     └── Settings

=== TABLE 39 ===

Role | Typical scope

Owner / Executive Producer | Full project, billing/plan where allowed, approvals, locks and exports.

Producer | Script/storyboard/budget/schedule/call-sheet control.

Director | Script, découpage, storyboard, shot list and schedule collaboration.

1st AD | Breakdown, schedule, call sheets and production-day operations.

Production Manager | Budget/logistics/schedule/call sheet.

Writer | Script creation/edit only unless additional permissions granted.

Cinematographer | Découpage, shot list, camera/lighting notes.

Art / Costume / HMU | Department breakdown items and references.

Accountant | Budget/rate cards/actuals according to permission.

Casting Manager | Cast/character/call availability according to permission.

Crew | Read assigned call sheet/project data only.

Viewer | Read-only.

Art City Administrator | Tenant/module permissions, policy, support and configured admin access.

=== TABLE 40 ===

Capability | Creator | Pro | Production

AC Script | Included | Included | Included

Script versions | Limited | Full | Full

AI Découpage | Credits | Included/credits | Higher allowance

AI Storyboards | Credits | Credits | Higher allowance

AC Budget | Basic | Full | Full + rate cards

Shooting Schedule | View/basic | Full | Full

AC Call | —/limited | Full | Full

Collaboration | Limited | Full | Full

Approval workflow | — | Limited | Full

Admin rate cards | — | — | Included/configurable

=== TABLE 41 ===

projects / project_members / project_settings /  / scripts / script_versions / script_elements / scenes / scene_revisions /  / characters / cast_members / character_cast_assignments / locations / breakdown_items /  / shots / storyboard_frames / visual_locks /  / production_schedules / shooting_days / shooting_day_scenes / availability_constraints /  / budgets / budget_versions / budget_lines / rate_cards / rate_card_items /  / call_sheets / call_sheet_versions / call_sheet_cast_calls / call_sheet_crew_calls / call_sheet_recipients /  / assets / asset_versions / asset_links /  / approvals / comments / audit_logs / ai_generations / domain_events

=== TABLE 42 ===

POST   /api/v1/projects / GET    /api/v1/projects/{project_id} / PATCH  /api/v1/projects/{project_id} /  / POST   /api/v1/projects/{id}/scripts / POST   /api/v1/scripts/{id}/generate / POST   /api/v1/scripts/{id}/rewrite / POST   /api/v1/scripts/{id}/translate / POST   /api/v1/scripts/{id}/versions / POST   /api/v1/script-versions/{id}/lock / POST   /api/v1/script-versions/{id}/breakdown / GET    /api/v1/script-versions/{id}/scenes / PATCH  /api/v1/scenes/{id} /  / POST   /api/v1/scenes/{id}/decoupage / POST   /api/v1/shots/{id}/storyboard / POST   /api/v1/storyboard-frames/{id}/regenerate / POST   /api/v1/storyboard-frames/{id}/approve /  / POST   /api/v1/projects/{id}/budgets / POST   /api/v1/budgets/{id}/generate-from-breakdown / POST   /api/v1/budgets/{id}/recalculate / POST   /api/v1/budgets/{id}/duplicate / POST   /api/v1/budget-versions/{id}/lock /  / POST   /api/v1/projects/{id}/schedules / POST   /api/v1/schedules/{id}/optimize / POST   /api/v1/shooting-days/{id}/approve /  / POST   /api/v1/shooting-days/{id}/call-sheet / POST   /api/v1/call-sheets/{id}/publish / POST   /api/v1/call-sheets/{id}/revise / POST   /api/v1/call-sheets/{id}/confirm /  / GET    /api/v1/projects/{id}/assets / GET    /api/v1/projects/{id}/audit-log / GET    /api/v1/projects/{id}/ai-usage

=== TABLE 43 ===

backend/app/ / ├── api/ / │   ├── projects.py / │   ├── scripts.py / │   ├── scenes.py / │   ├── breakdowns.py / │   ├── shots.py / │   ├── storyboards.py / │   ├── budgets.py / │   ├── schedules.py / │   ├── callsheets.py / │   └── assets.py / ├── models/ / ├── schemas/ / ├── repositories/ / ├── services/ / │   ├── ai/ / │   ├── script_service.py / │   ├── breakdown_service.py / │   ├── decoupage_service.py / │   ├── storyboard_service.py / │   ├── budget_service.py / │   ├── scheduler_service.py / │   ├── callsheet_service.py / │   ├── localization_service.py / │   └── export_service.py / ├── workers/ / │   ├── ai_worker.py / │   ├── storyboard_worker.py / │   └── document_worker.py / └── domain/ /     ├── events.py /     └── permissions.py

=== TABLE 44 ===

class AIProvider: /     async def generate_text(self, request): ... /     async def generate_structured(self, request, schema): ... /     async def generate_image(self, request): ... /  / # adapters can be changed without rewriting product logic / class ProviderA(AIProvider): ... / class ProviderB(AIProvider): ... / class LocalProvider(AIProvider): ...

=== TABLE 45 ===

{ /   "scene_id": "uuid", /   "cast": [], /   "extras": [], /   "props": [], /   "wardrobe": [], /   "makeup": [], /   "vehicles": [], /   "locations": [], /   "camera_requirements": [], /   "lighting_requirements": [], /   "sound_requirements": [], /   "sfx": [], /   "vfx": [], /   "stunts": [], /   "special_notes": [] / }

=== TABLE 46 ===

frontend/app/[locale]/projects/[projectId]/ / ├── overview/ / ├── script/ / ├── characters/ / ├── locations/ / ├── breakdown/ / ├── storyboard/ / ├── shots/ / ├── schedule/ / ├── budget/ / ├── callsheets/ / ├── studio/ / ├── cinema/ / ├── edit/ / ├── assets/ / ├── activity/ / └── settings/

=== TABLE 47 ===

Field | Reason

workspace_id / project_id | Tenant and project cost attribution.

user_id | Who initiated generation.

module / action | Script, breakdown, storyboard, etc.

provider / model | Operational traceability.

prompt_template_version | Reproducibility.

input hash / reference IDs | Trace source without duplicating sensitive text unnecessarily.

output object IDs | Link model result to persisted artifacts.

token/image usage | Cost calculation.

provider_cost | Internal economics.

latency_ms | Performance.

status / error | Reliability.

approved/rejected | Human-quality signal.

=== TABLE 48 ===

Phase | Deliverables | Why this order

1 — Shared Core | Project model extension, localization/RTL framework, permissions, asset links, versions, audit, AI job framework. | Everything else depends on this.

2 — AC Script | Screenplay editor, imports, AI assist, scene parser, script versions. | Creates canonical scenes/content.

3 — Breakdown Core | Breakdown extraction/editor, character/location registries. | Feeds all production modules.

4 — AC Storyboard | Découpage, shot DB, locks, storyboard generation and exports. | Uses scenes and references.

5 — AC Budget | Rate cards, budget grid, formulas, scenarios, exports. | Uses breakdown; improves once schedule exists.

6 — Schedule Core | Shooting days, constraints, scene assignment, approvals. | Required for reliable call sheets.

7 — AC Call | Call sheet template, weather, distribution, confirmation, revisions. | Depends on approved schedule.

8 — Deep Ecosystem Integration | Cinema/Studio/Edit handoff, production media tagging, advanced cross-module actions. | Turns suite into one operating system.

=== TABLE 49 ===

Architecture warning / The fastest-looking implementation — four pages, four prompts, four result boxes — will create a weak product. It duplicates data, prevents reliable budgeting/scheduling, breaks version control and makes Cinema/Studio/Edit integration expensive later.

=== TABLE 50 ===

IDEA /   ↓ / AC SCRIPT /   ↓ / SCENE BREAKDOWN /   ↓ / AC STORYBOARD + DÉCOUPAGE /   ↓ / AC BUDGET + SHOOTING SCHEDULE /   ↓ / AC CALL /   ↓ / ART CITY AI STUDIO / CINEMA /   ↓ / PRODUCTION /   ↓ / ART CITY AI EDIT /   ↓ / MASTER / DELIVER

=== TABLE 51 ===

from decimal import Decimal /  / def calculate_budget_line(quantity: Decimal, /                           rate: Decimal, /                           tax_rate: Decimal = Decimal("0"), /                           fringe_rate: Decimal = Decimal("0")): /     subtotal = quantity * rate /     tax = subtotal * tax_rate /     fringe = subtotal * fringe_rate /     return { /         "subtotal": subtotal, /         "tax": tax, /         "fringe": fringe, /         "total": subtotal + tax + fringe, /     }

=== TABLE 52 ===

@router.post("/scenes/{scene_id}/decoupage") / async def generate_decoupage(scene_id: UUID, request: DecoupageRequest, user=Depends(require_permission("storyboard.generate"))): /     scene = await scene_service.get(scene_id) /     result = await decoupage_service.generate(scene=scene, request=request) /     validated = DecoupageResult.model_validate(result) /     shots = await shot_service.create_versioned_shots(scene_id, validated.shots, user.id) /     return {"scene_id": str(scene_id), "shots": shots}

=== TABLE 53 ===

Service | Responsibility

ac-script-engine | Script generation, semantic editor support, versions, parser.

ac-breakdown-engine | Scene breakdown, production elements, dependency extraction.

ac-decoupage-engine | Shot planning and storyboard orchestration.

ac-budget-engine | Rate cards, deterministic calculations, scenarios and exports.

ac-production-engine | Schedule, shooting days and call sheets.

ac-asset-service | Shared asset/version/lineage links across Cinema, Studio, Edit and Pre-Production.

=== TABLE 54 ===

ARCHITECTURE RULE  Commission and architect the complete hub in one go, but implement and activate it as modular services behind feature flags. The platform must never require users to re-enter project data when they move from Script to Production, from Production to Edit, or from Edit to QC and Delivery.

=== TABLE 55 ===

Phase | Primary Art City AI modules | Canonical outputs

Development | Project Hub, AC Script, Character/World Bible, concept development | Approved development package, ScriptVersion, characters, locations

Pre-Production | Breakdown, Storyboard, Découpage, Shot List, Budget, Schedule, AC Call | Approved shooting plan, budget, schedule, call sheet

Production | Command Centre, Digital Slate, Shot/Take, Continuity, Camera/Sound Reports, Dailies, DPR | Captured production records and linked media

Post-Production | AC Edit, Review, VFX, Color, Sound, Music, ADR/Foley, Localization | Approved picture/sound versions and localized assets

Mastering & QC | Master Builder, technical QC, subtitle/audio QC, approval gates | Validated masters, QC reports

Delivery | Delivery Matrix, package builder, metadata/artwork, readiness control | Platform/broadcast/cinema/social delivery packages

=== TABLE 56 ===

Project /   ├── ScriptVersion → Scene → BreakdownItem /   ├── Character / Cast / Location / ProductionElement /   ├── Shot → StoryboardFrame → PlannedShot /   ├── ShootingDay → CallSheet /   ├── Take → CameraClip / AudioClip / ContinuityRecord /   ├── EditVersion → ReviewComment → Approval /   ├── VFXShot / ColorVersion / AudioMix / SubtitleTrack /   ├── Master → QCReport /   └── DeliveryPackage → DeliveryAttempt / Receipt

=== TABLE 57 ===

Widget | Required information | Source

Production day | Day X of Y, date, location, crew call, first shot, estimated wrap | Approved ShootingDay + CallSheet

Scene progress | Planned / in progress / completed / moved / dropped | Live production status

Page progress | Pages planned, pages completed, eighths remaining | Script + scene completion

Shot progress | Shots planned/completed/missing, pickups | Shot/Take tracker

Schedule variance | Ahead/behind in minutes and projected wrap | Actual timestamps vs schedule

Cost risk | Overtime exposure, unplanned resource use, forecast variance | Budget + actual production events

Cast status | Not called / travelling / HMU / wardrobe / on set / wrapped | Call + live status

Operational alerts | Weather, missing confirmations, media backup risk, safety/incident notices | Verified services + user records

=== TABLE 58 ===

PLANNED → CALLED → READY → SHOOTING → COMPLETE /                  ↘ HOLD / MOVED / PARTIAL / PICKUP REQUIRED

=== TABLE 59 ===

{ /   "take_id": "uuid", /   "project_id": "uuid", /   "shooting_day_id": "uuid", /   "scene_id": "uuid", /   "shot_id": "uuid", /   "take_number": 4, /   "slate": "21A-4", /   "camera": "A", /   "lens_mm": 50, /   "fps": 24, /   "timecode_in": "10:42:15:08", /   "timecode_out": "10:43:01:11", /   "status": "director_select", /   "sound_status": "good", /   "notes": "Best performance; slight focus drift at tail", /   "recorded_at": "timestamp" / }

=== TABLE 60 ===

DO NOT  Do not identify takes only from filenames. Filenames are useful, but the authoritative relationship must be a database link between Take and MediaAsset records.

=== TABLE 61 ===

Example alert | Evidence | Required user action

Wardrobe mismatch | Scene 43A reference: blue scarf; current take reference: no scarf | Confirm intentional change or mark continuity issue

Prop position mismatch | Glass was 30% full in previous matching angle | Confirm/reset/override

Dialogue deviation | Take 5 differs from locked line text | Accept as script change or keep as take note

=== TABLE 62 ===

CAMERA / SOUND MEDIA /     ↓ / REGISTER SOURCE MEDIA /     ↓ / CHECKSUM VERIFIED COPY /     ↓ / PRIMARY STORAGE + SECOND COPY STATUS /     ↓ / PROXY / TRANSCODE /     ↓ / SYNC SOUND /     ↓ / APPLY VIEWING LUT / BURN-IN /     ↓ / LINK SCENE / SHOT / TAKE METADATA /     ↓ / DAILIES REVIEW /     ↓ / AC EDIT

=== TABLE 63 ===

Group | Examples

Development | References, treatments, research, concept art

Pre-Production | Scripts, breakdown exports, boards, location/casting references, call sheets

Production | Camera originals, sound originals, proxies, stills, continuity photos, reports

Post | Edit exports, VFX plates/renders, color files, audio stems, subtitles, graphics

Mastering | Picture masters, audio masters, M&E, caption/subtitle masters

Delivery | DCP/IMF/ProRes/broadcast/OTT packages, metadata, artwork, receipts

=== TABLE 64 ===

MediaAsset / - asset_id / project_id / workspace_id / - asset_type / role / status / - original_filename / canonical_name / - object_key / storage_tier / - mime_type / size_bytes / checksum_sha256 / - language / locale / timecode / duration / technical_metadata / - scene_id / shot_id / take_id (nullable relationships) / - parent_asset_id / derivative_type / version / - rights_status / retention_state / - uploaded_by / created_at / verified_at

=== TABLE 65 ===

SORANI FILES  Unicode Kurdish filenames must be accepted, displayed and searched correctly. Object-storage keys may use internal UUIDs even when the user-facing filename is Kurdish.

=== TABLE 66 ===

Metric | Planned | Actual | Variance / status

Pages | 5 1/8 | 4 6/8 | -3/8

Scenes | 7 | 6 | 1 moved

Wrap | 19:00 | 19:47 | +47 min

Shots | 42 | 36 | 6 remaining/pickup

=== TABLE 67 ===

Status | Meaning

AVAILABLE | Ready to reserve

RESERVED | Allocated to a project/shooting day

CHECKED_OUT | Released to responsible user/unit

ON_SET | Confirmed active on shooting day

RETURNED | Checked back in

DAMAGED | Damage reported; use restricted

MAINTENANCE | Unavailable pending maintenance

=== TABLE 68 ===

DRAFT → IN_REVIEW → CHANGES_REQUESTED → IN_REVIEW → APPROVED → LOCKED /                     ↘ REJECTED | DRAFT → IN_REVIEW → CHANGES_REQUESTED → IN_REVIEW → APPROVED → LOCKED /                     ↘ REJECTED

IMMUTABILITY  A new uploaded/rendered version must never overwrite an approved review version. Approval is tied to the exact asset/version checksum or immutable asset version ID.

=== TABLE 69 ===

EditVersion / - edit_version_id / - project_id / - sequence_name / - version_number / - source_timeline_reference / - duration / frame_rate / aspect_ratio / - status: draft|review|approved|picture_locked / - parent_version_id / - exported_asset_id / - created_by / created_at / - approval_id

=== TABLE 70 ===

IDENTIFIED → BRIEFED → ASSIGNED → WIP → INTERNAL_REVIEW → CLIENT/DIRECTOR_REVIEW → APPROVED → FINAL_DELIVERED

=== TABLE 71 ===

PRINCIPLE  Art City AI should orchestrate and validate the color workflow; it should not claim color-science correctness from generative AI outputs alone.

=== TABLE 72 ===

Workstream | Tracked outputs

Dialogue | Production dialogue edit, cleanup, conform notes

ADR | Cue list, actor, language, recording status, selected takes

Foley | Cue list, categories, recording/edit status

SFX/Design | Cue/task, source, version, rights/usage notes

Music | Cue sheet, source/composer, versions, approval, rights status

Mix | Premix/final mix versions, channel layout, loudness target, approval

M&E | Music & Effects master versions and technical validation

=== TABLE 73 ===

AudioMaster / - layout: stereo | 5.1 | 7.1 | other supported layout / - channel_order: explicit ordered array / - sample_rate / bit_depth / codec / - integrated_loudness / true_peak when measured / - language / role: full_mix | m_and_e | dialogue | music | effects / - source_version / approved_by / qc_status

=== TABLE 74 ===

TRANSCRIPT → TRANSLATION → TIMED TEXT → LINGUISTIC REVIEW → TECHNICAL QC → APPROVED → MASTER/DELIVERY

=== TABLE 75 ===

ASSEMBLING → READY_FOR_QC → QC_FAILED / QC_PASSED → APPROVED_MASTER → ARCHIVED/SUPERSEDED

=== TABLE 76 ===

Severity | Meaning | Effect

BLOCKER | Objective rule failure that prevents package approval | QC_FAILED

ERROR | Material issue requiring correction/authorized override | QC_FAILED unless profile permits override

WARNING | Potential issue or heuristic finding | Human review required

INFO | Measured value / informational note | No automatic failure

=== TABLE 77 ===

QC SAFETY  Do not display a single “AI quality score” as a substitute for concrete checks. A summary score may be shown, but the pass/fail decision must expose the actual rules, measurements, overrides and reviewer.

=== TABLE 78 ===

Deliverable category | Examples | Readiness inputs

Picture | ProRes master, IMF component/package, DCP essence/package, broadcast file | Approved master + technical profile + QC

Audio | Stereo, 5.1, M&E, language dubs | Approved AudioMaster + QC

Timed text | SRT/VTT/TTML/other required subtitle/caption | Approved LocalizationTrack + QC

Artwork | Poster, thumbnail, hero, logo/title treatment | Approved Asset + dimensions/profile checks

Metadata | Title, synopsis, cast/crew, languages, ratings fields, credits | Validated MetadataSet

Documentation | Cue sheet, rights/release evidence where required, QC report | Approved document/status records

=== TABLE 79 ===

RightsRecord / - subject_type / subject_id / - right_type / - status: missing|pending|verified|restricted|expired / - territories[] / platforms[] / languages[] / - start_at / end_at / perpetual flag / - exclusivity / - document_asset_id / - verified_by / verified_at / - notes / restrictions

=== TABLE 80 ===

Category | Example readiness inputs

Script | Locked shooting script / unresolved revisions

Breakdown | Scenes parsed and production elements approved

Casting | Required roles confirmed and releases/status

Locations | Confirmed locations and permission status

Storyboard/Shot List | Coverage approved or intentionally waived

Budget | Approved budget/version

Schedule | Approved shooting days and conflicts resolved

Crew/Equipment | Critical departments/resources confirmed

Call Sheet | Latest shooting day published and confirmations tracked

Rights/Safety docs | Required production documents/status complete

=== TABLE 81 ===

Category | Example status

Picture | Picture lock approved

VFX | All required shots final/approved

Color | Final grade approved

Sound | Required mixes/M&E approved

Music/Rights | Cue sheet and rights statuses complete

Localization | Required language tracks approved

Mastering | Master candidate assembled

QC | Required profile checks passed/overrides approved

Artwork/Metadata | Required assets and fields approved

Delivery | Package/profile requirements complete

=== TABLE 82 ===

BLOCKERS FIRST  Always show BLOCKERS and unresolved mandatory requirements above the percentage. Example: “85% ready — BLOCKED: location permission missing for Scene 53.”

=== TABLE 83 ===

Action class | Examples | Policy

Read-only | Summarize status, find missing items, compare versions | May execute with normal read permission

Draft | Generate draft call sheet, draft budget scenario, suggested schedule | Creates DRAFT only; user reviews

State-changing | Publish call sheet, lock script, approve master, delete asset | Requires explicit user action and permission; no silent AI execution

High-impact/irreversible | Finalize delivery, revoke access, destructive deletion | Use explicit confirmation and full audit trail

=== TABLE 84 ===

Approval / - approval_id / project_id / - subject_type / subject_id / subject_version / - requested_by / requested_at / - required_role or required_user / - status: pending|approved|changes_requested|rejected|cancelled / - comment / decided_by / decided_at / - immutable subject checksum/version reference

=== TABLE 85 ===

Tier | Example | Typical access

Original camera/sound | High-resolution source | DIT, post supervisors, authorized editor/admin

Production proxy | Watermarked or clean proxy | Director, producer, editor, selected crew

Review proxy | Streaming derivative | Reviewers/clients based on share policy

Approved master | Final master asset | Restricted production/delivery roles

Delivery package | Client/platform package | Delivery-authorized users only

=== TABLE 86 ===

project_service / script_service / breakdown_service / storyboard_service / budget_service / scheduler_service / callsheet_service / production_service / slate_take_service / continuity_service / report_service / ingest_service / media_asset_service / review_service / edit_metadata_service / vfx_service / color_workflow_service / audio_post_service / localization_service / mastering_service / qc_service / delivery_service / rights_service / approval_service / notification_service / search_service / copilot_service / audit_service

=== TABLE 87 ===

Event | Example consumers

script.version_locked | breakdown, storyboard, schedule, dependency/stale service

shooting_day.updated | call sheet, production dashboard, notifications

take.recorded | dailies, edit metadata, production progress

media.ingest_verified | dailies, edit, backup/readiness

edit.picture_locked | VFX/color/sound/localization/mastering readiness

review.approved | workflow/status owners

qc.failed | mastering, delivery, notifications

delivery.rejected | delivery workflow, notifications, readiness

=== TABLE 88 ===

POST /api/v1/shooting-days/{id}/start / PATCH /api/v1/shooting-days/{id}/status / POST /api/v1/shots/{id}/takes / PATCH /api/v1/takes/{id} / POST /api/v1/takes/{id}/select / POST /api/v1/continuity/records / POST /api/v1/media/ingest-sessions / POST /api/v1/media/{id}/verify / POST /api/v1/dailies/{id}/publish / POST /api/v1/dpr/generate / POST /api/v1/reviews / POST /api/v1/reviews/{id}/comments / POST /api/v1/reviews/{id}/approve / POST /api/v1/vfx/shots / POST /api/v1/localization/tracks / POST /api/v1/masters / POST /api/v1/masters/{id}/qc / POST /api/v1/delivery-packages / POST /api/v1/delivery-packages/{id}/validate / POST /api/v1/delivery-packages/{id}/submit / GET  /api/v1/projects/{id}/readiness / POST /api/v1/projects/{id}/copilot/query

=== TABLE 89 ===

Area | Core entities/tables

Production | production_days, production_events, shot_takes, take_ratings, slate_records

Continuity | continuity_records, continuity_assets, script_deviations

Reports | camera_reports, sound_reports, department_reports, daily_production_reports

Media | media_assets, media_versions, media_derivatives, ingest_sessions, checksum_verifications, backup_statuses

Review | review_sessions, review_versions, review_comments, annotations, approvals

Post | edit_versions, vfx_shots, vfx_versions, color_versions, audio_assets, adr_cues, foley_cues, music_cues

Localization | transcripts, translations, timed_text_tracks, timed_text_cues, dub_cues

Master/QC | masters, master_components, qc_profiles, qc_runs, qc_findings, qc_overrides

Delivery | delivery_profiles, delivery_packages, delivery_components, delivery_attempts, delivery_receipts

Rights/Docs | rights_records, release_records, signed_documents

System | notifications, approval_requests, activity_events, domain_events

=== TABLE 90 ===

PROJECT OVERVIEW /  / DEVELOPMENT /   Script • Characters • Locations • References /  / PRE-PRODUCTION /   Breakdown • Storyboard • Découpage • Shot List • Budget • Schedule • Call Sheets • Readiness /  / PRODUCTION /   Live Dashboard • Slate/Takes • Continuity • Camera • Sound • Dailies • Media • DPR • Equipment /  / POST-PRODUCTION /   AC Edit • Review • VFX • Color • Sound • ADR/Foley • Music • Localization /  / MASTER & DELIVERY /   Mastering • QC • Artwork/Metadata • Delivery Matrix • Packages • Delivery History /  / CREATIVE AI /   Cinema • Studio /  / PROJECT CONTROL /   Assets • Rights • Documents • Team • Approvals • Activity • Settings

=== TABLE 91 ===

Role example | Typical scope

Executive Producer / Producer | Project-wide read; configured approval/lock/budget/delivery authority

Director | Script/storyboard/shot/take/review approvals; production visibility

1st AD | Schedule, call sheet, live production progress

Script Supervisor | Continuity, script deviations, take notes

DP / Camera | Shot metadata, camera reports, selected production visibility

Sound | Sound reports and sound media metadata

DIT / Data Manager | Ingest, verification, backup/media status

Editor | AC Edit, dailies/media, edit versions, review

VFX Supervisor/Artist | Scoped VFX tasks/versions/review

