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
  setJob: (job: AnalysisJob | null) => void;
  setReport: (report: AnalysisReport) => void;
  setSelectedFindingId: (findingId: string) => void;
  setTraceRows: (rows: TraceFinding[]) => void;
  setConnectionMode: (mode: ConnectionMode) => void;
  appendFindingToken: (findingId: string, token: string) => void;
  updateReviewStatus: (status: ReviewStatus) => void;
  updateFindingReview: (
    findingId: string,
    status: FindingReviewStatus,
    note: string,
  ) => void;
  loadDemo: () => void;
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
  setJob: (job) => set({ job }),
  setReport: (report) =>
    set((state) => ({
      report,
      selectedFindingId:
        report.findings.find((finding) => finding.finding_id === state.selectedFindingId)
          ?.finding_id ??
        report.findings[0]?.finding_id ??
        "",
    })),
  setSelectedFindingId: (findingId) => set({ selectedFindingId: findingId }),
  setTraceRows: (traceRows) => set({ traceRows }),
  setConnectionMode: (connectionMode) => set({ connectionMode }),
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
    }),
}));

interface SettingsState {
  settings: UserSettings;
  updateSettings: (patch: Partial<UserSettings>) => void;
}

export const defaultSettings: UserSettings = {
  inputMode: "file",
  inputPath: "tests/contracts/VulnerableVault.sol",
  ragMode: "fallback",
  datasetChunks: "data/dataset_v1.0/chunks/chunks.jsonl",
  modelPath: "",
  nativeBuildPolicy: "disabled",
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
      partialize: (state) => ({ settings: state.settings }),
      merge: (persisted, current) => {
        const persistedSettings =
          typeof persisted === "object" && persisted !== null && "settings" in persisted
            ? (persisted as Partial<SettingsState>).settings
            : undefined;
        return {
          ...current,
          settings: {
            ...defaultSettings,
            ...persistedSettings,
          },
        };
      },
    },
  ),
);
