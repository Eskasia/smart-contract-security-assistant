import type {
  AnalysisJob,
  CreateAnalysisRequest,
  CreateImportRequest,
  ImportResult,
  PatchFindingReviewRequest,
  PatchFindingReviewResponse,
  PatchReviewRequest,
  PatchReviewResponse,
} from "../types/api";
import type { AnalysisReport, TraceFinding } from "../types/report";

const statusMessages: Record<number, string> = {
  400: "Bad request.",
  401: "Authentication failed.",
  403: "Access denied.",
  404: "Resource not found.",
  413: "Request too large.",
  422: "Request validation failed.",
  500: "Server error.",
};

export class ApiRequestError extends Error {
  readonly status: number;

  constructor(status: number) {
    super(`HTTP ${status}: ${statusMessages[status] ?? "Request failed."}`);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

function authorizationHeader(apiToken?: string): Record<string, string> {
  const token = (apiToken ?? "").trim();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
  apiToken?: string,
): Promise<T> {
  const body = init?.body;
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const response = await fetch(path, {
    headers: {
      ...authorizationHeader(apiToken),
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status);
  }

  return response.json() as Promise<T>;
}

async function requestText(
  path: string,
  init?: RequestInit,
  apiToken?: string,
): Promise<string> {
  const response = await fetch(path, {
    headers: {
      ...authorizationHeader(apiToken),
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status);
  }

  return response.text();
}

function pathSegment(value: string): string {
  return encodeURIComponent(value);
}

export function createAnalysis(
  payload: CreateAnalysisRequest,
  apiToken?: string,
): Promise<AnalysisJob> {
  return requestJson<AnalysisJob>(
    "/api/analyses",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    apiToken,
  );
}

export function createImport(
  payload: CreateImportRequest,
  apiToken?: string,
): Promise<ImportResult> {
  return requestJson<ImportResult>(
    "/api/imports",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    apiToken,
  );
}

export function getAnalysis(analysisId: string, apiToken?: string): Promise<AnalysisJob> {
  return requestJson<AnalysisJob>(
    `/api/analyses/${pathSegment(analysisId)}`,
    undefined,
    apiToken,
  );
}

export function getReport(contractId: string, apiToken?: string): Promise<AnalysisReport> {
  return requestJson<AnalysisReport>(
    `/api/reports/${pathSegment(contractId)}`,
    undefined,
    apiToken,
  );
}

export function getReportMarkdown(contractId: string, apiToken?: string): Promise<string> {
  return requestText(
    `/api/reports/${pathSegment(contractId)}/markdown`,
    undefined,
    apiToken,
  );
}

export function getTrace(
  traceId: string,
  findingId?: string,
  apiToken?: string,
): Promise<TraceFinding[]> {
  const params = findingId ? `?finding_id=${encodeURIComponent(findingId)}` : "";
  return requestJson<TraceFinding[]>(
    `/api/traces/${pathSegment(traceId)}${params}`,
    undefined,
    apiToken,
  );
}

export function patchReviewStatus(
  contractId: string,
  payload: PatchReviewRequest,
  apiToken?: string,
): Promise<PatchReviewResponse> {
  return requestJson<PatchReviewResponse>(
    `/api/reports/${pathSegment(contractId)}/review`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    apiToken,
  );
}

export function patchFindingReview(
  contractId: string,
  findingId: string,
  payload: PatchFindingReviewRequest,
  apiToken?: string,
): Promise<PatchFindingReviewResponse> {
  return requestJson<PatchFindingReviewResponse>(
    `/api/reports/${pathSegment(contractId)}/findings/${pathSegment(findingId)}/review`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    apiToken,
  );
}
