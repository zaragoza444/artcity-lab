# Art City AI Core Development Directive

Private Art City document. Source: Darwin Ways, CEO / Executive Producer, Art City Group.

Branch policy for this repository: \eature/*\ → \development\ → \staging\ → \main\. Production deploys only from \main\ after approval.

---

ART CITY AI
Development Directive for an Art City-Controlled Generative Media Platform
Technical Roadmap and Implementation Instructions for the Development Team
Objective: transform the existing Art City Cinema, Studio, Publish, and Projects platform from an orchestration and workflow system into a genuine Art City-controlled generative media platform with owned datasets, fine-tuned models, model registry, training pipelines, and controlled inference.
To: Art City AI Studio Development Team
From: Darwin Ways, CEO / Executive Producer, Art City Group
Subject: Development Directive - Building Art City AI as an Art City-Controlled Generative Media Platform
Dear Development Team,
Following the successful deployment of the current Art City AI Studio platform, I would like the next development phase to move beyond interface development, workflow orchestration, proxy generation, and permanent dependence on external AI providers.
Our long-term objective is to create Art City AI as a privately operated and Art City-controlled generative media platform capable of generating images, videos, voices, audio, music, characters, scenes, shots, advertising campaigns, and complete productions.
The existing platform - including Art City Cinema, Art City Studio, Art City Publish, and Projects - should remain the main production interface. However, a new technical intelligence layer must now be developed underneath these products.
The objective is not initially to train a completely new foundation model from zero. Instead, the development team must build the infrastructure that allows Art City to:
Host suitable open or commercially licensed AI models.
Fine-tune models using Art City-owned or properly licensed datasets.
Train character-specific and Kurdish cultural adapters.
Operate inference through Art City-controlled GPU infrastructure.
Maintain model versions, licences, datasets, evaluations, and deployment records.
Reduce dependence on external AI-generation providers over time.
Retain external providers only as optional fallback or specialist services.
1. Clarification of the Current Architecture
The current platform consists of:
Art City Cinema.
Art City Studio.
Art City Publish.
Projects.
FastAPI backend.
Next.js frontend.
PostgreSQL.
Redis.
MinIO.
Railway deployment.
Private GitHub repository.
This is a strong production-management and orchestration platform. However, it is important to understand that:
MinIO is storage, not an AI-generation engine.
PostgreSQL stores structured records.
Redis manages queues and temporary job states.
Cinema and Studio manage production requests.
Publish handles validation, packaging, manifests, and delivery.
External providers currently perform actual AI inference wherever they are connected.
The next phase must add Art City-controlled AI inference, training, datasets, models, and evaluation.
Art City Cinema / Art City Studio                ↓        Art City Backend                ↓       Art City Model Gateway                ↓  ┌─────────────┼─────────────┐  │             │             │Image Engine  Video Engine  Voice Engine  │             │             │Audio Engine  Music Engine  Evaluation Engine                ↓        Art City Model Registry                ↓        Art City-Controlled Storage
2. Create the Art City Model Gateway
The first major requirement is the creation of a new internal service called the Art City Model Gateway. This service must become the single controlled entry point for all AI-generation requests.
Cinema and Studio must not permanently call external providers directly. Instead, they must call the Art City Model Gateway, which will decide whether a request should be processed by:
An Art City-hosted model.
An Art City fine-tuned model.
An Art City character adapter.
An open or licensed model running on Art City-controlled GPU infrastructure.
An approved external provider used as a fallback.
2.1 Required API Endpoints
POST /api/v1/ai/images/generatePOST /api/v1/ai/videos/generatePOST /api/v1/ai/voices/generatePOST /api/v1/ai/audio/generatePOST /api/v1/ai/music/generateGET  /api/v1/ai/jobs/{job_id}POST /api/v1/ai/jobs/{job_id}/cancelPOST /api/v1/ai/jobs/{job_id}/retryGET  /api/v1/ai/modelsGET  /api/v1/ai/models/{model_id}GET  /api/v1/ai/providers
2.2 Gateway Responsibilities
Authenticate the requesting user.
Verify project permissions.
Identify the requested media type.
Select the appropriate model.
Estimate cost before generation.
Submit jobs to Redis or another asynchronous queue.
Track job status.
Record prompt, model, version, dataset, provider, cost, and output.
Store generated outputs inside Art City-controlled storage.
Return results to Cinema or Studio.
Support retry and provider fallback.
Prevent unauthorised model or dataset access.
2.3 Standard Model or Provider Interface
submit_generation()get_status()get_result()cancel_generation()estimate_cost()download_output()health_check()
This abstraction must allow Art City to replace or add providers and self-hosted models without changing the Cinema or Studio frontend.
3. Add an Art City Data Lab
Create a new main platform section:
/data-lab
The Data Lab will manage all material intended for:
Model training.
Fine-tuning.
LoRA creation.
Speech adaptation.
Knowledge retrieval.
Evaluation.
Archive search.
Kurdish cultural and language support.
Mandatory rule: uploading a file does not make it training data. Every file must pass rights verification, cleaning, labelling, quality review, and dataset approval.
3.1 Dataset Registry
Every dataset must have a permanent record containing:
Dataset ID and dataset name.
Description and category.
Media type.
Language and dialect.
Owner and source.
Copyright holder and licence.
Commercial-use permission.
AI-training permission.
Voice-cloning permission where relevant.
Dataset size and number of records.
Version and quality status.
Creation date and reviewer.
Storage location and checksum.
Intended model use.
3.2 Dataset Categories
Text, speech, and voice.
Images and video.
Music and sound effects.
Subtitles, dictionaries, scripts, and lyrics.
Character references.
Cultural and geographic references.
Educational content.
Production metadata.
3.3 Dataset Statuses
rawingestingprocessingneeds_reviewverifiedtraining_readyevaluation_onlyreference_onlyblockedarchived
Only datasets marked training_ready may be attached to a training job.
4. Build a Data Ingestion Pipeline
The Data Lab must include a controlled ingestion service for large archives.
4.1 Supported Sources
Local upload.
MinIO or S3 bucket.
Existing Art City archive.
CSV or Excel metadata.
Subtitle and script files.
Audio, video, and image collections.
Database exports.
Authorised API imports.
4.2 Ingestion Operations
File validation and media-type detection.
Metadata extraction.
Duplicate detection.
Checksum generation.
File-format conversion.
Thumbnail and preview generation.
Audio extraction from video.
Subtitle extraction.
Language detection and basic dialect classification.
Duration and resolution detection.
Corrupt-file detection.
Personal-data risk flagging.
Rights-status verification.
Dataset record creation.
Every ingestion process must produce a report showing:
Number of files imported.
Number of duplicates.
Number of failed files.
Number of files with unknown rights.
Number of files requiring human review.
Total storage used.
Processing duration.
Operator identity.
5. Create an Annotation Workspace
Create the following route:
/data-lab/annotations
The annotation system must allow authorised reviewers to correct, verify, discuss, approve, and reject labels.
5.1 Text Annotation
Spelling and grammar.
Dialect and translation.
Child-friendly wording.
Cultural terminology.
Named entities.
Sentence boundaries.
Word changes and final approved versions.
5.2 Speech Annotation
Exact transcript.
Speaker identity and speaker changes.
Dialect and pronunciation.
Noise and music overlap.
Confidence score.
Consent status.
5.3 Image, Video, and Music Annotation
Character identity, clothing, region, location, objects, season, colour, and cultural elements.
Shot and scene boundaries, actions, camera movement, dialogue, and reusable video segments.
Lyrics, language, BPM, key, instrument, performer, composer, region, rights, and stems.
5.4 Annotation Controls
Reviewer assignment.
Review status.
Comment threads.
Revision history.
Approval and rejection.
Conflict resolution.
Export to JSONL, CSV, Parquet, or model-specific training manifests.
6. Add a Rights and Consent Registry
Create a protected section:
/rights
Every dataset, media file, voice, image, video, song, script, and model must have a traceable rights record before commercial use or model training.
6.1 Required Rights Fields
Rights record ID.
Asset or dataset ID.
Copyright owner.
Performer, speaker, photographer, composer, writer, or producer.
Source organisation.
Contract reference.
Commercial-use permission.
AI-training and fine-tuning permission.
Voice-cloning and image-generation permission.
Geographic and time restrictions.
Expiry date.
Consent document.
Legal-review status and notes.
6.2 Rights Statuses
approved_for_trainingapproved_for_referenceapproved_for_commercial_useapproved_for_voice_cloningrestrictedexpiredunknownblocked
6.3 Mandatory Backend Rule
If AI training permission is not approved,the dataset cannot be attached to a training job.
This restriction must be enforced in backend and database logic, not only as a warning in the user interface.
7. Create the Art City Model Registry
Create a new section:
/models
The Model Registry will be the official inventory of every AI model and adapter used by Art City.
7.1 Model Types
Foundation and base models.
Fine-tuned models.
LoRA, character, and style adapters.
Voice and speech-recognition models.
Image, video, audio, and music models.
Embedding, upscaler, safety, and evaluation models.
7.2 Required Model Information
Model ID, name, and version.
Model type and base model.
Source and licence.
Commercial-use status and owner.
Training and evaluation dataset versions.
Training method and framework.
GPU requirements.
Checkpoint location and checksum.
Quality score and known limitations.
Approved projects and deployment environment.
Created, approved, and deprecated dates.
7.3 Model Statuses
draftregisteredtrainingevaluatingapprovedstagingproductiondeprecatedblockedarchived
7.4 Example Records
Model: AC-KARDOKH-IMAGE-v1Type: Character LoRAOwner: Art CityBase model: Approved image base modelDataset: KD-CHARACTER-001-v2Status: stagingCommercial use: approvedModel: AC-KURDIYA-IMAGE-v1Type: Character LoRAOwner: Art CityDataset: KD-CHARACTER-002-v2Status: evaluatingModel: AC-KURDISH-ASR-v1Type: Kurdish speech-recognition modelLanguages: Sorani / Badini / KurmanjiStatus: development
8. Create a Training and Fine-Tuning Manager
Create a new section:
/training
The first objective is not to train a large foundation model from zero. Initial training must focus on efficient, specialised adaptation.
LoRA and parameter-efficient fine-tuning.
Character and style adapters.
Speech-model and voice-model adaptation.
Embedding generation.
Classifier and evaluation-model training.
8.1 Training Job Fields
Training job ID and model type.
Base model and dataset version.
Evaluation dataset.
Training method and configuration.
Epochs, learning rate, batch size, and seed.
GPU type and number of GPUs.
Estimated and actual cost.
Initiating user, start date, and end date.
Logs, checkpoints, and failure reason.
Evaluation result and approval decision.
8.2 Training Workflow
Verified dataset        ↓Rights verification        ↓Create training job        ↓Estimate GPU cost        ↓Producer or administrator approval        ↓Run training        ↓Store checkpoints        ↓Run evaluation        ↓Human review        ↓Approve or reject model        ↓Publish approved model to Model Registry
8.3 Safety Controls
Prevent training on unapproved, expired, or unknown-rights datasets.
Prevent voice cloning without documented consent.
Prevent accidental use of production evaluation sets as training data.
Prevent overwriting existing production models.
Prevent untracked checkpoints.
Prevent production deployment without evaluation and approval.
9. Build Art City-Controlled Inference Workers
Create separate worker services for actual generation:
image-workervideo-workervoice-workeraudio-workermusic-workerupscale-workerevaluation-workerembedding-worker
These services must run in Art City-controlled infrastructure. Initially, this can be GPU cloud infrastructure paid for and controlled by Art City. Physical on-premise GPU servers should be considered only after usage and costs are measured.
9.1 Generation Workflow
Cinema or Studio request        ↓Art City Model Gateway        ↓Redis queue        ↓Art City inference worker        ↓Art City-hosted or fine-tuned model        ↓Generated result        ↓Quality control        ↓Art City storage        ↓Cinema or Studio review
9.2 Worker Requirements
Job reservation and GPU availability checking.
Model loading and caching.
Generation and progress reporting.
Cancellation, timeout, and retry.
Error logging.
Output validation.
Cost estimation.
Storage upload.
Health check and metrics.
10. Build the First Art City-Owned Image Engine
The first self-hosted generative capability should be image generation. This is the most realistic and technically manageable starting point.
10.1 Initial Image Engine Capabilities
Text-to-image and image-to-image.
Character-reference generation.
Inpainting and background replacement.
Object replacement.
Control and pose guidance.
Upscaling.
LoRA and character-adapter loading.
Style presets.
Seed control.
Resolution selection.
Batch generation.
10.2 Initial Art City Models
AC-KARDOKH-IMAGE-v1AC-KURDIYA-IMAGE-v1
These adapters must be trained using approved and verified character-reference datasets.
10.3 Required Generation Flow
Select Kardokh or Kurdiya        ↓Select approved model version        ↓Enter scene prompt        ↓Attach official references        ↓Run Art City image worker        ↓Generate multiple versions        ↓Run visual QC        ↓Approve one version        ↓Store in Studio asset library
This is the first decisive proof that Art City controls its own inference and fine-tuned models, rather than only operating a branded interface over third-party generation.
11. Add a Kurdish Knowledge Base
Create a new section:
/knowledge
The Kurdish Knowledge Base should support retrieval-augmented generation, dataset preparation, language consistency, and cultural verification.
11.1 Initial Categories
Kurdish dictionaries and terminology.
Sorani, Badini, and Kurmanji vocabulary.
Kurdish months, seasons, and traditional time names.
Geography, mountains, rivers, cities, and villages.
Clothing, foods, customs, and proverbs.
Children's vocabulary and body-part terminology.
Finger and toe names.
Songs, stories, and Shayi / Kurdish folk movement.
Kardokh and Kurdiya Story Bible.
Cultural rules and approved terminology.
11.2 Required Entry Fields
Entry ID.
Word or concept.
Language and dialect.
Definition and child-friendly definition.
Translation and example sentence.
Source and licence.
Reviewer and approval status.
Cultural notes.
Related media.
Pronunciation audio.
Cinema and Studio must be able to query the Knowledge Base when generating scripts, prompts, subtitles, and educational content.
12. Create an Evaluation and Benchmark Lab
Create a new section:
/evaluations
No candidate model should be deployed directly into production. It must first be evaluated against the current approved model.
12.1 Image and Video Metrics
Character identity and facial consistency.
Clothing and Kurdish cultural accuracy.
Hand and finger accuracy.
Prompt adherence.
Background consistency.
Motion stability.
Visual artifacts.
Resolution and style consistency.
Child-safety compliance.
12.2 Speech and Voice Metrics
Word error rate.
Dialect and named-entity accuracy.
Kurdish proper-name accuracy.
Noise tolerance and speaker separation.
Subtitle timing.
Naturalness and pronunciation.
Voice similarity and emotional control.
Stability, consent verification, and speaker-identity protection.
12.3 Evaluation Workflow
Candidate model        ↓Run standard benchmark        ↓Compare with current production model        ↓Human review        ↓Approve or reject        ↓Deploy only if approved
A new model must not automatically replace an existing model merely because it is newer.
13. Build the Model Router
The Model Gateway should contain a routing engine that selects the appropriate model for each job.
13.1 Routing Factors
Media type and character.
Project and required quality.
Resolution and speed.
Cost and project budget.
GPU availability.
Privacy level.
Licence and approved use.
Historical success rate.
Production status.
13.2 Routing Example
Kardokh image    → AC-KARDOKH-IMAGE-v1Kurdiya image    → AC-KURDIYA-IMAGE-v1Kurdish landscape    → Art City general image modelShort character animation    → Art City video modelHigh-complexity premium shot    → Approved external provider fallback
External providers should become fallback or specialist services, not the permanent core of the platform.
14. Strengthen Security Before Archive Ingestion
Before large archives or confidential datasets are uploaded, the current platform must be secured.
14.1 Mandatory Security Work
Authentication and role-based permissions.
Protected APIs.
Admin-only model and training controls.
Dataset-level access permissions.
Encryption in transit and at rest where applicable.
Audit logs.
Secure provider and GPU credentials.
Secret rotation.
Malware scanning and file validation.
Rate limiting.
Session expiration.
Two-factor authentication for administrators.
Separate staging and production environments.
Automated backups and restore testing.
14.2 Restricted Production Actions
Only explicitly authorised roles may:
Upload or download datasets.
Approve rights.
Start training.
Register or promote models.
Clone voices.
View confidential client assets.
Change model-routing rules.
15. GitHub and Deployment Controls
The private GitHub repository must remain owned by Art City.
Protect the main branch.
Require pull requests and at least one reviewer.
Require automated tests and successful build checks.
Prevent force pushes.
Record all deployments.
Separate development, staging, and production.
Use separate environment variables for each environment.
Never commit real .env files.
Never commit datasets or model weights directly to Git.
Recommended branch structure:
feature/*developmentstagingmain
Production deployment should occur only from main after approval.
16. Required New Navigation Structure
DashboardProjectsCinemaStudioPublishData LabKnowledgeRightsModelsTrainingEvaluationsCostsNotificationsUsersSettings
The new sections must use the same Art City design system as the existing platform.
17. Recommended Sprint Plan
Sprint
Estimated Duration
Focus
Key Deliverables
Sprint 1
2-3 weeks
Core control layer
Authentication and RBAC; Model Gateway; Dataset Registry; Rights Registry; Model Registry; branch protection; staging environment; audit logging.
Sprint 2
3-4 weeks
Data and first inference
Data ingestion; annotation workspace; Kurdish Knowledge Base; one self-hosted image worker; GPU queue; evaluation framework; Studio integration.
Sprint 3
4-8 weeks
Character model pilot
Kardokh and Kurdiya datasets; rights verification; AC-KARDOKH-IMAGE-v1; AC-KURDIYA-IMAGE-v1; benchmark; Cinema/Studio integration; external fallback; cost report.
Sprint 4
Following phase
Video and Kurdish speech preparation
Self-hosted image-to-video worker; video evaluation; Kurdish speech ingestion; transcript annotation; ASR pilot; voice-engine feasibility; one complete real campaign.
18. Definition of Success
This phase is not complete merely because new pages exist. It is successful only when the team can demonstrate:
A verified Kardokh dataset exists.
A verified Kurdiya dataset exists.
Both datasets have approved AI-training rights.
Two Art City character adapters have been trained.
Both models are registered with version and checksum.
Generation runs on Art City-controlled GPU infrastructure.
Studio generates Kardokh and Kurdiya images through the Model Gateway.
Outputs are stored under Art City control.
Visual QC compares outputs with official references.
The approved image enters Cinema or a Project.
Prompt, dataset, model version, user, cost, and output are traceable.
An external provider can be disabled without breaking the platform.
19. Final Strategic Principle
CinemaCreates complete campaign packagesStudioCreates individual assetsPublishValidates, packages, and releases approved outputsProjectsControls production records and ownershipData LabCreates verified datasetsTrainingCreates Art City model adaptationsModel RegistryControls model versions and licencesModel GatewayRuns and routes all AI generationInference WorkersPerform actual Art City-controlled generation
The current platform is the production operating system. The new AI Core will become the intelligence and generation layer underneath it.
Final objective: Art City must own the platform, source code, datasets, fine-tuned models, character adapters, model gateway, production records, deployment accounts, and inference control. External AI providers must remain optional and replaceable.
Please treat this development phase as the transition from an Art City-branded AI orchestration platform into a genuine Art City-controlled generative media system.
Kind regards,
Darwin Ways
CEO / Executive Producer
Art City Group