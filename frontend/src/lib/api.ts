import { getAccessToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Project = {
  id: string;
  name: string;
  description: string | null;
  status: string;
  budget_limit: number | null;
  created_at: string;
  updated_at: string;
};

export type Character = {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  costume_notes: string | null;
  created_at: string;
};

export type Script = {
  id: string;
  project_id: string;
  title: string;
  language: string;
  body: string;
  created_at: string;
};

export type Health = {
  status: string;
  database: string;
  redis: string;
  minio: string;
};

export type Modality = "image" | "video" | "voice" | "audio" | "music";

export type GenerationJob = {
  id: string;
  project_id: string;
  modality: Modality | string;
  provider: string;
  model: string | null;
  prompt: string | null;
  status: string;
  result_uri: string | null;
  error_message: string | null;
  estimated_cost: number | null;
  actual_cost: number | null;
  provider_job_id: string | null;
  created_at: string;
  updated_at: string;
  media_url?: string | null;
  audio_url?: string | null;
  transcript_url?: string | null;
  transcript_job_id?: string | null;
  asr_summary?: string | null;
};

export type Asset = {
  id: string;
  project_id: string;
  asset_type: string;
  name: string;
  storage_path: string | null;
  metadata_json: Record<string, unknown> | null;
  soft_deleted: boolean;
  created_at: string;
  media_url?: string | null;
};

export type StudioSummary = {
  project_id: string;
  totals: Record<string, number>;
  approved: number;
  pending_review: number;
  spent: number;
};

export type Review = {
  id: string;
  generation_job_id: string;
  decision: string;
  notes: string | null;
  reviewer_role: string;
  quality_score: number | null;
  created_at: string;
};

export function mediaAbsolute(path?: string | null): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${API_URL}${path}`;
}

/** Append JWT for browser downloads (ZIP, manifest) that cannot send Authorization headers. */
export function withAccessToken(url: string): string {
  const token = getAccessToken();
  if (!token) return url;
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}access_token=${encodeURIComponent(token)}`;
}

function formatApiError(status: number, text: string): string {
  try {
    const data = JSON.parse(text) as {
      message?: string;
      detail?: unknown;
    };
    if (typeof data.message === "string" && data.message.trim()) {
      return data.message;
    }
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object") {
            const row = item as { field?: string; message?: string; msg?: string; loc?: unknown[] };
            const field =
              row.field ||
              (Array.isArray(row.loc)
                ? row.loc.filter((x) => x !== "body").join(".")
                : undefined);
            const msg = row.message || row.msg || "Invalid value";
            return field ? `${field}: ${msg}` : msg;
          }
          return String(item);
        })
        .join("; ");
    }
    if (typeof data.detail === "string") return data.detail;
  } catch {
    /* plain text */
  }
  return text || `Request failed: ${status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(formatApiError(res.status, text));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: string;
  email: string;
  full_name: string;
  user_id: string;
};

export type Dataset = {
  id: string;
  name: string;
  description: string | null;
  category: string;
  media_type: string;
  status: string;
  version: string;
  ai_training_permission: boolean;
  commercial_use: boolean;
  checksum: string | null;
  record_count: number;
  created_at: string;
};

export type RightsRecord = {
  id: string;
  dataset_id: string | null;
  copyright_owner: string;
  ai_training: boolean;
  commercial_use: boolean;
  legal_status: string;
  created_at: string;
};

export type RegistryModel = {
  id: string;
  name: string;
  version: string;
  model_type: string;
  character_key: string | null;
  modality: string;
  status: string;
  checksum: string | null;
  commercial_use: boolean;
  created_at: string;
};

export type TrainingJob = {
  id: string;
  base_model: string;
  dataset_id: string;
  status: string;
  epochs: number;
  estimated_cost: number | null;
  resulting_model_id: string | null;
  created_at: string;
};

export type KnowledgeEntry = {
  id: string;
  term: string;
  language: string;
  dialect: string | null;
  definition: string;
  translation?: string | null;
  example_sentence?: string | null;
  category: string;
  approval_status: string;
  cultural_notes?: string | null;
  created_at: string;
};

export type SpeechDialect = {
  id: string;
  label: string;
  script: string;
};

export type AsrManifest = {
  engine: string;
  model?: string;
  status: string;
  language: string;
  dialect: string;
  average_confidence: number;
  segment_count: number;
  job_id?: string;
  audio_storage_key?: string;
  media_urls?: {
    transcript?: string;
    vtt?: string;
    srt?: string;
  };
  segments: {
    start: number;
    end: number;
    text: string;
    speaker?: string;
    dialect?: string;
    confidence: number;
  }[];
};

export type SpeechUploadResult = {
  audio_storage_key: string;
  project_id: string;
  asset_id: string;
  checksum: string;
  bytes: number;
  duration_seconds: number | null;
  content_type: string;
};

export type AnnotationTask = {
  id: string;
  dataset_id: string;
  media_type: string;
  payload: Record<string, unknown>;
  labels: Record<string, unknown> | null;
  status: string;
  comments: unknown[] | null;
  created_at: string;
};

export type EvaluationRun = {
  id: string;
  candidate_model_id: string;
  modality: string;
  metrics: Record<string, unknown> | null;
  status: string;
  human_decision: string | null;
  created_at: string;
};

export const api = {
  health: () => request<Health>("/health"),
  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ id: string; email: string; full_name: string; role: string }>("/api/auth/me"),
  listDatasets: () => request<Dataset[]>("/api/datasets"),
  listRights: () => request<RightsRecord[]>("/api/rights"),
  listRegistryModels: () => request<RegistryModel[]>("/api/models/registry"),
  listTraining: () => request<TrainingJob[]>("/api/training"),
  listKnowledge: (q?: string, dialect?: string) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (dialect) params.set("dialect", dialect);
    const qs = params.toString();
    return request<KnowledgeEntry[]>(`/api/knowledge${qs ? `?${qs}` : ""}`);
  },
  createKnowledge: (body: {
    term: string;
    definition: string;
    language?: string;
    dialect?: string;
    translation?: string;
    example_sentence?: string;
    category?: string;
  }) =>
    request<KnowledgeEntry>("/api/knowledge", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  approveKnowledge: (id: string) =>
    request<KnowledgeEntry>(`/api/knowledge/${id}/approve`, { method: "PATCH" }),
  queryKnowledge: (terms: string, dialect?: string) => {
    const params = new URLSearchParams({ terms });
    if (dialect) params.set("dialect", dialect);
    return request<KnowledgeEntry[]>(`/api/knowledge/query?${params}`);
  },
  culturalPack: (dialect?: string) =>
    request<{
      language: string;
      dialect: string | null;
      count: number;
      categories: Record<string, KnowledgeEntry[]>;
    }>(`/api/knowledge/cultural-pack${dialect ? `?dialect=${encodeURIComponent(dialect)}` : ""}`),
  listSpeechDialects: () =>
    request<{ language: string; dialects: SpeechDialect[]; model: string; engine?: string }>(
      "/api/v1/ai/speech/dialects"
    ),
  detectLanguage: (text: string) =>
    request<{ language: string; dialect: string; script: string; confidence: number }>(
      "/api/v1/ai/speech/detect",
      { method: "POST", body: JSON.stringify({ text }) }
    ),
  uploadSpeechAudio: async (file: File, projectId?: string) => {
    const token = getAccessToken();
    const form = new FormData();
    form.append("file", file);
    if (projectId) form.append("project_id", projectId);
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/api/v1/ai/speech/upload`, {
      method: "POST",
      headers,
      body: form,
      cache: "no-store",
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(formatApiError(res.status, text));
    }
    return res.json() as Promise<SpeechUploadResult>;
  },
  runAsr: (body: {
    audio_storage_key: string;
    dialect?: string;
    duration_hint?: number;
    project_id?: string;
    create_annotation?: boolean;
  }) =>
    request<AsrManifest>("/api/v1/ai/speech/asr", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getSpeechJob: (jobId: string) =>
    request<AsrManifest & { job?: GenerationJob }>(`/api/v1/ai/speech/jobs/${jobId}`),
  downloadSpeechSubtitle: async (jobId: string, format: "vtt" | "srt" = "vtt") => {
    const token = getAccessToken();
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(
      `${API_URL}/api/v1/ai/speech/jobs/${jobId}/subtitles?format=${format}`,
      { headers, cache: "no-store" }
    );
    if (!res.ok) {
      const text = await res.text();
      throw new Error(formatApiError(res.status, text));
    }
    return res.blob();
  },
  downloadSpeechTranscript: async (jobId: string) => {
    const token = getAccessToken();
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/api/v1/ai/speech/jobs/${jobId}/transcript`, {
      headers,
      cache: "no-store",
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(formatApiError(res.status, text));
    }
    return res.blob();
  },
  listAnnotations: () => request<AnnotationTask[]>("/api/data-lab/annotations"),
  createAnnotation: (body: {
    dataset_id: string;
    media_type?: string;
    payload: Record<string, unknown>;
    labels?: Record<string, unknown>;
  }) =>
    request<AnnotationTask>("/api/data-lab/annotations", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateAnnotation: (
    id: string,
    body: { labels?: Record<string, unknown>; status?: string; comment?: string }
  ) =>
    request<AnnotationTask>(`/api/data-lab/annotations/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  listEvaluations: () => request<EvaluationRun[]>("/api/evaluations"),
  listProviders: () => request<{ name: string; healthy: boolean }[]>("/api/v1/ai/providers"),
  listAiModels: () => request<RegistryModel[]>("/api/v1/ai/models"),
  generateImage: (body: {
    project_id: string;
    prompt: string;
    character_key?: string;
    character_name?: string;
    model?: string;
  }) =>
    request<GenerationJob>("/api/v1/ai/images/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getAiJob: (jobId: string) => request<GenerationJob>(`/api/v1/ai/jobs/${jobId}`),
  listProjects: () => request<Project[]>("/api/projects"),
  createProject: (body: { name: string; description?: string; budget_limit?: number }) =>
    request<Project>("/api/projects", { method: "POST", body: JSON.stringify(body) }),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  listCharacters: (projectId: string) =>
    request<Character[]>(`/api/projects/${projectId}/characters`),
  createCharacter: (projectId: string, body: { name: string; description?: string }) =>
    request<Character>(`/api/projects/${projectId}/characters`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listScripts: (projectId: string) => request<Script[]>(`/api/projects/${projectId}/scripts`),
  createScript: (
    projectId: string,
    body: { title: string; body: string; language?: string }
  ) =>
    request<Script>(`/api/projects/${projectId}/scripts`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  studioSummary: (projectId: string) =>
    request<StudioSummary>(`/api/projects/${projectId}/studio/summary`),
  listGenerations: (projectId: string) =>
    request<GenerationJob[]>(`/api/projects/${projectId}/generations`),
  listAssets: (projectId: string) => request<Asset[]>(`/api/projects/${projectId}/assets`),
  generate: (
    projectId: string,
    body: {
      modality: Modality;
      prompt: string;
      duration_seconds?: number;
      dialogue_lines?: string[];
      character_name?: string;
      dialect?: string;
    }
  ) =>
    request<GenerationJob>(`/api/projects/${projectId}/studio/generate`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  review: (
    projectId: string,
    jobId: string,
    body: { decision: "approve" | "reject" | "request_changes"; notes?: string; quality_score?: number }
  ) =>
    request<Review>(`/api/projects/${projectId}/generations/${jobId}/reviews`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  createCinemaPackage: (
    projectId: string,
    body: {
      campaign: string;
      brief: string;
      cta?: string;
      brand?: string;
      voiceover_script?: string;
      music_style?: "epic" | "warm" | "pulse" | "soft";
      duration_seconds?: number;
      initiated_by?: string;
      dialect?: string;
      character_key?: string;
      character_name?: string;
      channels?: string[];
    }
  ) =>
    request<CinemaPackage>(`/api/projects/${projectId}/cinema/packages`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listCinemaPackages: (projectId: string) =>
    request<CinemaPackage[]>(`/api/projects/${projectId}/cinema/packages`),
  validateCinemaPackage: (projectId: string, packageId: string) =>
    request<CinemaPackage>(`/api/projects/${projectId}/cinema/packages/${packageId}/validate`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  cinemaZipUrl: (projectId: string, packageId: string) =>
    withAccessToken(
      `${API_URL}/api/projects/${projectId}/cinema/packages/${packageId}/zip`
    ),
  cinemaManifestUrl: (projectId: string, packageId: string) =>
    withAccessToken(
      `${API_URL}/api/projects/${projectId}/cinema/packages/${packageId}/manifest`
    ),
  cinemaValidationUrl: (projectId: string, packageId: string) =>
    withAccessToken(
      `${API_URL}/api/projects/${projectId}/cinema/packages/${packageId}/validation`
    ),
  listPublications: (projectId: string) =>
    request<Publication[]>(`/api/projects/${projectId}/publications`),
  createPublication: (
    projectId: string,
    body: {
      cinema_package_id: string;
      channel?: string;
      auto_approve_missing?: boolean;
      publisher_note?: string;
    }
  ) =>
    request<Publication>(`/api/projects/${projectId}/publications`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getPublication: (projectId: string, publicationId: string) =>
    request<Publication>(`/api/projects/${projectId}/publications/${publicationId}`),
  finalizePublish: (projectId: string, publicationId: string) =>
    request<Publication>(`/api/projects/${projectId}/publications/${publicationId}/publish`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
};

export type CinemaDeliverable = {
  role?: string | null;
  type?: string | null;
  modality: string;
  job_id: string;
  label?: string | null;
  aspect?: string | null;
  aspect_ratio?: string | null;
  media_url?: string | null;
  audio_url?: string | null;
  video_file?: string | null;
  audio_file?: string | null;
  file?: string | null;
  mood?: string | null;
  script?: string | null;
  transcript?: AsrManifest | null;
  transcript_job_id?: string | null;
  subtitle_vtt?: string | null;
  subtitle_srt?: string | null;
};

export type ValidationCheck = {
  id: string;
  label: string;
  passed: boolean;
  expected: unknown;
  actual: unknown;
  detail: string;
};

export type DeliverableValidation = {
  role: string;
  passed: boolean;
  checks: ValidationCheck[];
  technical?: Record<string, unknown>;
};

export type PackageValidation = {
  passed: boolean;
  completeness?: ValidationCheck;
  deliverables: DeliverableValidation[];
  presets?: Record<string, unknown>;
  targets?: Record<string, unknown>;
};

export type CinemaPackage = {
  package_id: string;
  asset_id: string;
  product?: string;
  campaign: string;
  brief: string;
  cta: string;
  brand: string;
  brand_colors?: Record<string, string>;
  music_style: string;
  duration_seconds: number;
  formats: string[];
  deliverables: CinemaDeliverable[];
  total_cost: number;
  production_time_seconds?: number | null;
  initiated_by?: string | null;
  usage_rights?: string | null;
  campaign_manifest?: Record<string, unknown> | null;
  validation?: PackageValidation | null;
  validation_passed?: boolean | null;
  manifest_url?: string | null;
  validation_url?: string | null;
  zip_url?: string | null;
  created_at?: string | null;
};

export type ChecklistItem = {
  id: string;
  label: string;
  required: boolean;
  status: string;
  detail?: string | null;
  master?: Record<string, unknown> | null;
};

export type PublicationMaster = {
  role: string;
  label: string;
  aspect?: string | null;
  modality?: string | null;
  filename?: string;
  media_url?: string | null;
  audio_url?: string | null;
  checksum_sha256?: string;
  bytes?: number;
};

export type Publication = {
  publication_id: string;
  asset_id: string;
  project_id: string;
  cinema_package_id?: string | null;
  campaign?: string | null;
  channel?: string | null;
  status?: string | null;
  formats: string[];
  checklist: ChecklistItem[];
  masters: PublicationMaster[];
  progress: number;
  manifest_url?: string | null;
  report_url?: string | null;
  publisher_note?: string | null;
  published_at?: string | null;
  created_at?: string | null;
};
