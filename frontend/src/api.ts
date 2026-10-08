const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${base}/api${path}`, init);
  if (!r.ok) {
    throw new Error(`Request failed (${r.status})`);
  }
  return r.json() as Promise<T>;
}

export type Brand = {
  id: string;
  name: string;
  slug?: string;
  description?: string | null;
  official_domain?: string | null;
  logo_url?: string | null;
  status?: string;
  created_at?: string;
  updated_at?: string;
};

export type OfficialSocial = {
  id: string;
  brand_id?: string;
  platform: string;
  handle: string;
  display_name?: string | null;
  verified: boolean;
  profile_url: string;
  description?: string | null;
  status?: string;
};

export type OfficialApp = {
  id: string;
  brand_id?: string;
  platform: string;
  app_name: string;
  developer_name: string;
  developer_identifier?: string | null;
  package_identifier: string;
  store_url: string;
  description?: string | null;
  logo_url?: string | null;
  status?: string;
};

export type BrandAsset = {
  id: string;
  brand_id?: string;
  asset_type: string;
  value: string;
  label?: string | null;
};

export type Threat = {
  id: string;
  name: string;
  source: string;
  publisher?: string | null;
  threat_type: string | null;
  risk_score: number;
  severity: string;
  status: string;
  detected_at: string;
};

export type Overview = {
  brand: Brand;
  summary: Record<string, number>;
  risk_distribution: { severity: string; count: number }[];
  source_distribution: { source: string; count: number }[];
  threat_type_distribution: { threat_type: string; count: number }[];
  recent_threats: Threat[];
  last_scan: {
    id?: string;
    status?: string;
    completed_at: string | null;
    candidate_count: number;
  } | null;
};

export type EvidenceSignal = {
  signal_type: string;
  available: boolean;
  score: number | null;
  priority?: number;
  details: Record<string, unknown>;
};

export type DetectionCandidate = {
  name: string;
  source: string;
  handle?: string | null;
  publisher?: string | null;
  store_url?: string | null;
  profile_url?: string | null;
  description?: string | null;
  package_identifier?: string | null;
  developer_identifier?: string | null;
};

export type Detection = {
  id: string;
  brand_id?: string;
  candidate_type?: string;
  candidate_id?: string;
  risk_score: number;
  severity: string;
  threat_type: string | null;
  status: string;
  confidence?: number;
  official_match?: boolean;
  lookalike_detected?: boolean;
  detected_at: string;
  candidate: DetectionCandidate;
  evidence: EvidenceSignal[];
};

export type Note = {
  id: string;
  content: string;
  actor: string;
  created_at: string;
};

export type Activity = {
  id: string;
  event_type: string;
  previous_value: string | null;
  new_value: string | null;
  details: Record<string, unknown>;
  actor: string;
  created_at: string;
};

export type Draft = {
  id: string;
  draft_type: string;
  content: string;
  evidence_summary: string[];
  actor: string;
  created_at: string;
};

export type Investigation = {
  detection_id: string;
  status: string;
  notes: Note[];
  activity: Activity[];
  drafts: Draft[];
};

export type AnalystEvidence = {
  signal_type: string;
  summary: string;
  score: number | null;
  details: Record<string, unknown>;
};

export type AnalystAnalysis = {
  summary: string;
  risk_rationale: string;
  key_evidence: AnalystEvidence[];
  uncertainties: string[];
  recommended_actions: string[];
  confidence: string;
  source_facts: {
    risk_score: number;
    severity: string;
    candidate_name: string;
    [key: string]: unknown;
  };
  generated_at: string;
  provider: string;
};

export type MonitoringRun = {
  id: string;
  brand_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  candidate_count: number;
  social_candidate_count: number;
  app_candidate_count: number;
  safe_count: number;
  low_count: number;
  medium_count: number;
  high_count: number;
  critical_count: number;
  created_at: string;
};

const post = <T>(path: string, body: unknown) =>
  request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const api = {
  brands: () => request<Brand[]>("/brands"),
  brand: (id: string) => request<Brand>(`/brands/${id}`),
  brandSocial: (id: string) => request<OfficialSocial[]>(`/brands/${id}/social-accounts`),
  brandApps: (id: string) => request<OfficialApp[]>(`/brands/${id}/apps`),
  brandAssets: (id: string) => request<BrandAsset[]>(`/brands/${id}/assets`),
  overview: (id: string) => request<Overview>(`/dashboard/overview?brand_id=${id}`),
  scan: (id: string) => post<MonitoringRun>("/monitoring/scan", { brand_id: id }),
  detections: () => request<Detection[]>("/detections"),
  detection: (id: string) => request<Detection>(`/detections/${id}`),
  investigation: (id: string) => request<Investigation>(`/detections/${id}/investigation`),
  status: (id: string, status: string) => post<Investigation>(`/detections/${id}/status`, { status }),
  note: (id: string, content: string) => post<Investigation>(`/detections/${id}/notes`, { content }),
  draft: (id: string, draft_type: string) => post<Draft>(`/detections/${id}/remediation-drafts`, { draft_type }),
  analyze: (id: string) => post<AnalystAnalysis>(`/detections/${id}/analyze`, {}),
};
