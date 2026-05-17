import type {
  AnalysisReport,
  AnalysisStatus,
  EtherscanExplorerHost,
  ExternalToolName,
  Finding,
  FindingReviewStatus,
  NativeBuildPolicy,
  RagMode,
  ReviewStatus,
} from "./report";

export interface CreateAnalysisRequest {
  input_path: string;
  rag_mode: RagMode;
  dataset_chunks: string;
  model_path: string | null;
  native_build_policy: NativeBuildPolicy;
  external_tools?: ExternalToolName[];
  external_timeout_seconds?: number;
}

export type CreateImportRequest =
  | {
      source_kind: "github_archive";
      repository: string;
    }
  | {
      source_kind: "etherscan_api";
      contract_address: string;
      explorer_host: EtherscanExplorerHost;
      api_key?: string;
    }
  | {
      source_kind: "zip_base64";
      archive_base64: string;
      archive_name?: string;
    };

export interface ImportResult {
  input_path: string;
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

export interface PatchFindingReviewRequest {
  review_status: FindingReviewStatus;
  review_note?: string;
}

export interface PatchFindingReviewResponse {
  report: AnalysisReport;
  finding: Finding;
}
