import type {
  AnalysisJob,
  CreateAnalysisRequest,
  PatchReviewRequest,
  PatchReviewResponse,
} from "../types/api";
import type { AnalysisReport, TraceFinding } from "../types/report";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
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

export function createAnalysis(payload: CreateAnalysisRequest): Promise<AnalysisJob> {
  return requestJson<AnalysisJob>("/api/analyses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
