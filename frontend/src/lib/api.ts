import type {
  AnalysisJob,
  CreateAnalysisRequest,
  PatchFindingReviewRequest,
  PatchFindingReviewResponse,
  PatchReviewRequest,
  PatchReviewResponse,
} from "../types/api";
import type { AnalysisReport, TraceFinding } from "../types/report";

function persistedApiToken(): string {
  try {
    const raw = window.localStorage.getItem("sca_settings_v1");
    if (!raw) return "";
    const parsed = JSON.parse(raw) as {
      state?: { settings?: { apiToken?: unknown } };
    };
    const token = parsed.state?.settings?.apiToken;
    return typeof token === "string" ? token.trim() : "";
  } catch {
    return "";
  }
}

function authorizationHeader(apiToken?: string): Record<string, string> {
  const token = (apiToken ?? persistedApiToken()).trim();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
  apiToken?: string,
): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...authorizationHeader(apiToken),
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function createAnalysis(
  payload: CreateAnalysisRequest,
  apiToken?: string,
): Promise<AnalysisJob> {
  return requestJson<AnalysisJob>("/api/analyses", {
    method: "POST",
    body: JSON.stringify(payload),
  }, apiToken);
}

export function getAnalysis(analysisId: string): Promise<AnalysisJob> {
  return requestJson<AnalysisJob>(`/api/analyses/${analysisId}`);
}

export function getReport(contractId: string): Promise<AnalysisReport> {
  return requestJson<AnalysisReport>(`/api/reports/${contractId}`);
}

export function getTrace(traceId: string, findingId?: string): Promise<TraceFinding[]> {
  const params = findingId ? `?finding_id=${encodeURIComponent(findingId)}` : "";
  return requestJson<TraceFinding[]>(`/api/traces/${traceId}${params}`);
}

export function patchReviewStatus(
  contractId: string,
  payload: PatchReviewRequest,
): Promise<PatchReviewResponse> {
  return requestJson<PatchReviewResponse>(`/api/reports/${contractId}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function patchFindingReview(
  contractId: string,
  findingId: string,
  payload: PatchFindingReviewRequest,
): Promise<PatchFindingReviewResponse> {
  return requestJson<PatchFindingReviewResponse>(
    `/api/reports/${contractId}/findings/${findingId}/review`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}
