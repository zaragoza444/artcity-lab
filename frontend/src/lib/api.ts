import {
  clearSession,
  emitSessionExpired,
  getAccessToken,
  getRefreshToken,
  setSession,
} from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: string;
  email: string;
  full_name: string;
  user_id: string;
  phone_number?: string | null;
  email_verified?: boolean;
  phone_verified?: boolean;
};

let refreshInFlight: Promise<boolean> | null = null;

function isAuthPublicPath(path: string): boolean {
  return (
    path.startsWith("/api/auth/login") ||
    path.startsWith("/api/auth/signup") ||
    path.startsWith("/api/auth/refresh") ||
    path.startsWith("/api/auth/verify-email") ||
    path.startsWith("/api/auth/verify-phone") ||
    path.startsWith("/api/auth/token")
  );
}

/** Refresh access token using stored refresh token. Returns true when a new session is stored. */
export async function refreshAccessSession(): Promise<boolean> {
  if (typeof window === "undefined") return false;
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;
    try {
      const res = await fetch(`${API_URL}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: "no-store",
      });
      if (!res.ok) {
        clearSession();
        return false;
      }
      const data = (await res.json()) as TokenResponse;
      if (!data.access_token || !data.refresh_token) {
        clearSession();
        return false;
      }
      setSession(data);
      return true;
    } catch {
      clearSession();
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

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

export type DataBankAsset = Asset & {
  checksum?: string | null;
  source?: string | null;
  tags?: string[];
  prompt?: string | null;
  size_bytes?: number | null;
  content_type?: string | null;
};

export type DataBankSummary = {
  project_id: string;
  total: number;
  by_type: Record<string, number>;
  by_source: Record<string, number>;
};

export type DataBankHub = {
  projects_with_assets: number;
  total_assets: number;
  bank_project_id: string | null;
  projects: Array<{
    project_id: string;
    name: string;
    total: number;
    by_type: Record<string, number>;
    by_source: Record<string, number>;
  }>;
};

export type DataBankSeed = {
  project: { id: string; name: string; description?: string | null };
  seed_job_id: string;
  seed_status: string;
  seed_media_url?: string | null;
  sync: { created: number; skipped: number; jobs_scanned: number };
  summary: DataBankSummary;
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

async function request<T>(path: string, init?: RequestInit, retried = false): Promise<T> {
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

  if (res.status === 401 && !retried && !isAuthPublicPath(path)) {
    const refreshed = await refreshAccessSession();
    if (refreshed) {
      return request<T>(path, init, true);
    }
    clearSession();
    emitSessionExpired();
    const text = await res.text();
    throw new Error(formatApiError(401, text || '{"detail":"Not authenticated"}'));
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(formatApiError(res.status, text));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

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
  language?: string | null;
  dialect?: string | null;
  size_bytes?: number;
};

export type IngestionRun = {
  id: string;
  dataset_id: string | null;
  source_type: string;
  status: string;
  report: {
    imported?: number;
    duplicates?: number;
    failed?: number;
    unknown_rights?: number;
    needs_review?: number;
    total_bytes?: number;
    duration_seconds?: number;
    operator?: string;
    language?: string;
    dialect?: string;
    media_counts?: Record<string, number>;
  } | null;
  created_at: string;
};

export type DatasetFile = {
  id: string;
  dataset_id: string;
  ingestion_run_id?: string | null;
  filename: string;
  storage_key: string;
  checksum: string;
  content_type?: string | null;
  media_type: string;
  size_bytes: number;
  language?: string | null;
  dialect?: string | null;
  rights_status: string;
  duration_seconds?: number | null;
  media_url?: string | null;
  created_at?: string | null;
};

export type DatasetDetail = Dataset & {
  file_count: number;
  approved_annotations: number;
  pending_annotations: number;
  storage_path?: string | null;
  intended_model_use?: string | null;
  voice_cloning_permission?: boolean;
  rights: {
    id: string;
    copyright_owner: string;
    legal_status: string;
    ai_training: boolean;
    commercial_use: boolean;
  } | null;
  latest_ingestion: {
    id: string;
    status: string;
    report: IngestionRun["report"];
    created_at: string | null;
  } | null;
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
  assignee_id?: string | null;
  comments: unknown[] | null;
  revision_history?: unknown[] | null;
  created_at: string;
  updated_at?: string | null;
};

export type AnnotationStats = {
  total: number;
  by_status: Record<string, number>;
  by_media: Record<string, number>;
  asr_sourced: number;
  ingest_sourced: number;
  dataset_id?: string | null;
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
  signup: (body: {
    email: string;
    full_name: string;
    phone_number: string;
    password: string;
    accept_terms: boolean;
  }) =>
    request<{
      user_id: string;
      email: string;
      phone_number: string;
      full_name: string;
      account_state: string;
      message: string;
      email_token?: string | null;
      phone_code?: string | null;
    }>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  verifyEmail: (email: string, token: string) =>
    request<{
      email: string;
      email_verified: boolean;
      phone_verified: boolean;
      account_state: string;
      can_login: boolean;
    }>("/api/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ email, token }),
    }),
  verifyPhone: (email: string, code: string) =>
    request<{
      email: string;
      email_verified: boolean;
      phone_verified: boolean;
      account_state: string;
      can_login: boolean;
    }>("/api/auth/verify-phone", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),
  me: () =>
    request<{
      id: string;
      email: string;
      full_name: string;
      role: string;
      phone_number?: string | null;
      email_verified_at?: string | null;
      phone_verified_at?: string | null;
    }>("/api/auth/me"),
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
  ingestFiles: async (opts: {
    files: FileList | File[];
    datasetId?: string;
    datasetName?: string;
    language?: string;
    dialect?: string;
  }) => {
    const token = getAccessToken();
    const form = new FormData();
    const list = Array.from(opts.files);
    for (const file of list) form.append("files", file);
    if (opts.datasetId) form.append("dataset_id", opts.datasetId);
    if (opts.datasetName) form.append("dataset_name", opts.datasetName);
    if (opts.language) form.append("language", opts.language);
    if (opts.dialect) form.append("dialect", opts.dialect);
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/api/data-lab/ingest`, {
      method: "POST",
      headers,
      body: form,
      cache: "no-store",
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(formatApiError(res.status, text));
    }
    return res.json() as Promise<IngestionRun>;
  },
  listIngestions: () => request<IngestionRun[]>("/api/data-lab/ingestions"),
  getIngestion: (runId: string) => request<IngestionRun>(`/api/data-lab/ingestions/${runId}`),
  getDatasetDetail: (datasetId: string) =>
    request<DatasetDetail>(`/api/data-lab/datasets/${datasetId}`),
  listDatasetFiles: (datasetId: string) =>
    request<DatasetFile[]>(`/api/data-lab/datasets/${datasetId}/files`),
  getDatasetManifest: (datasetId: string) =>
    request<Record<string, unknown>>(`/api/data-lab/datasets/${datasetId}/manifest`),
  exportDataset: async (datasetId: string, format: "jsonl" | "csv" = "jsonl", persist = false) => {
    const token = getAccessToken();
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const qs = new URLSearchParams({ format, persist: String(persist) });
    const res = await fetch(`${API_URL}/api/data-lab/datasets/${datasetId}/export?${qs}`, {
      headers,
      cache: "no-store",
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(formatApiError(res.status, text));
    }
    return res.blob();
  },
  updateDatasetStatus: (datasetId: string, status: string) =>
    request<Dataset>(`/api/datasets/${datasetId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  listAnnotations: (opts?: { dataset_id?: string; status?: string; media_type?: string }) => {
    const params = new URLSearchParams();
    if (opts?.dataset_id) params.set("dataset_id", opts.dataset_id);
    if (opts?.status) params.set("status", opts.status);
    if (opts?.media_type) params.set("media_type", opts.media_type);
    const qs = params.toString();
    return request<AnnotationTask[]>(`/api/data-lab/annotations${qs ? `?${qs}` : ""}`);
  },
  getAnnotation: (id: string) => request<AnnotationTask>(`/api/data-lab/annotations/${id}`),
  annotationStats: (datasetId?: string) =>
    request<AnnotationStats>(
      `/api/data-lab/annotations/stats${datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : ""}`
    ),
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
    body: {
      labels?: Record<string, unknown>;
      payload?: Record<string, unknown>;
      status?: string;
      comment?: string;
    }
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
  dataBankHub: () => request<DataBankHub>("/api/data-bank"),
  seedDataBank: () =>
    request<DataBankSeed>("/api/data-bank/seed", { method: "POST", body: JSON.stringify({}) }),
  dataBankSummary: (projectId: string) =>
    request<DataBankSummary>(`/api/projects/${projectId}/data-bank/summary`),
  listDataBank: (
    projectId: string,
    params?: { q?: string; asset_type?: string; source?: string; limit?: number }
  ) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.asset_type) qs.set("asset_type", params.asset_type);
    if (params?.source) qs.set("source", params.source);
    if (params?.limit) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<DataBankAsset[]>(`/api/projects/${projectId}/data-bank${suffix}`);
  },
  syncDataBank: (projectId: string) =>
    request<{ created: number; skipped: number; jobs_scanned: number }>(
      `/api/projects/${projectId}/data-bank/sync`,
      { method: "POST", body: JSON.stringify({}) }
    ),
  uploadDataBank: async (
    projectId: string,
    file: File,
    opts?: { name?: string; notes?: string; tags?: string }
  ) => {
    const token = getAccessToken();
    const form = new FormData();
    form.append("file", file);
    if (opts?.name) form.append("name", opts.name);
    if (opts?.notes) form.append("notes", opts.notes);
    if (opts?.tags) form.append("tags", opts.tags);
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/api/projects/${projectId}/data-bank/upload`, {
      method: "POST",
      headers,
      body: form,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(formatApiError(res.status, text));
    }
    return (await res.json()) as DataBankAsset;
  },
  deleteDataBankAsset: (projectId: string, assetId: string) =>
    request<DataBankAsset>(`/api/projects/${projectId}/data-bank/${assetId}`, {
      method: "DELETE",
    }),
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
  generateBankBuilding: (body?: {
    notes?: string;
    project_id?: string;
    prefer_external?: boolean;
  }) =>
    request<GenerationJob>("/api/studio/bank-building/generate", {
      method: "POST",
      body: JSON.stringify(body ?? {}),
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
      delivery_targets?: string[];
      variants?: string[];
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
  updateCinemaTimeline: (
    projectId: string,
    packageId: string,
    body: { music_gain_db?: number; voice_gain_db?: number; duck_music_under_vo?: boolean }
  ) =>
    request<CinemaPackage>(`/api/projects/${projectId}/cinema/packages/${packageId}/timeline`, {
      method: "PATCH",
      body: JSON.stringify(body),
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

  // Art City Edit
  editSummary: () => request<EditSummary>("/api/edit/summary"),
  editListPlans: () => request<EditPlan[]>("/api/edit/plans"),
  editSeedInternal: () =>
    request<EditWorkspace>("/api/edit/seed/internal", { method: "POST" }),
  editListWorkspaces: () => request<EditWorkspace[]>("/api/edit/workspaces"),
  editListOrganisations: () => request<EditOrganisation[]>("/api/edit/organisations"),
  editSubmitApplication: (body: {
    organisation_name: string;
    requested_plan_code?: string;
    use_case?: string;
    expected_monthly_minutes?: number;
    country?: string;
    website?: string;
    business_type?: string;
    billing_contact_email?: string;
    declarations_accepted: boolean;
  }) =>
    request<EditAccessApplication>("/api/edit/access-applications", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  editMyApplications: () =>
    request<EditAccessApplication[]>("/api/edit/access-applications/mine"),
  editListApplications: (state?: string) =>
    request<EditAccessApplication[]>(
      `/api/edit/access-applications${state ? `?state=${encodeURIComponent(state)}` : ""}`
    ),
  editReviewApplication: (
    applicationId: string,
    body: { action: string; reason?: string; plan_code?: string }
  ) =>
    request<EditAccessApplication>(`/api/edit/access-applications/${applicationId}/review`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  editActivateSubscription: (organisationId: string, planCode: string) =>
    request<EditSubscription>(`/api/edit/organisations/${organisationId}/activate`, {
      method: "POST",
      body: JSON.stringify({ plan_code: planCode, billing_method: "invoice" }),
    }),
  editUploadAsset: async (
    workspaceId: string,
    file: File,
    rightsAttested: boolean,
    rightsNotes?: string
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("rights_attested", String(rightsAttested));
    if (rightsNotes) form.append("rights_notes", rightsNotes);
    const token = getAccessToken();
    const res = await fetch(`${API_URL}/api/edit/workspaces/${workspaceId}/assets`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(detail || `Upload failed (${res.status})`);
    }
    return (await res.json()) as EditMediaAsset;
  },
  editListAssets: (workspaceId: string) =>
    request<EditMediaAsset[]>(`/api/edit/workspaces/${workspaceId}/assets`),
  editCreateProject: (
    workspaceId: string,
    body: {
      title: string;
      source_asset_id: string;
      brand_profile_version_id?: string;
      production_project_id?: string;
      objective?: string;
      brief?: Record<string, unknown>;
    }
  ) =>
    request<EditProject>(`/api/edit/workspaces/${workspaceId}/projects`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  editListProjects: (workspaceId: string) =>
    request<EditProject[]>(`/api/edit/workspaces/${workspaceId}/projects`),
  editGetProject: (projectId: string) =>
    request<EditProject>(`/api/edit/projects/${projectId}`),
  editStartAnalysis: (projectId: string) =>
    request<EditAnalysisJob>(`/api/edit/projects/${projectId}/analyse`, { method: "POST" }),
  editListCandidates: (projectId: string) =>
    request<EditCandidate[]>(`/api/edit/projects/${projectId}/candidates`),
  editCandidateDecision: (candidateId: string, decision: string) =>
    request<EditCandidate>(`/api/edit/candidates/${candidateId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }),
  editCreateTimeline: (projectId: string, candidateIds: string[], name?: string) =>
    request<EditTimelineVersion>(`/api/edit/projects/${projectId}/timelines`, {
      method: "POST",
      body: JSON.stringify({ candidate_ids: candidateIds, name }),
    }),
  editListTimelines: (projectId: string) =>
    request<EditTimelineVersion[]>(`/api/edit/projects/${projectId}/timelines`),
  editSubmitTimelineReview: (versionId: string) =>
    request<EditTimelineVersion>(`/api/edit/timelines/${versionId}/submit-review`, {
      method: "POST",
    }),
  editDecideTimeline: (
    versionId: string,
    decision: string,
    comments?: string
  ) =>
    request<EditTimelineVersion>(`/api/edit/timelines/${versionId}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision, comments }),
    }),
  editStartRender: (projectId: string, timelineVersionId: string, ratios?: string[]) =>
    request<EditRenderJob>(`/api/edit/projects/${projectId}/renders`, {
      method: "POST",
      body: JSON.stringify({
        timeline_version_id: timelineVersionId,
        ratios: ratios ?? ["9:16", "16:9", "4:5", "1:1"],
      }),
    }),
  editListRenders: (projectId: string) =>
    request<EditRenderJob[]>(`/api/edit/projects/${projectId}/renders`),
  editExportPackage: (renderJobId: string) =>
    request<Record<string, unknown>>(`/api/edit/renders/${renderJobId}/package`),
  editCreateBrand: (workspaceId: string, name: string, rules?: Record<string, unknown>) =>
    request<EditBrandProfile>(`/api/edit/workspaces/${workspaceId}/brands`, {
      method: "POST",
      body: JSON.stringify({ name, rules }),
    }),
  editListBrands: (workspaceId: string) =>
    request<EditBrandProfile[]>(`/api/edit/workspaces/${workspaceId}/brands`),
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
  mp4_url?: string | null;
  video_file?: string | null;
  audio_file?: string | null;
  file?: string | null;
  is_mp4?: boolean | null;
  mood?: string | null;
  variant?: string | null;
  script?: string | null;
  transcript?: AsrManifest | null;
  transcript_job_id?: string | null;
  subtitle_vtt?: string | null;
  subtitle_srt?: string | null;
};

export type CinemaTimelineClip = {
  id: string;
  track: string;
  role?: string;
  label?: string;
  start: number;
  end: number;
  job_id?: string;
  media_url?: string | null;
  mp4_url?: string | null;
  gain_db?: number;
  duck_music?: boolean;
};

export type CinemaTimeline = {
  duration_seconds: number;
  fps?: number;
  tracks?: { id: string; label: string }[];
  clips?: CinemaTimelineClip[];
  mix?: {
    music_gain_db?: number;
    voice_gain_db?: number;
    duck_music_under_vo?: boolean;
  };
  status?: string;
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
  delivery_targets?: { id?: string; label?: string; aspect?: string; channel?: string }[];
  variants?: { id: string; label?: string; primary?: boolean; music_style?: string; cta?: string }[];
  timeline?: CinemaTimeline | null;
  mix_master_path?: string | null;
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

export type EditSummary = {
  product: string;
  workspaces: number;
  projects: number;
  pending_applications: number;
  feature_flags: Record<string, boolean>;
};

export type EditPlan = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
  feature_flags: Record<string, unknown> | null;
  limits_json: Record<string, unknown> | null;
  price_usd_monthly: number | null;
};

export type EditWorkspace = {
  id: string;
  organisation_id: string;
  name: string;
  status: string;
  require_approval_before_export: boolean;
  created_at: string;
};

export type EditOrganisation = {
  id: string;
  legal_name: string;
  display_name: string;
  country: string | null;
  org_type: string;
  status: string;
  owner_user_id: string | null;
  website: string | null;
  ai_training_opt_in: boolean;
  created_at: string;
};

export type EditAccessApplication = {
  id: string;
  organisation_id: string | null;
  applicant_user_id: string;
  requested_plan_code: string;
  use_case: string | null;
  organisation_name: string;
  state: string;
  decision_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type EditSubscription = {
  id: string;
  organisation_id: string;
  plan_id: string;
  billing_method: string;
  status: string;
  created_at: string;
};

export type EditMediaAsset = {
  id: string;
  workspace_id: string;
  filename: string;
  storage_key: string;
  checksum: string;
  content_type: string | null;
  size_bytes: number;
  duration_seconds: number | null;
  rights_attested: boolean;
  rights_status: string;
  created_at: string;
};

export type EditProject = {
  id: string;
  workspace_id: string;
  title: string;
  objective: string | null;
  status: string;
  source_asset_id: string | null;
  brand_profile_version_id: string | null;
  production_project_id: string | null;
  brief_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type EditCandidate = {
  id: string;
  project_id: string;
  source_in: number;
  source_out: number;
  score: number;
  explanation: string | null;
  risks_json: unknown[] | null;
  user_decision: string;
  created_at: string;
};

export type EditAnalysisJob = {
  id: string;
  project_id: string;
  asset_id: string;
  job_type: string;
  state: string;
  cost_usd: number;
  created_at: string;
};

export type EditTimelineVersion = {
  id: string;
  project_id: string;
  version_number: number;
  name: string | null;
  edit_plan_json: Record<string, unknown> | null;
  transcript_json: Record<string, unknown> | null;
  status: string;
  created_at: string;
};

export type EditRenderJob = {
  id: string;
  project_id: string;
  timeline_version_id: string;
  preset: string;
  state: string;
  outputs_json: Record<string, unknown> | null;
  qc_json: Record<string, unknown> | null;
  cost_usd: number;
  created_at: string;
};

export type EditBrandProfile = {
  id: string;
  workspace_id: string;
  name: string;
  status: string;
  created_at: string;
};

export type HubFeatures = {
  script: boolean;
  storyboard: boolean;
  budget: boolean;
  call: boolean;
};

export type HubScript = {
  id: string;
  project_id: string;
  title: string;
  entry_mode: string;
  primary_locale: string;
  content_languages: string[] | null;
  current_version_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type HubScriptVersion = {
  id: string;
  script_id: string;
  project_id: string;
  version_label: string;
  status: string;
  page_eighths: number;
  locked_at: string | null;
  parent_version_id: string | null;
  created_at: string;
};

export type HubElement = {
  id: string;
  script_version_id: string;
  position: number;
  element_type: string;
  display_text: string;
  scene_id: string | null;
  character_id: string | null;
  locale: string | null;
  metadata_json: Record<string, unknown> | null;
};

export type HubScene = {
  id: string;
  script_version_id: string;
  scene_number: string;
  int_ext: string | null;
  location_name: string | null;
  time_of_day: string | null;
  heading_display: string | null;
  page_eighths: number;
  sort_order: number;
};

export type HubBreakdownItem = {
  id: string;
  scene_id: string;
  category: string;
  display_text: string;
  quantity: number | null;
  approval_status: string;
  source: string;
};

export const hubApi = {
  features: () => request<HubFeatures>("/api/v1/hub/features"),
  listScripts: (projectId: string) =>
    request<HubScript[]>(`/api/v1/hub/projects/${projectId}/scripts`),
  createScript: (
    projectId: string,
    body: {
      title: string;
      entry_mode?: string;
      primary_locale?: string;
      content_languages?: string[];
      seed_text?: string;
    },
  ) =>
    request<HubScript>(`/api/v1/hub/projects/${projectId}/scripts`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getScript: (scriptId: string) => request<HubScript>(`/api/v1/hub/scripts/${scriptId}`),
  listVersions: (scriptId: string) =>
    request<HubScriptVersion[]>(`/api/v1/hub/scripts/${scriptId}/versions`),
  newRevision: (scriptId: string) =>
    request<HubScriptVersion>(`/api/v1/hub/scripts/${scriptId}/versions`, { method: "POST" }),
  lockVersion: (versionId: string) =>
    request<HubScriptVersion>(`/api/v1/hub/versions/${versionId}/lock`, { method: "POST" }),
  listElements: (versionId: string) =>
    request<HubElement[]>(`/api/v1/hub/versions/${versionId}/elements`),
  saveElements: (versionId: string, elements: Partial<HubElement>[]) =>
    request<HubElement[]>(`/api/v1/hub/versions/${versionId}/elements`, {
      method: "PUT",
      body: JSON.stringify({ elements }),
    }),
  parseScenes: (versionId: string) =>
    request<HubScene[]>(`/api/v1/hub/versions/${versionId}/parse-scenes`, { method: "POST" }),
  listScenes: (versionId: string) =>
    request<HubScene[]>(`/api/v1/hub/versions/${versionId}/scenes`),
  proposeBreakdown: (versionId: string) =>
    request<HubBreakdownItem[]>(`/api/v1/hub/versions/${versionId}/breakdown/propose`, {
      method: "POST",
    }),
  listBreakdown: (versionId: string) =>
    request<HubBreakdownItem[]>(`/api/v1/hub/versions/${versionId}/breakdown`),
  decideBreakdown: (itemId: string, approval_status: "approved" | "rejected" | "proposed") =>
    request<HubBreakdownItem>(`/api/v1/hub/breakdown/${itemId}/decision`, {
      method: "POST",
      body: JSON.stringify({ approval_status }),
    }),
  compareVersions: (a: string, b: string) =>
    request<{ left: string[]; right: string[]; added: number; removed: number }>(
      `/api/v1/hub/versions/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`,
    ),
  aiCommand: (
    versionId: string,
    body: { command: string; target_locale?: string; element_ids?: string[]; apply?: boolean },
  ) =>
    request<{ provider: string; elements: Partial<HubElement>[]; apply: boolean }>(
      `/api/v1/hub/versions/${versionId}/ai`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  exportUrl: (versionId: string, fmt: "pdf" | "docx") =>
    `${API_URL}/api/v1/hub/versions/${versionId}/export/${fmt}`,
  handoff: (projectId: string, target: "cinema" | "studio" | "edit", body?: object) =>
    request<{ ok: boolean; redirect: string; asset_id: string }>(
      `/api/v1/hub/projects/${projectId}/handoff/${target}`,
      { method: "POST", body: JSON.stringify(body || {}) },
    ),
  listStale: (projectId: string) =>
    request<{ id: string; resource_type: string; resource_id: string; reason: string }[]>(
      `/api/v1/hub/projects/${projectId}/stale`,
    ),
};

export type VdProject = {
  id: string;
  vd_project_id: string;
  project_id: string;
  title: string;
  logline?: string | null;
  primary_locale: string;
  status: string;
  ip_title?: { id: string; title: string; status: string } | null;
};

export const vdApi = {
  features: () => request<{ enabled: boolean }>(`/api/v1/vertical-drama/features`),
  list: () => request<VdProject[]>(`/api/v1/vertical-drama/projects`),
  create: (body: object) =>
    request<VdProject>(`/api/v1/vertical-drama/projects`, { method: "POST", body: JSON.stringify(body) }),
  get: (vdId: string) => request<VdProject>(`/api/v1/vertical-drama/projects/${vdId}`),
  byPlatform: (projectId: string) =>
    request<VdProject>(`/api/v1/vertical-drama/projects/by-platform/${projectId}`),
  rights: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/rights`),
  addRights: (vdId: string, body: object) =>
    request(`/api/v1/vertical-drama/projects/${vdId}/rights`, { method: "POST", body: JSON.stringify(body) }),
  contributors: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/contributors`),
  addContributor: (vdId: string, body: object) =>
    request(`/api/v1/vertical-drama/projects/${vdId}/contributors`, { method: "POST", body: JSON.stringify(body) }),
  provenance: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/provenance`),
  characters: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/characters`),
  addCharacter: (vdId: string, body: object) =>
    request(`/api/v1/vertical-drama/projects/${vdId}/characters`, { method: "POST", body: JSON.stringify(body) }),
  locations: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/locations`),
  addLocation: (vdId: string, body: object) =>
    request(`/api/v1/vertical-drama/projects/${vdId}/locations`, { method: "POST", body: JSON.stringify(body) }),
  props: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/props`),
  canon: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/canon`),
  addCanon: (vdId: string, body: object) =>
    request(`/api/v1/vertical-drama/projects/${vdId}/canon`, { method: "POST", body: JSON.stringify(body) }),
  approveCanon: (id: string) => request(`/api/v1/vertical-drama/canon/${id}/approve`, { method: "POST" }),
  bible: (vdId: string) => request<Record<string, unknown>>(`/api/v1/vertical-drama/projects/${vdId}/story-bible`),
  saveBible: (vdId: string, sections_json: object) =>
    request(`/api/v1/vertical-drama/projects/${vdId}/story-bible`, {
      method: "POST",
      body: JSON.stringify({ sections_json }),
    }),
  approveBible: (versionId: string) =>
    request(`/api/v1/vertical-drama/story-bibles/${versionId}/approve`, { method: "POST" }),
  seasons: (vdId: string) => request<Record<string, unknown>[]>(`/api/v1/vertical-drama/projects/${vdId}/seasons`),
  createSeason: (vdId: string, body: object) =>
    request(`/api/v1/vertical-drama/projects/${vdId}/seasons`, { method: "POST", body: JSON.stringify(body) }),
  episode: (id: string) => request<Record<string, unknown>>(`/api/v1/vertical-drama/episodes/${id}`),
  patchEpisode: (id: string, body: object) =>
    request(`/api/v1/vertical-drama/episodes/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  saveScreenplay: (id: string, body: object) =>
    request(`/api/v1/vertical-drama/episodes/${id}/screenplay`, { method: "POST", body: JSON.stringify(body) }),
  decoupage: (id: string) =>
    request(`/api/v1/vertical-drama/episodes/${id}/decoupage`, { method: "POST" }),
  generateShot: (shotId: string) =>
    request(`/api/v1/vertical-drama/shots/${shotId}/generations`, { method: "POST", body: JSON.stringify({}) }),
  assemble: (id: string) => request(`/api/v1/vertical-drama/episodes/${id}/assembly`, { method: "POST" }),
  qc: (id: string) => request(`/api/v1/vertical-drama/episodes/${id}/qc-runs`, { method: "POST" }),
  localize: (id: string, body: object) =>
    request(`/api/v1/vertical-drama/episodes/${id}/localize`, { method: "POST", body: JSON.stringify(body) }),
  listLocalize: (id: string) => request(`/api/v1/vertical-drama/episodes/${id}/localize`),
  delivery: (id: string) =>
    request(`/api/v1/vertical-drama/episodes/${id}/delivery-packages`, { method: "POST" }),
};
