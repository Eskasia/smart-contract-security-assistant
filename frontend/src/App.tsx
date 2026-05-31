import { useEffect, useLayoutEffect, useState } from "react";
import { BrowserRouter, Route, Routes, useParams, useSearchParams } from "react-router-dom";

import { FindingList } from "./components/FindingList";
import { InputPanel } from "./components/InputPanel";
import { ReportHeader } from "./components/ReportHeader";
import { RightRail } from "./components/RightRail";
import { useAnalysisStream } from "./hooks/useAnalysisStream";
import { useTranslation } from "./lib/i18n";
import { getReport, getTrace } from "./lib/api";
import { useAnalysisStore, useSettingsStore } from "./store/analysisStore";

function Workbench() {
  const { t } = useTranslation();
  const job = useAnalysisStore((state) => state.job);
  const report = useAnalysisStore((state) => state.report);
  const connectionMode = useAnalysisStore((state) => state.connectionMode);
  const selectedFindingId = useAnalysisStore((state) => state.selectedFindingId);
  const setReport = useAnalysisStore((state) => state.setReport);
  const setSelectedFindingId = useAnalysisStore((state) => state.setSelectedFindingId);
  const startRouteLoad = useAnalysisStore((state) => state.startRouteLoad);
  const setTraceRows = useAnalysisStore((state) => state.setTraceRows);
  const setConnectionMode = useAnalysisStore((state) => state.setConnectionMode);
  const apiToken = useSettingsStore((state) => state.settings.apiToken);
  const { contractId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [routeLoadErrorDetail, setRouteLoadErrorDetail] = useState("");
  const [isRouteLoading, setIsRouteLoading] = useState(false);
  useAnalysisStream(job?.analysis_id === "demo-analysis" ? null : job?.analysis_id ?? null);

  useEffect(() => {
    const findingId = searchParams.get("finding");
    if (!findingId) return;
    const findingExists = report.findings.some((finding) => finding.finding_id === findingId);
    if (findingExists && findingId !== selectedFindingId) {
      setSelectedFindingId(findingId);
      return;
    }
    if (!findingExists && report.findings.length > 0) {
      const nextSearchParams = new URLSearchParams(searchParams);
      nextSearchParams.delete("finding");
      setSearchParams(nextSearchParams, { replace: true });
    }
  }, [report.findings, searchParams, selectedFindingId, setSearchParams, setSelectedFindingId]);

  useLayoutEffect(() => {
    if (!contractId) {
      setIsRouteLoading(false);
      setRouteLoadErrorDetail("");
      return;
    }
    let active = true;
    setIsRouteLoading(true);
    setRouteLoadErrorDetail("");
    startRouteLoad(contractId);
    getReport(contractId, apiToken)
      .then((nextReport) => {
        if (!active) return;
        setTraceRows([]);
        setConnectionMode("polling");
        setReport(nextReport, new URLSearchParams(window.location.search).get("finding") ?? undefined);
      })
      .catch((error: unknown) => {
        if (!active) return;
        setRouteLoadErrorDetail(error instanceof Error ? error.message : "");
      })
      .finally(() => {
        if (active) setIsRouteLoading(false);
      });
    return () => {
      active = false;
    };
  }, [apiToken, contractId, setConnectionMode, setReport, setTraceRows, startRouteLoad]);

  useEffect(() => {
    const traceId = report.analysis_metadata.analysis_trace_id;
    if (connectionMode === "demo") return;
    setTraceRows([]);
    if (!traceId || !selectedFindingId) return;
    let active = true;
    getTrace(traceId, selectedFindingId, apiToken)
      .then((rows) => {
        if (active) setTraceRows(rows);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [
    apiToken,
    connectionMode,
    report.analysis_metadata.analysis_trace_id,
    selectedFindingId,
    setTraceRows,
  ]);

  return (
    <div className="flex min-h-dvh flex-col bg-canvas text-text lg:flex-row lg:overflow-hidden">
      <InputPanel />
      <main className="flex min-w-0 flex-1 flex-col lg:h-full">
        <ReportHeader />
        <div className="flex-1 bg-canvas px-5 py-4 lg:min-h-0">
          {contractId && isRouteLoading ? (
            <div className="mb-4 rounded-md border border-border-subtle bg-surface px-4 py-3 text-sm text-text-muted">
              {t("routeLoadStatus", { contractId })}
            </div>
          ) : null}
          {contractId && routeLoadErrorDetail ? (
            <div
              className="mb-4 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"
              role="alert"
            >
              {routeLoadErrorDetail.trim()
                ? t("routeLoadFailed", { contractId, message: routeLoadErrorDetail })
                : t("routeLoadFailedHint", { contractId })}
            </div>
          ) : null}
          <FindingList findings={report.findings} />
        </div>
      </main>
      <RightRail />
    </div>
  );
}

export function App() {
  const baseName = import.meta.env.BASE_URL === "/" ? undefined : import.meta.env.BASE_URL.replace(/\/$/, "");

  return (
    <BrowserRouter
      basename={baseName}
      future={{ v7_relativeSplatPath: true, v7_startTransition: true }}
    >
      <Routes>
        <Route path="/" element={<Workbench />} />
        <Route path="/reports/:contractId" element={<Workbench />} />
      </Routes>
    </BrowserRouter>
  );
}
