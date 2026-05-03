import type { AnalysisReport, AnalysisStatus, Finding, RagMode, ReviewStatus } from "./report";

export interface CreateAnalysisRequest {
  input_path: string;
  rag_mode: RagMode;
  dataset_chunks: string;
  model_path: string | null;
}

export interface AnalysisJob {
  analysis_id: string;
  status: AnalysisStatus;
  message?: string;
  report_id?: string;
  contract_id?: string;
}

export type AnalysisEvent =
  | { type: "status"; status: AnalysisStatus; message?: string }
  | { type: "finding_token"; finding_id: string; token: string }
  | { type: "finding_complete"; finding: Finding }
  | { type: "done"; status?: AnalysisStatus; report_id: string; contract_id?: string }
  | { type: "error"; status: "error"; message: string };

export interface PatchReviewRequest {
  review_status: ReviewStatus;
}

export interface PatchReviewResponse {
  report: AnalysisReport;
}
