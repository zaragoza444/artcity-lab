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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/health"),
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
    `${API_URL}/api/projects/${projectId}/cinema/packages/${packageId}/zip`,
  cinemaManifestUrl: (projectId: string, packageId: string) =>
    `${API_URL}/api/projects/${projectId}/cinema/packages/${packageId}/manifest`,
  cinemaValidationUrl: (projectId: string, packageId: string) =>
    `${API_URL}/api/projects/${projectId}/cinema/packages/${packageId}/validation`,
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
