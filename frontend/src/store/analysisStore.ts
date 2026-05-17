import { create } from "zustand";
import { persist } from "zustand/middleware";

import { demoReport, demoTrace } from "../data/demoReport";
import type { AnalysisJob } from "../types/api";
import type {
  AnalysisReport,
  FindingReviewStatus,
  ReviewStatus,
  TraceFinding,
  UserSettings,
} from "../types/report";

export type ConnectionMode = "sse" | "polling" | "demo";

interface AnalysisState {
  job: AnalysisJob | null;
  report: AnalysisReport;
  selectedFindingId: string;
  traceRows: TraceFinding[];
  connectionMode: ConnectionMode;
  streamTextByFinding: Record<string, string>;
  analysisError: string;
  setJob: (job: AnalysisJob | null) => void;
  startAnalysis: (job: AnalysisJob, connectionMode: ConnectionMode) => void;
  startRouteLoad: (contractId: string) => void;
  setReport: (report: AnalysisReport, preferredFindingId?: string) => void;
  setSelectedFindingId: (findingId: string) => void;
  setTraceRows: (rows: TraceFinding[]) => void;
  setConnectionMode: (mode: ConnectionMode) => void;
  setAnalysisError: (message: string) => void;
  appendFindingToken: (findingId: string, token: string) => void;
  updateReviewStatus: (status: ReviewStatus) => void;
  updateFindingReview: (
    findingId: string,
    status: FindingReviewStatus,
    note: string,
  ) => void;
  loadDemo: () => void;
}

function emptyReport(
  contractId: string,
  status: AnalysisReport["overall_status"],
  reviewReason: string,
): AnalysisReport {
  return {
    report_version: "1.0",
    overall_status: status,
    contract_id: contractId,
    review_status: "pending_human_review",
    requires_human_review: true,
    business_logic_review_required: false,
    review_reason: reviewReason,
    findings: [],
    analysis_metadata: {
      dataset_version: "",
      model_version: "",
      solc_version: null,
      slither_version: null,
      partial_analysis: false,
      analysis_trace_id: "",
      context_tokens_used: 0,
      rag_mode: "fallback",
      total_duration_ms: 0,
      errors: [],
    },
    security_score: 100,
    score_formula_version: "security_score_v2",
    score_factors: {},
    external_tool_results: [],
  };
}

function pendingReport(job: AnalysisJob): AnalysisReport {
  return emptyReport(
    job.contract_id ?? job.report_id ?? job.analysis_id,
    job.status,
    "Analysis is running.",
  );
}

function isPendingReport(report: AnalysisReport): boolean {
  return (
    report.findings.length === 0 &&
    (report.overall_status === "queued" || report.overall_status === "running")
  );
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  job: {
    analysis_id: "demo-analysis",
    status: demoReport.overall_status,
    contract_id: demoReport.contract_id,
    report_id: demoReport.contract_id,
  },
  report: demoReport,
  selectedFindingId: demoReport.findings[0]?.finding_id ?? "",
  traceRows: demoTrace,
  connectionMode: "demo",
  streamTextByFinding: {},
  analysisError: "",
  setJob: (job) =>
    set((state) => {
      if (!job || !isPendingReport(state.report)) return { job };
      return {
        job,
        report: {
          ...state.report,
          overall_status: job.status,
          contract_id: job.contract_id ?? job.report_id ?? state.report.contract_id,
          review_reason: job.message ?? state.report.review_reason,
        },
      };
    }),
  startAnalysis: (job, connectionMode) =>
    set({
      job,
      report: pendingReport(job),
      selectedFindingId: "",
      traceRows: [],
      connectionMode,
      streamTextByFinding: {},
      analysisError: "",
    }),
  startRouteLoad: (contractId) =>
    set({
      job: null,
      report: emptyReport(contractId, "queued", "Report is loading."),
      selectedFindingId: "",
      traceRows: [],
      connectionMode: "polling",
      streamTextByFinding: {},
      analysisError: "",
    }),
  setReport: (report, preferredFindingId) =>
    set((state) => ({
      job: state.job
        ? {
            ...state.job,
            status: report.overall_status,
            contract_id: report.contract_id,
            report_id: report.contract_id,
          }
        : state.job,
      report,
      selectedFindingId:
        report.findings.find((finding) => finding.finding_id === preferredFindingId)
          ?.finding_id ??
        report.findings.find((finding) => finding.finding_id === state.selectedFindingId)
          ?.finding_id ??
        report.findings[0]?.finding_id ??
        "",
      streamTextByFinding: {},
      analysisError: "",
    })),
  setSelectedFindingId: (findingId) => set({ selectedFindingId: findingId }),
  setTraceRows: (traceRows) => set({ traceRows }),
  setConnectionMode: (connectionMode) => set({ connectionMode }),
  setAnalysisError: (analysisError) => set({ analysisError }),
  appendFindingToken: (findingId, token) =>
    set((state) => ({
      streamTextByFinding: {
        ...state.streamTextByFinding,
        [findingId]: `${state.streamTextByFinding[findingId] ?? ""}${token}`,
      },
    })),
  updateReviewStatus: (reviewStatus) =>
    set((state) => ({ report: { ...state.report, review_status: reviewStatus } })),
  updateFindingReview: (findingId, reviewStatus, reviewNote) =>
    set((state) => ({
      report: {
        ...state.report,
        findings: state.report.findings.map((finding) =>
          finding.finding_id === findingId
            ? {
                ...finding,
                review_status: reviewStatus,
                review_note: reviewNote,
              }
            : finding,
        ),
      },
    })),
  loadDemo: () =>
    set({
      job: {
        analysis_id: "demo-analysis",
        status: demoReport.overall_status,
        contract_id: demoReport.contract_id,
        report_id: demoReport.contract_id,
      },
      report: demoReport,
      selectedFindingId: demoReport.findings[0]?.finding_id ?? "",
      traceRows: demoTrace,
      connectionMode: "demo",
      streamTextByFinding: {},
      analysisError: "",
    }),
}));

interface SettingsState {
  settings: UserSettings;
  updateSettings: (patch: Partial<UserSettings>) => void;
}

export const defaultSettings: UserSettings = {
  inputMode: "file",
  inputPath: "tests/contracts/VulnerableVault.sol",
  importSourceType: "local",
  importSourceValue: "",
  importExplorerHost: "api.etherscan.io",
  ragMode: "fallback",
  datasetChunks: "data/dataset_v1.0/chunks/chunks.jsonl",
  modelPath: "",
  nativeBuildPolicy: "disabled",
  echidnaEnabled: false,
  externalTimeoutSeconds: 60,
  apiToken: "",
  diffMode: "inline",
  leftColumnWidth: 280,
  locale: "zh",
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      updateSettings: (patch) =>
        set((state) => ({
          settings: { ...state.settings, ...patch },
        })),
    }),
    {
      name: "sca_settings_v1",
      partialize: (state) => {
        const { apiToken: _apiToken, ...persistedSettings } = state.settings;
        return { settings: persistedSettings };
      },
      merge: (persisted, current) => {
        const persistedSettings =
          typeof persisted === "object" && persisted !== null && "settings" in persisted
            ? (persisted as Partial<SettingsState>).settings
            : undefined;
        const { apiToken: _apiToken, ...safePersistedSettings } = persistedSettings ?? {};
        return {
          ...current,
          settings: {
            ...defaultSettings,
            ...safePersistedSettings,
            apiToken: current.settings.apiToken,
          },
        };
      },
    },
  ),
);
