export type AnalysisStatus =
  | "queued"
  | "running"
  | "finding"
  | "no_finding"
  | "partial_analysis"
  | "error";

export type ReviewStatus = "pending_human_review" | "approved" | "rejected" | "blocked";

export type FindingReviewStatus =
  | "unreviewed"
  | "true_positive"
  | "false_positive"
  | "accepted_risk"
  | "fixed";

export type RagMode = "quality" | "balanced" | "fast" | "fallback";
export type NativeBuildPolicy = "trusted" | "disabled";
export type ExternalToolName = "aderyn" | "echidna" | "medusa" | "halmos";
export type EtherscanExplorerHost =
  | "api.etherscan.io"
  | "api-sepolia.etherscan.io";
export type ImportSourceType =
  | "local"
  | "github_archive"
  | "etherscan_api"
  | "zip_base64";

export interface ZeroGProof {
  storage_root_hash: string;
  storage_tx_hash: string;
  registry_address: string;
  registry_tx_hash: string;
  explorer_links: {
    storage_tx?: string;
    registry?: string;
    registration_tx?: string;
  };
}

export interface Location {
  file: string;
  function: string | null;
  line_start: number;
  line_end: number;
}

export interface StandardRef {
  standard: string;
  id: string;
  label: string;
  confidence: string;
}

export interface EvidenceClaim {
  claim_id: string;
  finding_id?: string;
  claim_text?: string;
  text?: string;
  support_node_ids?: string[];
  groundedness_status: "supported" | "partially_supported" | "unsupported" | "contradicted" | string;
}

export interface NativeRuleResult {
  rule_id: string;
  status: string;
  confidence_delta?: number;
  summary?: string;
  evidence_nodes?: string[];
  confidence_breakdown?: Record<string, number>;
}

export interface EvidenceGraph {
  nodes_path?: string;
  edges_path?: string;
  claims_path?: string;
  root_finding_node_id?: string;
  source_nodes?: string[];
  tool_signal_nodes?: string[];
  rag_chunk_nodes?: string[];
  claim_nodes?: string[];
  rule_nodes?: string[];
  advanced_nodes?: string[];
  standard_nodes?: string[];
  claims?: EvidenceClaim[];
  rule_results?: NativeRuleResult[];
  unsupported_security_claims?: number;
  groundedness_status?: string;
}

export interface ExploitValidation {
  validation_id?: string;
  status: string;
  mode: string;
  poc_artifact_path?: string | null;
  test_framework?: string | null;
  triggered?: boolean | null;
  profit_delta?: Record<string, string> | null;
  asset_delta?: Record<string, string>[];
  transaction_sequence?: string[];
  execution_log_path?: string | null;
  human_review_required: boolean;
  safety_notes: string[];
  supported_by: string[];
}

export interface FuzzSeedSuggestion {
  finding_id: string;
  seed_id: string;
  target_function: string;
  preconditions?: string[];
  sequence?: Record<string, string>[];
  expected_signal?: string;
  status?: string;
  supported_by: string[];
}

export interface FormalPropertySuggestion {
  property_id: string;
  finding_id: string;
  format: string;
  status: "draft" | string;
  property_text?: string;
  compile_status?: string;
  verification_status: string;
  supported_by: string[];
  review_notes?: string;
}

export interface DefiProfitSignal {
  status: string;
  asset_flow?: Record<string, string>[];
  oracle_dependency?: string | null;
  flash_loan_dependency?: boolean;
  profitability_status?: string;
  supported_by?: string[];
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
  review_status?: FindingReviewStatus;
  review_note?: string;
  standard_refs?: StandardRef[];
  evidence_graph?: EvidenceGraph;
  native_rule_results?: NativeRuleResult[];
  exploit_validation?: ExploitValidation;
  fuzz_seed_suggestions?: FuzzSeedSuggestion[];
  formal_property_suggestions?: FormalPropertySuggestion[];
  defi_profit_signal?: DefiProfitSignal;
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
  zero_g_proof?: ZeroGProof;
  errors: string[];
}

export interface ExternalToolResult {
  tool_name: string;
  command: string[];
  status: "finding" | "passed" | "skipped" | "error" | string;
  findings_count: number;
  summary: string;
  output_path?: string;
  artifact_paths?: Record<string, string>;
  error?: string;
  duration_ms?: number;
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
  security_score?: number;
  score_formula_version?: string;
  score_factors?: Record<string, unknown>;
  external_tool_results?: ExternalToolResult[];
  evidence_graph_summary?: Record<string, unknown>;
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
  packed_prompt: string | null;
  llm_raw_output: string | null;
  schema_valid: boolean | number;
  retry_count: number;
  partial: boolean | number;
  review_status?: FindingReviewStatus;
  review_note?: string;
}

export interface UserSettings {
  inputMode: "file" | "project";
  inputPath: string;
  importSourceType: ImportSourceType;
  importSourceValue: string;
  importExplorerHost: EtherscanExplorerHost;
  ragMode: RagMode;
  datasetChunks: string;
  modelPath: string;
  nativeBuildPolicy: NativeBuildPolicy;
  externalTools: ExternalToolName[];
  externalTimeoutSeconds: number;
  apiToken: string;
  diffMode: "inline" | "split";
  leftColumnWidth: number;
  locale: "zh" | "en";
}
