# Art City Edit — Product Requirements Document v1.0

> Imported from Art_City_Edit_Developer_Product_Requirements_v1.0.docx (July 2026).
> Parent platform: Art City AI Studio. Confidential — internal use.

ART CITY EDIT

AI-supported editing and repurposing layer for Art City AI Studio

PRODUCT REQUIREMENTS DOCUMENT& TECHNICAL SPECIFICATION

Version 1.0  |  July 2026

Approved Product Direction

Build Art City Edit as the editing and repurposing layer of Art City AI Studio, not as an isolated clip generator. External users must request access, select a subscription, and receive explicit Art City approval before their workspace becomes active.

Prepared for: Art City Group development teamDocument classification: Confidential - Internal product and engineering use

Document Control

Field

Value

Product

Art City Edit

Parent platform

Art City AI Studio

Document type

Product Requirements Document (PRD) and Technical Specification

Version

1.0

Date

July 2026

Primary owner

Art City Group

Intended audience

Product, engineering, UX/UI, AI/ML, DevOps, security, QA, operations and commercial teams

Status

Approved direction - ready for discovery, architecture validation and MVP implementation

Confidentiality

Confidential - not for public distribution

Approval and Change Control

This document establishes the baseline scope for the first implementation. Any material change to the subscription model, Art City approval gate, data ownership, security, AI training policy, publishing workflow or MVP acceptance criteria requires written approval from the product owner.

Version

Date

Owner

Change Summary

Approval

1.0

July 2026

Art City Group

Initial consolidated product, technical and operational specification.

Pending signature

How Developers Should Use This Document

Review the product principles and non-negotiable rules before proposing architecture changes.

Validate assumptions through a short technical discovery phase and record any deviations.

Convert each numbered requirement and acceptance criterion into tracked engineering tickets.

Build the MVP around one primary job: transforming long-form spoken video into high-quality branded social clips.

Keep later-phase features behind feature flags; do not delay the MVP by implementing the entire long-term vision at once.

Contents

1. Executive Summary

2. Product Vision, Positioning and Principles

3. Business Objectives and Success Measures

4. Scope, Boundaries and Release Strategy

5. Users, Tenancy, Roles and Permissions

6. Registration, Subscription and Art City Approval

7. End-to-End User Experience

8. Functional Requirements

9. AI and Media Intelligence Requirements

10. Editing, Color, Audio, Caption and Format Engines

11. Trend Intelligence and Performance Learning

12. Brand Memory and Editorial Governance

13. Technical Architecture

14. Data Model and Storage Design

15. API and Event Requirements

16. Security, Privacy, Rights and Compliance

17. Quality Control, Reliability and Observability

18. UX/UI Requirements

19. Administration and Operations Console

20. MVP Delivery Plan and Roadmap

21. Acceptance Criteria and Test Scenarios

22. Risks, Constraints and Critical Decisions

23. Developer Handoff Checklist

Appendices

1. Executive Summary

Art City Edit is an AI-supported video editing and content repurposing product embedded inside Art City AI Studio. It will transform long-form recorded material - interviews, podcasts, television programmes, documentaries, events, music content and authorised archive footage - into strategically selected, professionally edited and brand-consistent social and broadcast-ready outputs.

The product must combine natural-language instructions with multimodal understanding of speech, visuals, speakers, emotion, pacing, scene structure, audio quality and brand rules. It will identify attractive moments, propose coherent clips, perform non-destructive editing, improve picture and sound, add captions, intelligently reframe for different aspect ratios, run quality control and deliver multiple versions from one approved edit.

Non-negotiable commercial rule

Self-registration does not automatically grant access. External users and organisations must request permission, select a proposed subscription, pass Art City review, and activate billing before they can process media. Art City retains the ability to approve, reject, suspend, limit or revoke access.

Primary Product Promise

Transform one long-form video into multiple high-quality, branded and platform-ready clips from a prompt, while preserving editorial meaning and keeping a human reviewer in control.

Strategic Differentiation

Editorial intelligence: The system explains why a moment was selected and protects context rather than only calculating a generic viral score.

Kurdish and regional-language capability: Specialised support for Sorani, Badini, Arabic, English and other relevant languages, including terminology dictionaries and right-to-left caption design.

Persistent brand memory: Each organisation can define logos, typography, colors, caption rules, transitions, music, tone, restrictions and approval policy.

Professional workflow: Candidate review, transcript editing, timeline control, version history, technical QC, permissions and approval states.

Performance loop: The platform learns which hooks, durations, topics, presenters and caption styles perform best for each authorised account.

Art City governance: Controlled onboarding, subscription approval, account limits, operational oversight and rights protection.

Critical Truth

Automatic clipping, captions, reframing and one-click editing are becoming commodity features. Art City Edit will only be defensible if it achieves superior editorial judgment, language intelligence, brand consistency, professional governance and measurable learning from published performance.

2. Product Vision, Positioning and Principles

2.1 Vision

Create the professional AI editing layer for Art City AI Studio: a controlled, multilingual and brand-aware environment where media organisations and creators convert recorded content into publishable assets faster without surrendering editorial accountability.

2.2 Recommended Positioning

Positioning statement

Art City Edit transforms long-form footage into strategically selected, professionally edited and brand-consistent content - guided by a prompt, approved by people and improved by real audience performance.

2.3 Product Family

Product

Primary Function

Relationship

Art City Studio

Create or manage individual AI-generated assets.

Source and companion capability.

Art City Cinema

Produce complete advertising campaign packages.

Campaign orchestration and deliverables.

Art City Edit

Edit, repurpose and distribute recorded footage.

Editing and repurposing layer; reuses identity, storage, publishing and analytics services.

2.4 Product Principles

Principle

Implementation Meaning

Human-controlled AI

AI proposes and executes reversible actions; users can inspect, revise and approve.

Non-destructive editing

Original masters remain unchanged. Every edit is stored as a versioned edit decision list or structured timeline.

Context before virality

The system must not create misleading combinations merely to improve engagement.

Brand consistency by default

Outputs inherit approved brand profiles, not random templates.

Permission before processing

Access, plan, workspace and processing rights are controlled by Art City.

Deterministic rendering

AI creates validated edit instructions; a controlled render engine performs media operations.

Privacy by design

Client media is not used for model training unless the client explicitly opts in under a separate agreement.

Professional extensibility

The MVP is narrow, but the architecture supports broadcast, archive, multi-camera and enterprise workflows later.

3. Business Objectives and Success Measures

3.1 Business Objectives

Create a subscription SaaS revenue line inside Art City AI Studio.

Reduce the time required to turn long-form footage into approved social assets.

Build proprietary editorial, language and brand intelligence rather than relying only on third-party model outputs.

Serve Art City Group brands first, then offer controlled access to selected external organisations.

Create an enterprise pathway for broadcasters, agencies, labels, archives and government media teams.

Generate structured data about clips, edits, performance and rights that can improve future tools across Art City AI Studio.

3.2 MVP Success Metrics

Metric

Initial Target

Measurement

Time to first candidate clips

Under 10 minutes for a 60-minute proxy under normal load.

Job telemetry from upload completion to candidate availability.

Editorial usefulness

At least 70% of generated projects contain one candidate accepted with minor edits.

Review outcome and edit distance.

Export reliability

At least 98% successful exports excluding invalid source files.

Render and QC job results.

Caption usability

At least 90% of projects require only correction-level, not full transcript replacement, in supported language conditions.

User correction rate.

Reframe quality

At least 90% of sampled exports keep the active subject and mandatory brand elements visible.

Human QA and automated safe-zone checks.

Activation governance

100% of external workspaces require Art City approval and active entitlement.

Audit log and authorization tests.

Rights attestation

100% of uploads require recorded rights confirmation.

Upload metadata and audit events.

System availability

99.5% monthly availability for the MVP control plane, excluding planned maintenance.

Monitoring and incident records.

3.3 Later-Stage Commercial Metrics

Monthly recurring revenue, annual recurring revenue and approved workspace conversion rate.

Gross margin per processing minute and per exported asset.

Free-trial or pilot conversion rate where Art City permits trials.

Retention by customer segment and language.

Average processed minutes, exports and active editors per workspace.

Performance uplift of AI-selected clips versus manually selected control clips.

4. Scope, Boundaries and Release Strategy

4.1 MVP Scope

The MVP shall focus on one controlled workflow: a user uploads a long-form spoken video, asks for specific social clips, reviews AI-selected candidates, edits them, applies a brand profile and exports multiple ratios.

Included in MVP

Deferred from MVP

Account request, Art City approval, plan entitlement and workspace activation.

Unrestricted public sign-up with immediate access.

Video upload, proxy generation and media inspection.

Live camera ingest and real-time switching.

Multilingual transcription, speaker identification and scene/silence analysis.

Full broadcast newsroom automation.

Prompt-based clip discovery and ranking.

Guaranteed viral prediction.

Transcript editing and controlled timeline editing.

Complete replacement for Premiere Pro or DaVinci Resolve.

Smart reframing for 9:16, 4:5, 1:1 and 16:9.

Advanced multi-camera synchronisation.

Captions, basic audio enhancement, basic color correction and shot matching.

High-end cinematic grading from scratch.

Brand profiles, versioning, review, export and technical QC.

Fully autonomous publishing without approval.

Usage tracking, subscription limits and administration console.

Open marketplace for third-party templates.

4.2 Source Content Types

Interviews and talk shows.

Podcasts and video podcasts.

Television programmes and recorded livestreams.

Documentary interviews and behind-the-scenes footage.

Music interviews, artist content and promotional material.

Events, conferences, educational and corporate videos.

Authorised archive material with recorded rights status.

4.3 Output Types

Vertical short video: 9:16.

Portrait feed: 4:5.

Square: 1:1.

Horizontal: 16:9.

Custom ratio and resolution in later plans.

Caption files: SRT and WebVTT; embedded captions as rendered graphics.

Project package with metadata, transcript, structured edit plan and QC report.

4.4 Explicit Product Boundaries

Do not overpromise

The product must not market itself as guaranteeing virality, replacing professional colorists, freely scraping every social platform, or obtaining rights to music and footage on behalf of users.

5. Users, Tenancy, Roles and Permissions

5.1 Multi-Tenant Model

The platform shall use organisation-based multi-tenancy. An organisation owns one or more workspaces, brand profiles, projects, media assets, entitlements and users. Data isolation must be enforced at the application and database authorization layers.

Entity

Description

Organisation

Commercial or legal customer entity.

Workspace

Operational area for a team, brand, client or department.

Brand Profile

Reusable visual, editorial, language and publishing rules.

User Membership

A user-role relationship scoped to an organisation or workspace.

Entitlement

Feature and usage allowance granted by an approved subscription.

Project

A non-destructive editing job linked to source media and versions.

5.2 Platform Roles

Role

Scope

Primary Powers

Art City Super Administrator

Entire platform

Full control, emergency suspension, plan and policy management, audit access.

Art City Approval Administrator

Entire platform

Review applications, approve/reject organisations and users, request documents, apply limits.

Art City Billing Administrator

Entire platform

Manage plans, invoices, credits, usage adjustments and billing exceptions.

Art City Support/Operations

Assigned accounts

Diagnose jobs, view operational metadata, impersonation only under controlled support procedure.

Organisation Owner

Organisation

Manage workspaces, billing contacts, memberships, security and approvals within plan limits.

Workspace Administrator

Workspace

Manage projects, users, brands and workspace settings.

Editor

Workspace

Upload, analyse, edit, render and export.

Reviewer/Approver

Workspace

Comment, compare, approve or reject versions; cannot change billing.

Viewer

Workspace

View approved content and reports; no editing.

External Collaborator

Specific projects

Time-limited, least-privilege access to assigned projects.

5.3 Permission Rules

Deny by default. Every protected action requires an explicit permission and active entitlement.

Organisation and workspace membership must be verified for every request, including background jobs.

An active subscription does not override suspension, rights complaints or security restrictions.

Project sharing outside an organisation must be disabled by default and time-limited when enabled.

Art City administrators must not view client media content unless required for support, rights review, security or contractual operations; such access must be logged.

Sensitive administrator actions require step-up authentication and auditable reasons.

5.4 Suggested Permission Matrix

Action

Owner

Admin

Editor

Reviewer

Viewer

External

Manage billing

Yes

No

No

No

No

No

Invite users

Yes

Yes

No

No

No

No

Upload media

Yes

Yes

Yes

No

No

Conditional

Create/edit project

Yes

Yes

Yes

No

No

Conditional

Approve version

Yes

Yes

Conditional

Yes

No

Conditional

Export/download

Yes

Yes

Yes

Conditional

Conditional

Conditional

Delete source media

Yes

Yes

Conditional

No

No

No

Manage brand profile

Yes

Yes

Conditional

No

No

No

6. Registration, Subscription and Art City Approval

6.1 Core Rule

External access is application-based. Registration creates an identity record, not a functioning production account. The user must verify identity, submit required organisation information, request a subscription, accept legal terms and receive Art City approval before workspace activation.

6.2 Recommended Onboarding Sequence

Create identity. User enters name, business email, password or approved single sign-on method.

Verify email. System sends time-limited verification link and prevents progression until confirmed.

Create or join organisation application. User provides organisation name, country, business type, website, intended usage, expected monthly minutes and billing contact.

Select requested plan. User chooses a proposed plan or requests enterprise pricing. Selection is provisional and creates no entitlement.

Accept declarations. User accepts Terms of Service, Privacy Notice, Acceptable Use Policy, rights warranty and no-unlawful-content declaration.

Submit access request. Application enters Art City review queue.

Art City review. Administrator may approve, reject, request clarification, request documents, assign a different plan, add limits or define a pilot period.

Billing activation. After approval, the user completes checkout or Art City applies an authorised invoice/contract arrangement.

Workspace activation. Only when approval and billing requirements are satisfied does the system issue entitlements and permit processing.

Ongoing control. Art City may suspend, downgrade, limit or revoke access for non-payment, abuse, rights claims, security issues or contractual reasons.

6.3 Account and Application States

State

Meaning

Allowed Actions

REGISTERED_UNVERIFIED

Identity created; email not verified.

Verify email, reset password.

PENDING_PROFILE

Email verified; application incomplete.

Complete profile and declarations.

PENDING_ART_CITY_REVIEW

Application submitted.

View status, respond to requests; no media processing.

MORE_INFORMATION_REQUIRED

Art City requested clarification or evidence.

Edit requested fields and resubmit.

APPROVED_PENDING_BILLING

Access approved; commercial activation incomplete.

Complete checkout or await invoice activation.

ACTIVE

Approval, billing and entitlements are valid.

Use granted platform features within limits.

SUSPENDED

Temporarily blocked by Art City or automated policy.

View notices; no processing or export unless explicitly allowed.

REJECTED

Application declined.

View decision; appeal only when Art City enables it.

PAST_DUE

Payment overdue within grace policy.

Restricted processing; billing correction.

CANCELLED

Subscription cancelled.

Read-only access during retention window, then archive/delete policy.

TERMINATED

Access ended for cause or contract conclusion.

No access except formal data export process if permitted.

6.4 Subscription Design

Plans should be configuration-driven rather than hard-coded. A plan defines feature flags, included processing minutes, storage, seats, brands, workspaces, export quality, concurrent jobs, retention and support level.

Entitlement Dimension

Examples

Processing

Monthly source minutes, analysis minutes, render minutes, transcription language tiers.

Capacity

Storage, active projects, retained versions, concurrent jobs.

Collaboration

Seats, workspaces, reviewers, external collaborators.

Output

Resolution, watermarks, custom ratios, batch exports, broadcast codecs.

Branding

Number of brand profiles, custom fonts, lower thirds and template governance.

AI

Clip ranking, advanced look matching, translation, trend intelligence, performance learning.

Administration

SSO, SCIM, audit export, custom retention, dedicated support.

Illustrative Plan Tiers - Final Prices to Be Set by Art City

Plan

Intended Customer

Indicative Limits

Creator

Approved individual creator or small team.

1 workspace, limited seats, monthly processing allowance, standard exports.

Professional

Production company, agency, label or media team.

Multiple users and brands, higher limits, advanced review and analytics.

Broadcast/Enterprise

Broadcaster, archive, government or large organisation.

Contracted limits, SSO, audit, dedicated support, custom storage and integrations.

Internal Art City

Art City Group brands and approved departments.

Internally assigned entitlements; may use cost-centre tracking instead of commercial billing.

6.5 Billing Rules

Do not capture payment before Art City approval unless the commercial team deliberately enables an application deposit; the default is no charge until approval.

Support recurring card billing, invoice/manual contract activation and promotional credits.

Usage must be metered independently from payment provider records.

Hard limits, soft limits and overage pricing must be configurable by plan and customer.

Every entitlement change must create an immutable audit event.

Cancellation must define effective date, data access window, export rights and deletion schedule.

6.6 Art City Approval Console Requirements

Queue of pending applications with risk and completeness indicators.

Applicant identity, organisation, country, website, use case, requested plan, expected volume and declarations.

Request-more-information workflow with templated messages.

Approve, reject, approve with conditions, assign pilot, add custom limits or escalate for commercial/legal review.

Decision reason required for rejection, suspension and termination.

Four-eyes approval option for high-risk or enterprise accounts.

Complete audit trail of reviewer, timestamps, evidence and state changes.

Security requirement

No frontend control is sufficient by itself. Every media-processing API, job worker and export endpoint must verify current account state and entitlement server-side.

7. End-to-End User Experience

7.1 Standard Project Flow

User signs in to an active approved workspace.

User creates a project and selects a brand profile.

User uploads or imports authorised source footage and confirms rights.

System validates format, computes checksum, creates proxy and extracts technical metadata.

System performs transcription, speaker detection, scene analysis, visual/audio quality analysis and semantic indexing.

User describes the desired clips through prompt plus structured controls.

Editorial Planner creates a structured brief and candidate-generation plan.

Clip Ranker produces candidate moments with scores and explanations.

User previews, rejects, adjusts or approves candidates.

Editing Engine creates non-destructive first-cut versions.

User edits transcript/timeline and requests prompt-based revisions.

Color, audio, caption and format engines process the approved sequence.

System generates ratio-specific previews and runs technical/editorial QC.

Reviewer approves final version according to workspace policy.

User exports a package or publishes through an authorised connector.

Where permitted, platform performance data is collected and associated with the source edit for learning and reporting.

7.2 Prompt Example

Find six strong clips from this 45-minute interview. Focus on surprising statements about the future of Kurdish music. Make each clip 25-50 seconds. Start with the strongest sentence, remove repetition and pauses, preserve the speaker's meaning, use a prestigious documentary style, add Sorani and English captions, keep skin tones natural, and deliver 9:16, 4:5, 1:1 and 16:9 versions.

7.3 Structured Prompt Controls

Control

Examples

Objective

Awareness, engagement, education, promotion, conversion.

Audience

Kurdish youth, parents, filmmakers, diaspora, professionals.

Platform

TikTok, Instagram Reels, YouTube Shorts, LinkedIn, broadcast.

Tone

Fast, emotional, serious, cinematic, humorous, prestigious.

Duration

15, 30, 45, 60, 90 seconds or custom range.

Language

Sorani, Badini, Arabic, English, Turkish, Persian.

Selection focus

Quotes, emotions, demonstrations, reactions, controversy, education.

Restrictions

Exclude politics, profanity, minors, logos, unverified claims or selected topics.

CTA

Follow, watch full programme, visit site, register, buy, donate.

Brand profile

Art City, Pêlistank TV, AC Music or client brand.

7.4 Revision Examples

Make the opening more provocative without changing the speaker’s meaning.

Remove the reference to the government.

Use fewer transitions and longer reaction shots.

Keep the complete answer; only remove silence and repetition.

Make it suitable for children and apply the Pêlistank profile.

Replace the music with a warmer approved track.

Create an alternative version for LinkedIn with slower pacing and burned-in English captions.

8. Functional Requirements

8.1 Identity, Access and Workspace

ID

Requirement

FR-001

Users can create an identity and verify email.

FR-002

External users must submit an access and subscription application.

FR-003

Art City administrators can approve, reject, request information, suspend and terminate.

FR-004

Access to media processing requires ACTIVE status and valid entitlement.

FR-005

Organisation owners can invite members only within approved seat limits.

FR-006

System supports organisation, workspace and project-level roles.

FR-007

All permission and state changes are audited.

8.2 Ingest and Media Management

ID

Requirement

FR-010

Support resumable multipart uploads and clear progress reporting.

FR-011

Validate file type, codec, duration, dimensions, frame rate, audio tracks and corruption indicators.

FR-012

Compute checksum and preserve immutable original master.

FR-013

Create proxy, thumbnail, waveform and preview assets.

FR-014

Require rights attestation and allow project-specific rights notes.

FR-015

Support configurable retention, archive and deletion policies.

FR-016

Prevent duplicate upload when checksum and workspace policy indicate the same asset already exists.

8.3 Analysis and Discovery

ID

Requirement

FR-020

Transcribe speech with word-level timing where supported.

FR-021

Identify and label speakers with manual correction.

FR-022

Detect scenes, shots, transitions, silence, filler words, repetition, faces, active speakers and selected visual objects.

FR-023

Create a searchable multimodal timeline.

FR-024

Convert user prompt and controls into a structured editorial brief.

FR-025

Return candidate clips with score, explanation, source timecodes and risk indicators.

FR-026

Allow users to pin, reject, compare and regenerate candidates.

8.4 Editing and Versioning

ID

Requirement

FR-030

Create non-destructive timelines referencing source time ranges.

FR-031

Support transcript-based removal and restoration.

FR-032

Support trim, split, reorder, delete, speed adjustment, crop, scale, position and basic transition controls.

FR-033

Support J-cuts, L-cuts, audio ducking, punch-ins and reaction shot insertion.

FR-034

Maintain immutable version history and named versions.

FR-035

Allow prompt-based revision against the current version, not only a full rebuild.

FR-036

Show when non-contiguous statements are joined.

8.5 Collaboration, Review and Approval

ID

Requirement

FR-040

Users can comment at project, version and timecode level.

FR-041

Workspace can require one or more approvals before export or publish.

FR-042

Approval records include person, role, timestamp, version and decision.

FR-043

A revised version invalidates prior approval when configured.

FR-044

External review links are disabled by default and require expiry, password or authenticated access.

8.6 Export and Publishing

ID

Requirement

FR-050

Export 9:16, 4:5, 1:1 and 16:9 from the same approved edit.

FR-051

Apply output presets for codec, resolution, frame rate, audio and captions.

FR-052

Generate QC report, checksums and manifest for delivery packages.

FR-053

Enforce plan resolution, watermark, branding and download restrictions.

FR-054

Publishing connectors require explicit account authorization and final user approval.

FR-055

Record destination, published asset identifier, caption text and publication time.

9. AI and Media Intelligence Requirements

9.1 Analysis Pipeline

The analysis pipeline must create a time-aligned representation of the entire source. Each detected element should retain source timecodes, confidence, model/provider version and provenance.

Signal

Required Outputs

Speech

Transcript, word timing, language, confidence, speaker, pauses, filler words, key phrases.

Semantics

Topics, questions, answers, claims, entities, sentiment, novelty and prompt relevance.

Visual

Shots, scenes, faces, active speaker, expressions, objects, text, logos, composition and quality.

Audio

Speech energy, music, applause, laughter, silence, noise, clipping and loudness.

Editorial

Hook candidates, setup, payoff, standalone clarity, context dependence, sensitive content risk.

Technical

Codec, frame rate, resolution, color properties, audio layout, corruption and sync indicators.

9.2 Candidate Clip Ranking

The first model may use a configurable weighted score. Weights must be stored by version so decisions can be reproduced and compared.

Signal

Initial Weight

Description

Hook strength

25%

Strength and immediacy of the opening.

Standalone clarity

20%

Whether the clip makes sense without excessive external context.

Emotional/intellectual impact

15%

Intensity, insight, humour, surprise or significance.

Visual quality

10%

Framing, focus, exposure, subject visibility and stability.

Novelty

10%

Unexpected claim, distinctive moment or original expression.

Prompt relevance

10%

Alignment with objective, topic, audience and restrictions.

Brand compatibility

5%

Fit with tone, policy and identity.

Trend compatibility

5%

Alignment with verified current patterns where data is available.

Penalty Signals

Missing context or deceptive meaning after removal from the source.

Poor audio, unstable picture, obstruction or unusable framing.

Repeated content, weak ending or excessive setup.

Sensitive content, minors, private information, rights risk or prohibited topics.

Unsupported factual claims where the workspace requires verification.

9.3 Explainability

Every candidate must include a concise explanation that is useful to an editor, not an opaque score. Example: “Selected because the speaker gives a complete, surprising claim within the first four seconds and closes with a clear takeaway.”

9.4 Model Governance

Record model name, provider, version, prompt template version, parameters and cost for each AI task.

Support provider abstraction so a model can be replaced without redesigning the product.

Use confidence thresholds and fallback workflows; do not silently invent transcript or visual details.

Permit manual correction of transcript, speaker, language, scene and detected object labels.

Keep customer data segregated; no cross-customer model learning from raw media without explicit contractual opt-in.

Run offline evaluation sets for Kurdish and regional-language accuracy before changing production models.

10. Editing, Color, Audio, Caption and Format Engines

10.1 Narrative Editing Engine

Place a strong hook before context when the meaning remains truthful.

Remove irrelevant introductions, false starts, long pauses and repetition.

Tighten questions while preserving the answer’s intent.

Create J-cuts and L-cuts and use reaction shots where source coverage permits.

Use punch-ins, cutaways or approved B-roll to conceal unavoidable jump cuts.

Align cuts with speech rhythm and music beats when selected.

Generate alternative openings and endings from the same source.

Display an edit-integrity warning when separate statements are combined.

10.2 Color Pipeline

Automatic Correction

Detect source color properties and normalise supported formats to a managed working color space.

Correct exposure, white balance, contrast, highlights, shadows and saturation within conservative thresholds.

Match adjacent camera angles and preserve natural skin tones.

Detect and optionally reduce flicker, noise and instability.

Show before/after preview and allow per-shot adjustment or reset.

Creative Grading

Apply an approved LUT, reference image, brand look or textual look description.

Provide intensity and skin-protection controls.

Store look version and parameters in the project.

Never apply random fashionable LUTs automatically without a selected profile or user approval.

10.3 Audio Engine

Analyse loudness, clipping, noise, hum, speech intelligibility and channel layout.

Apply dialogue enhancement, denoise, de-reverb and level normalisation with preview.

Perform music ducking and automatic fades.

Preserve original audio as a recoverable layer.

Flag suspected sync drift, missing channels or distorted audio.

Use only user-supplied, Art City-owned or properly licensed music and sound effects.

10.4 Caption Engine

Support Sorani, Badini, Arabic, English, Turkish, Persian and additional languages as validated.

Provide word-level timing where available, speaker labels and editable dictionaries.

Support Kurdish names, artist names, programme names and brand terminology.

Use meaning-aware line breaks and safe reading speed.

Support right-to-left layout, punctuation and mixed-language captions.

Export SRT, WebVTT and burned-in graphics.

Allow bilingual caption templates and independent language review.

10.5 Format Engine

Generate 9:16, 4:5, 1:1 and 16:9 compositions from one timeline.

Track active speakers and anticipate movement to avoid late reframing.

Preserve products, artworks, demonstrations, logos and other objects identified as mandatory.

Use split-screen when two speakers or visual elements are simultaneously important.

Avoid placing captions, CTAs and logos over faces or critical content.

Respect platform-safe zones and brand profile placement rules.

Allow independent manual composition overrides per ratio.

11. Trend Intelligence and Performance Learning

11.1 Definition

Trend intelligence means identifying recurring public content patterns and account-level performance signals that can inform editorial choices. It does not mean copying another creator or bypassing platform restrictions.

11.2 Permitted Signal Sources

Authorised account analytics and publication data.

Official public discovery APIs where available and contractually permitted.

User-supplied reference links, videos, screenshots or examples.

Licensed social-listening providers and commercial datasets.

Art City’s own aggregate, privacy-protected performance history.

Manual editorial observations added by approved Art City analysts.

11.3 Trend Outputs

Common hook structures.

Typical duration ranges by topic and platform.

Caption density and first-frame text patterns.

Pacing, cut frequency and visual composition trends.

Topic velocity and recurring questions.

Music or audio pattern references only when rights and platform rules allow use.

11.4 Performance Loop

Record publication and destination metadata.

Ingest authorised views, watch time, completion, retention, engagement and conversion signals.

Associate metrics with source moment, hook, duration, caption style, brand and edit decisions.

Normalise for audience size, spend, platform and publication timing before comparison.

Generate recommendations for the same customer without exposing another customer’s confidential performance.

Require human review before changing default editorial strategies.

Analytical caution

High performance does not prove causation. The product should present correlations and confidence, not claim that a single edit choice caused success.

12. Brand Memory and Editorial Governance

12.1 Brand Editing Profile

Each approved organisation can maintain one or more versioned brand profiles. A project links to a specific profile version so old exports remain reproducible after later brand changes.

Category

Profile Fields

Identity

Brand name, logos, colors, fonts, iconography and safe areas.

Video

Intro, outro, end card, lower thirds, transitions, overlays and preferred framing.

Captions

Fonts, size, position, animation, highlight style, language and line-breaking rules.

Audio

Approved music, sonic logo, loudness targets, voice treatment and prohibited tracks.

Editorial

Tone, pacing, audience, preferred duration, CTA rules and sensitive topics.

Language

Dictionary, spelling policy, proper names, translations and banned words.

Compliance

Disclaimers, children’s rules, legal text, rights notices and approval requirements.

Publishing

Platform presets, titles, descriptions, hashtags, account destinations and scheduling rules.

12.2 Example Profiles

Profile

Expected Behaviour

Pêlistank TV

Child-safe content, bright but controlled visuals, simplified captions, restricted topics, parental and platform compliance.

AC Music

Artist-focused visuals, music metadata, release CTA, rights-aware audio, catalogue terminology.

Art City Corporate

Prestigious pacing, restrained transitions, corporate typography, bilingual output and formal approval.

External Client

Customer-specific brand and editorial rules within Art City’s platform policies.

12.3 Governance

Only authorised roles can publish a brand profile version.

Draft changes can be tested in a sandbox project before becoming default.

Profile changes require audit history and rollback.

Workspace administrators can require brand compliance before export.

Art City can define platform-level prohibited rules that customer profiles cannot override.

13. Technical Architecture

13.1 Architecture Direction

Art City Edit should reuse the existing Art City AI Studio platform stack where practical: FastAPI backend, PostgreSQL, Redis, MinIO-compatible object storage and Next.js frontend. Heavy media and AI workloads should run as asynchronous jobs isolated from the web API.

Client / Next.js Web Application        |API Gateway / FastAPI Control Plane        |---------------- Identity, Approval, Billing, Entitlements        |---------------- Organisations, Workspaces, Projects, Brands        |---------------- Review, Export, Publish, Analytics        |Event / Job Orchestration Layer        |+----------------+----------------+----------------+----------------+| Ingest Workers | AI Analysis    | Render Workers | QC Workers     || Proxy/Probe    | Speech/Vision  | FFmpeg/Media   | Technical/Edit |+----------------+----------------+----------------+----------------+        |PostgreSQL + Redis + Object Storage + Search/Vector Index        |Approved External AI, Billing, Storage and Publishing Providers

13.2 Service Responsibilities

Service

Responsibilities

Identity and Access

Authentication, MFA, sessions, organisation membership, roles and permission checks.

Approval Service

Applications, review queue, decisions, conditions, suspension and audit.

Billing and Entitlements

Plans, subscriptions, invoices, usage, limits and feature flags.

Ingest Service

Uploads, checksums, inspection, proxy, thumbnails, waveform and metadata.

Media Intelligence

Speech, speakers, scenes, faces, objects, semantic and quality analysis.

Editorial Planner

Prompt parsing, structured brief, selection strategy and revision instructions.

Clip Ranker

Candidate generation, scoring, explanation and integrity risk.

Timeline Service

Structured non-destructive edits, versions, comments and approvals.

Render Service

Validated edit compilation, transcode, resize, captions, audio, transitions and packaging.

Look Engine

Correction, shot matching, grade application and preview.

QC Service

Technical and editorial checks, reports and pass/fail policy.

Publish Service

Authorised destination connections, publishing and publication records.

Analytics Service

Usage, performance ingestion, reporting and recommendation features.

13.3 Deployment Requirements

Containerised services with separate CPU and GPU worker pools.

Autoscaling based on queue depth, processing time and GPU/CPU capacity.

Job idempotency and safe retry for upload, analysis, render and QC operations.

Signed object-storage URLs with short expiry and least privilege.

Environment separation: local, development, staging and production.

Feature flags for incomplete engines and customer-specific pilots.

No customer media in application logs, error traces or analytics payloads.

13.4 Structured Edit Plan

Language models must not directly emit unrestricted shell commands. They should produce a validated, versioned edit schema that the render compiler converts into approved media operations.

{  "schema_version": "1.0",  "project_id": "prj_...",  "source_asset_id": "ast_...",  "output_duration_seconds": 42.5,  "segments": [    {      "source_in": 814.2,      "source_out": 822.8,      "role": "hook",      "speed": 1.0,      "integrity_note": null    }  ],  "format_profile": "social_vertical_1080x1920",  "caption_profile_version": "bpv_...",  "color_profile_version": "look_...",  "audio_profile_version": "aud_..."}

13.5 Build-versus-Buy Boundary

Build as Art City IP

Use Replaceable Providers

Editorial prompt model, clip scoring logic and explanations.

Base speech-to-text models.

Kurdish dictionaries and language corrections.

Generic vision, face or object models.

Brand memory and policy engine.

Payment processing.

Structured edit schema and deterministic compiler.

Email/SMS delivery.

Performance data model and customer-specific learning.

Cloud GPU infrastructure where economical.

Approval, entitlement and professional workflow.

Publishing APIs and external social intelligence.

14. Data Model and Storage Design

14.1 Core Entities

Entity

Selected Fields

User

id, email, name, auth status, MFA status, locale, created_at.

Organisation

id, legal/display name, country, type, status, owner, risk level.

AccessApplication

organisation, applicant, requested plan, use case, documents, state, reviewer, decision.

Subscription

organisation, plan, billing method, status, period, cancellation and provider references.

Entitlement

organisation/workspace, feature, limit, used, reset rule, effective dates.

Workspace

organisation, name, status, default brand, retention policy.

Membership

user, organisation/workspace, role, status, invitation and expiry.

BrandProfile

workspace, name, status, owner.

BrandProfileVersion

assets, rules, language, captions, color, audio, compliance, version.

MediaAsset

workspace, owner, checksum, storage, technical metadata, rights status, retention.

Project

workspace, title, objective, status, brand profile version, source assets.

AnalysisJob

asset, type, provider/model, state, cost, timestamps, outputs.

TimelineVersion

project, parent version, structured edit plan, creator, status.

CandidateClip

project, timecodes, score, explanation, risks, user decision.

RenderJob

timeline version, preset, state, output, cost, QC status.

Approval

version, approver, role, decision, timestamp and comments.

Publication

version, destination, external id, time, metadata and analytics permission.

UsageRecord

organisation, job, metric, quantity, cost and billing period.

AuditEvent

actor, action, entity, before/after summary, reason, IP/device and timestamp.

14.2 Storage Classes

Class

Examples

Policy

Original master

Uploaded camera or programme file.

Immutable, encrypted, highest protection; lifecycle by contract.

Working proxy

Low-resolution edit and analysis file.

Regenerable; shorter retention permitted.

Derived analysis

Transcript, shots, embeddings, waveforms and thumbnails.

Versioned with model provenance.

Project data

Timelines, comments, approvals and brand references.

Transactional database plus immutable history.

Rendered output

Final ratios, caption files, manifests and QC reports.

Retention by plan and project policy.

Audit/security

Access and administrative events.

Restricted, append-only or tamper-evident retention.

14.3 Search and Timeline Index

Index transcript terms, topics, entities, speakers, scenes, objects and time ranges.

Store embeddings with tenant-aware access control and model/version metadata.

Search results must resolve to exact source timecodes.

Deleting a source asset must trigger policy-defined deletion or invalidation of dependent indexes.

15. API and Event Requirements

15.1 API Principles

Versioned REST or equivalent stable APIs under the existing Art City AI Studio gateway.

Server-side tenant and entitlement checks on every protected route.

Idempotency keys for create, upload completion, render and publishing operations.

Cursor pagination for large lists and time-based filters for operational views.

Consistent error codes with safe user messages and internal correlation IDs.

OpenAPI documentation and generated client types where practical.

15.2 Suggested Endpoint Groups

Group

Representative Endpoints

Applications

POST /access-applications; GET /access-applications/{id}; POST /review; POST /request-info.

Subscriptions

GET /plans; POST /checkout-session; GET /subscription; POST /cancel.

Organisations

GET/POST /organisations; memberships; invitations; security settings.

Workspaces

GET/POST /workspaces; brand profiles; retention and approval policy.

Assets

Create upload, upload parts, complete upload, metadata, rights and deletion.

Projects

Create, update, list, archive, source assignment and prompt brief.

Analysis

Start analysis, job status, transcript, scenes, speakers and candidate clips.

Timelines

Versions, edits, restore, compare and prompt revision.

Renders

Create job, status, preview, outputs, manifest and QC.

Reviews

Comments, approvals, rejection and history.

Publishing

Connections, destinations, publish request, result and analytics consent.

Admin

Applications, users, accounts, entitlements, usage, jobs, incidents and audit.

15.3 Domain Events

Event

Consumers

access_application.submitted

Approval queue, notification and risk checks.

access_application.approved

Billing activation, organisation provisioning and notification.

subscription.activated

Entitlement service and workspace provisioning.

asset.uploaded

Media inspection and proxy generation.

asset.analysis_completed

Candidate generation and user notification.

timeline.version_created

Preview render, review and audit.

render.completed

QC, usage metering and notification.

qc.failed

User alert, support diagnostics and retry policy.

version.approved

Export/publish unlock and audit.

publication.completed

Analytics tracking and performance loop.

subscription.suspended

Immediate entitlement revocation and job cancellation policy.

15.4 Webhooks and External Integrations

Verify signatures, timestamps and replay protection.

Store provider event identifiers and process idempotently.

Do not trust payment-provider status alone; reconcile against internal subscription state.

Publishing and analytics integrations must be scoped to the customer account and revocable.

16. Security, Privacy, Rights and Compliance

16.1 Security Baseline

Encryption in transit and at rest for databases, object storage, backups and secrets.

MFA required for Art City administrators; available or required by plan for customers.

Short-lived access tokens, secure session management and device/session revocation.

Role-based access control combined with tenant and entitlement enforcement.

Secrets in a managed secret store; never in source code or client applications.

Malware scanning and file validation before processing.

Rate limiting, abuse detection and quota enforcement.

Dependency, container and infrastructure vulnerability scanning.

Backups, restoration tests and documented disaster recovery targets.

16.2 Media Rights

Every upload requires a rights declaration stating that the user owns or is authorised to process the material.

Store rights status, territory, term, restrictions, music status, talent releases and notes where supplied.

Provide a rights complaint and takedown procedure.

Allow Art City to suspend processing or export when a credible rights dispute exists.

Do not imply that the platform’s technical ability to edit or publish creates a legal right to do so.

16.3 Privacy and AI Training

Default data rule

Customer media, transcripts, prompts and outputs must not be used to train general models or another customer’s models by default. Any opt-in must be explicit, separate, revocable where feasible and contractually documented.

Data minimisation: collect only information required for onboarding, processing, billing, safety and support.

Clear retention and deletion periods by plan and contract.

Export and deletion workflows for organisation data, subject to legal retention obligations.

Provider contracts should prevent unauthorised model training and define retention of submitted media.

Sensitive administrator access must require a support or policy reason and produce an audit event.

16.4 Children and Sensitive Content

Support child-safe brand profiles and stricter review rules for Pêlistank and similar customers.

Detect potential minors and apply configured restrictions, while recognising that automated age estimation is imperfect.

Flag profanity, sexual content, violence, private information and other configured categories.

Do not rely solely on automated safety classification for high-risk publishing decisions.

16.5 Audit Requirements

Log authentication, access decisions, application review, subscription changes, uploads, deletions, exports, publishing and administrator actions.

Audit records must include actor, action, target, timestamp, result, reason and correlation ID.

High-risk audit records should be tamper-evident and retained according to contract and legal policy.

17. Quality Control, Reliability and Observability

17.1 Automated QC Checks

Category

Checks

Video technical

Duration, dimensions, frame rate, codec, black/frozen frames, corruption, safe-area and crop.

Audio technical

Clipping, silence, channel layout, loudness, dialogue level, sync and missing tracks.

Captions

Timing, overflow, reading speed, safe area, encoding, spelling alerts and language direction.

Color

Extreme exposure, abrupt shot mismatch, skin-tone deviation and unsupported HDR/SDR handling.

Editorial

Missing context, duplicate segments, abrupt sentence cuts, unsupported joins and restricted topics.

Brand

Logo, font, CTA, intro/outro, disclaimer and profile compliance.

Package

File naming, manifest, checksum, required outputs and delivery completeness.

17.2 QC Result Model

Technical status: PASS, PASS_WITH_WARNING or FAIL.

Editorial confidence: numeric score with specific explanations.

Brand compliance: compliant, warning or blocked.

Every failed check identifies timecode, output, severity and recommended correction.

Configured critical failures prevent export or publishing until resolved or formally overridden by an authorised role.

17.3 Reliability

Durable job queue with retry, timeout, cancellation and dead-letter handling.

Worker heartbeat and orphaned-job recovery.

Resumable upload and render-stage checkpoints where economical.

Graceful degradation when an external AI provider is unavailable.

User-visible job state and actionable error messages.

Resource and cost limits per job to prevent accidental runaway processing.

17.4 Observability

Metrics: queue depth, processing duration, job success, GPU/CPU utilisation, provider latency, cost and usage.

Distributed tracing with correlation IDs across API, worker and provider calls.

Structured logs that exclude raw media, transcript content and secrets.

Alerting for failed pipelines, entitlement bypass attempts, storage pressure, billing mismatch and provider outages.

Operational dashboard with customer-impact and system-health views.

18. UX/UI Requirements

18.1 Primary Navigation

Home / Dashboard.

Projects.

Media Library.

Brand Profiles.

Publishing and Performance.

Team and Permissions.

Subscription and Usage.

Help and Support.

18.2 Project Workspace Layout

Area

Function

Video Viewer

Playback, safe zones, ratio switcher, before/after and timecode.

Transcript Panel

Search, speakers, word editing, selection and restore.

Timeline

Segments, video/audio/caption tracks, trim, reorder, transitions and key controls.

Candidate Panel

AI candidates, scores, explanations, risk flags and comparison.

Prompt Panel

Initial brief and revision conversation with structured controls.

Inspector

Crop, position, audio, color, captions, brand and segment settings.

Review Panel

Comments, approvals, change history and assigned reviewers.

QC Panel

Technical, editorial and brand checks with jump-to-issue.

18.3 Operating Modes

Mode

Behaviour

Auto Mode

Produces complete candidate versions with minimum configuration.

Guided Mode

AI proposes; user approves selection, style and important edit decisions.

Professional Mode

Full timeline, detailed audio/color controls and per-ratio overrides.

18.4 Required States

Empty, uploading, validating, analysing, candidates ready, editing, rendering, QC, review, approved, published, failed, suspended and archived.

Application and subscription state must be visible without confusing “account created” with “access approved.”

Every long-running state must show progress, last update and safe next action.

18.5 Accessibility and Localisation

Keyboard-accessible major controls and visible focus states.

Screen-reader labels and semantic structure for core workflows.

High-contrast mode and caption preview accessibility.

Right-to-left interface readiness for Kurdish/Arabic localisation where selected.

Date, number and time-zone localisation; default operational time zone may be organisation-specific.

19. Administration and Operations Console

19.1 Console Modules

Module

Capabilities

Approval Queue

Review applications, evidence, risk, decisions and communication.

Customer Accounts

Status, plans, users, workspaces, limits, incidents and notes.

Plans and Entitlements

Feature flags, quotas, trials, overages and custom contracts.

Billing Operations

Invoices, credits, payment status, reconciliation and exceptions.

Job Operations

Search, inspect, retry, cancel and diagnose analysis/render jobs.

Provider Operations

Health, costs, latency, model versions and routing.

Rights and Safety

Complaints, takedowns, holds, restricted projects and evidence.

Audit and Security

Administrative events, suspicious access, session revocation and exports.

Content/Template Governance

Global profiles, prohibited rules, feature releases and announcements.

Support

Customer tickets, support access requests and resolution notes.

19.2 Support Access

Support impersonation is disabled by default and should require explicit temporary grant or documented emergency policy.

Content access requires a reason, limited duration and audit record.

Where possible, diagnostic metadata should be sufficient without opening customer media.

19.3 Operational Controls

Global maintenance mode and provider-specific circuit breakers.

Suspend organisation, workspace, user, integration, project or individual job.

Apply temporary credits, limits or pilot features with expiry.

Feature flag rollouts by environment, organisation or percentage.

20. MVP Delivery Plan and Roadmap

20.1 Phase 0 - Discovery and Foundation

Confirm target customer segments and first internal pilot content.

Validate current Art City AI Studio architecture, identity, storage, job and deployment capabilities.

Define the structured edit schema and provider abstraction interfaces.

Prototype transcription and clip selection using a representative Kurdish/English evaluation set.

Confirm billing provider, approval policy and rights/legal documents.

Define media cost model and plan limits before public pricing.

20.2 Phase 1 - Controlled Internal MVP

Art City internal user provisioning.

Upload, proxy, transcription, scenes and searchable timeline.

Prompt brief, candidate ranking and explanation.

Transcript editing, first-cut timeline and versioning.

Captions, basic audio, basic color and 9:16/16:9 export.

Technical QC and internal operational dashboard.

20.3 Phase 2 - Approved External Pilot

External registration, access application and Art City review console.

Subscription, billing, entitlements and plan limits.

Organisation/workspace membership and collaboration.

4:5 and 1:1 export, brand profiles, review and approval.

Customer audit, rights declarations and support workflow.

20.4 Phase 3 - Professional Product

Advanced timeline and look/audio controls.

Publishing connectors, analytics and performance loop.

Custom enterprise retention, SSO, audit export and integrations.

Broader language and broadcast format support.

20.5 Phase 4 - Advanced Media Operations

Multi-camera editing and programme workflows.

Archive-scale semantic search and automated repurposing queues.

Live/near-live clipping.

Licensed B-roll and music marketplaces or integrations.

Customer-specific models and advanced trend intelligence under separate governance.

20.6 Suggested Engineering Workstreams

Workstream

Primary Deliverables

Platform/Identity

Approval, roles, tenancy, plans, entitlements and audit.

Media Pipeline

Upload, proxy, probe, storage, lifecycle and render.

AI/ML

Transcription, scenes, semantic timeline, candidates and evaluation.

Editor Frontend

Viewer, transcript, timeline, candidates, inspector and versions.

Brand/Caption/Format

Profiles, captions, color/audio basics and multi-ratio composition.

Review/Publish

Comments, approvals, exports, connectors and analytics.

DevOps/Security

Workers, scaling, monitoring, secrets, backups and incident readiness.

QA

Media fixtures, evaluation sets, automated tests, QC and regression.

21. Acceptance Criteria and Test Scenarios

21.1 Access and Subscription

AC ID

Acceptance Criterion

AC-001

A newly registered external user cannot create a production workspace or upload media before email verification, Art City approval and active entitlement.

AC-002

An Art City administrator can request more information, approve, reject and suspend an application with a reason and audit record.

AC-003

Approval alone does not activate processing when billing is required and incomplete.

AC-004

Suspending an organisation prevents new processing and export across API and worker layers within the defined revocation window.

AC-005

Plan limits are enforced server-side and usage is recorded for each billable job.

21.2 Media and Analysis

AC ID

Acceptance Criterion

AC-010

A valid supported video uploads resumably, receives checksum, proxy, thumbnail and technical metadata.

AC-011

The original file remains unchanged after all edits and exports.

AC-012

A 60-minute test interview produces transcript, speakers, scenes and candidate clips with source timecodes.

AC-013

Candidate explanations identify hook, relevance and at least one relevant risk or limitation when present.

AC-014

Manual correction of transcript or speaker label is preserved in later versions.

21.3 Editing and Output

AC ID

Acceptance Criterion

AC-020

The user can remove text from the transcript and the timeline updates without modifying the source master.

AC-021

The system can generate 9:16, 4:5, 1:1 and 16:9 versions from one approved edit.

AC-022

A reviewer can reject a version with timecoded comments and approve a later version.

AC-023

Critical QC failures block export until fixed or overridden by an authorised role with reason.

AC-024

Export package includes requested media files, captions where selected, manifest, checksum and QC report.

21.4 Security and Isolation

AC ID

Acceptance Criterion

AC-030

A user from Organisation A cannot read, search, download or reference Organisation B data by changing identifiers.

AC-031

Expired signed media URLs no longer grant access.

AC-032

Administrator content access creates an audit record with reason and timestamp.

AC-033

Logs and error reports do not contain raw transcript or media content.

AC-034

Deletion or retention jobs remove or archive data according to policy and record the outcome.

21.5 Minimum Test Media Set

Single-speaker Sorani interview.

Two-speaker Kurdish/English interview.

Arabic right-to-left caption example.

Low-light, noisy and unstable footage.

Multi-camera programme excerpt with reaction shots.

Vertical source with product demonstration.

Video with music, applause and audience laughter.

Corrupt, unsupported and extremely large files for failure handling.

22. Risks, Constraints and Critical Decisions

Risk

Why It Matters

Mitigation

Commodity competition

Basic clipping and captions are widely available.

Focus IP on editorial quality, language, brand governance, approval and performance learning.

Misleading edits

Combining statements can damage trust and create legal risk.

Integrity warnings, context scoring, source comparison and reviewer approval.

Kurdish model accuracy

Generic speech models may perform poorly on dialects and names.

Build evaluation datasets, dictionaries, corrections and provider comparison.

Media processing cost

GPU, transcription and render costs can exceed subscription revenue.

Meter every job, price by real cost, quotas, caching, proxies and efficient routing.

Platform API limits

Trend and publishing capabilities can change or be restricted.

Use authorised APIs, provider abstraction and avoid dependence on scraping.

Rights violations

Users may upload material they do not own.

Rights declaration, audit, takedown, holds and account governance.

Scope expansion

Attempting a full NLE will delay launch.

Protect the narrow MVP and phase advanced editing.

Model/provider lock-in

Pricing, quality and availability may change.

Provider interfaces, provenance and evaluation harness.

Tenant leakage

A severe security and trust failure.

Defence-in-depth authorization, automated isolation tests and audit.

Approval bottleneck

Manual review can slow customer conversion.

Risk tiers, clear SLA, complete applications and automation that supports - not replaces - Art City decisions.

22.1 Decisions Required Before Development Freeze

Final MVP-supported input codecs, maximum duration and file size.

Initial languages and required accuracy thresholds.

Billing provider, currencies, tax/invoice handling and whether trials exist.

Exact plan limits and overage policy.

Default retention periods for originals, proxies, analysis and outputs.

Cloud region and third-party AI providers permitted for customer media.

Who can approve external accounts and the review service level.

Whether initial publishing connectors are included in MVP or Phase 3.

Legal documents: Terms, Privacy, Acceptable Use, Data Processing and rights/takedown policy.

22.2 Product Decisions Already Approved

Art City Edit is part of Art City AI Studio.

It is an editing and repurposing layer, not an isolated clip generator.

External users subscribe through an application and require Art City permission.

The MVP focuses on long-form spoken video to branded multi-ratio social clips.

Human review and non-destructive editing are fundamental.

23. Developer Handoff Checklist

23.1 Product and UX

Translate all FR and AC items into traceable tickets.

Produce user flows for application, approval, billing, upload, analysis, editing, review and export.

Create clickable prototypes for dashboard, project workspace and admin approval console.

Validate Sorani/Arabic right-to-left caption and interface behaviour early.

23.2 Architecture

Document the current Art City AI Studio services to be reused.

Approve the structured edit schema and rendering compiler boundary.

Define queues, worker pools, storage buckets, lifecycle and retry strategy.

Define tenancy enforcement and permission middleware before feature development.

Create provider interfaces for speech, vision, language, billing and publishing.

23.3 Security and Legal

Threat-model upload, media URLs, tenant isolation, administrator access and publishing connectors.

Implement rights attestation and audit before external pilot.

Confirm provider data retention and training terms.

Implement account suspension and entitlement revocation as an early integration test.

23.4 AI/ML

Create representative evaluation media in Sorani, Badini, Arabic and English.

Define candidate-quality labels and human evaluation process.

Track model, prompt, parameters, confidence, cost and latency for every AI operation.

Build correction capture so manual edits can improve evaluation and future customer-specific recommendations.

23.5 QA and Release

Build deterministic media fixtures and golden outputs.

Automate tenant isolation, entitlement and account-state tests.

Test interrupted uploads, provider outage, worker crash, partial render and suspended account.

Run visual and audio regression checks on supported ratios and languages.

Define go/no-go criteria for internal MVP and external pilot separately.

23.6 Definition of Ready for MVP Build

Architecture and data model reviewed.

MVP scope protected from deferred features.

Subscription and approval workflow approved by Art City.

Supported media formats and language evaluation set confirmed.

Security, rights and data-retention baselines approved.

Initial plan configuration and cost assumptions documented.

Appendix A - Suggested Status Models

Project Status

DRAFT -> UPLOADING -> VALIDATING -> ANALYSING -> CANDIDATES_READY -> EDITING -> RENDERING -> QC_REVIEW -> HUMAN_REVIEW -> APPROVED -> EXPORTED/PUBLISHED -> ARCHIVED

Job Status

QUEUED -> RUNNING -> SUCCEEDED | FAILED | CANCELLED | TIMED_OUT | BLOCKED_BY_ENTITLEMENT

Version Review Status

DRAFT -> READY_FOR_REVIEW -> CHANGES_REQUESTED -> APPROVED -> SUPERSEDED

Appendix B - Example Editorial Brief Schema

{  "objective": "engagement",  "audience": ["Kurdish diaspora", "music professionals"],  "platforms": ["instagram_reels", "youtube_shorts"],  "target_duration": {"min": 25, "max": 50},  "quantity": 6,  "languages": ["ckb", "en"],  "tone": ["prestigious", "documentary"],  "focus": ["surprising claims", "future of Kurdish music"],  "restrictions": ["no political references", "preserve full meaning"],  "brand_profile_version_id": "bpv_...",  "deliverables": ["9:16", "4:5", "1:1", "16:9"]}

Appendix C - Example QC Manifest

{  "project_id": "prj_...",  "timeline_version_id": "tlv_...",  "outputs": [    {      "ratio": "9:16",      "resolution": "1080x1920",      "duration_seconds": 42.5,      "checksum_sha256": "...",      "technical_qc": "PASS",      "brand_compliance": "PASS",      "editorial_confidence": 0.86,      "warnings": []    }  ]}

Appendix D - Initial Non-Functional Requirements

ID

Requirement

NFR-001

Control-plane availability target: 99.5% monthly for MVP excluding planned maintenance.

NFR-002

API authorization decisions must not rely on client-supplied role or organisation values.

NFR-003

All long-running operations are asynchronous and recoverable.

NFR-004

Source masters are immutable and checksummed.

NFR-005

Sensitive data is encrypted in transit and at rest.

NFR-006

No raw media or transcript is written to general application logs.

NFR-007

Audit logs cover all administrative and rights-sensitive actions.

NFR-008

The platform supports horizontal worker scaling and separate CPU/GPU pools.

NFR-009

Outputs are reproducible from stored source, timeline schema, profile versions and render version.

NFR-010

The system supports feature flags and customer-specific pilot activation.

NFR-011

User-facing dates and times support localisation and organisation time zone.

NFR-012

Critical services include backup, restore and disaster recovery procedures tested before external production.

Appendix E - Final Product Statement

Approved summary

Art City Edit will be built as a subscription-based, Art City-approved editing and repurposing layer within Art City AI Studio. It will use prompts, media intelligence, brand memory and professional review to transform authorised long-form footage into high-quality multi-ratio outputs while preserving source integrity, customer data isolation and human editorial control.

This specification is sufficiently detailed to begin technical discovery, UX design, backlog creation and MVP architecture. The development team must record any assumption or proposed deviation before implementation.

Internal Approval

__________________________________________Product Owner / Art City Group

__________________________________________Technical Lead

__________________________________________Date