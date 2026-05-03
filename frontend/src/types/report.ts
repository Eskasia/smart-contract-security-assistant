export type AnalysisStatus =
  | "queued"
  | "running"
  | "finding"
  | "no_finding"
  | "partial_analysis"
  | "error";

export type ReviewStatus = "pending_human_review" | "approved" | "rejected" | "blocked";

export type RagMode = "quality" | "balanced" | "fast" | "fallback";

export interface Location {
  file: string;
  function: string | null;
  line_start: number;
  line_end: number;
}

export interface Finding {
  finding_id: string;
  vulnerability_type: string;
  severity: number;
  location: Location;
  evidence: string;
  reference: string[];
  finding_confidence: number;
  explanation_confidence: number;
  explanation: string;
  attack_path: string;
  fix_suggestion: string;
  remediation_code?: string;
  vulnerable_code?: string;
  static_tool_source: string;
  detector_name: string;
  partial: boolean;
  local_judge_score?: number;
  external_judge_score?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}

export interface AnalysisMetadata {
  dataset_version: string;
  model_version: string;
  solc_version: string | null;
  slither_version: string | null;
  partial_analysis: boolean;
  analysis_trace_id: string;
  context_tokens_used: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  local_average_judge_score?: number;
  external_average_judge_score?: number;
  rag_mode: RagMode | string;
  total_duration_ms: number;
  input_kind?: string;
  project_type?: string;
  entry_path?: string;
  project_root?: string;
  source_files_count?: number;
  errors: string[];
}

export interface AnalysisReport {
  report_version?: string;
  overall_status: AnalysisStatus;
  contract_id: string;
  review_status: ReviewStatus;
  requires_human_review: boolean;
  business_logic_review_required: boolean;
  review_reason: string;
  findings: Finding[];
  analysis_metadata: AnalysisMetadata;
}

export interface TraceFinding {
  trace_id: string;
  finding_id: string;
  detector_name: string | null;
  rag_mode: string;
  retrieval_duration_ms: number;
  llm_duration_ms: number;
  chunks_used: number;
  slither_raw: string | null;
  normalized_finding: string | null;
  rag_chunk_ids: string | null;
  packed_prompt: string;
  llm_raw_output: string | null;
  schema_valid: boolean | number;
  retry_count: number;
  partial: boolean | number;
}

export interface UserSettings {
  inputMode: "file" | "project";
  inputPath: string;
  ragMode: RagMode;
  datasetChunks: string;
  modelPath: string;
  diffMode: "inline" | "split";
  leftColumnWidth: number;
  locale: "zh" | "en";
}
