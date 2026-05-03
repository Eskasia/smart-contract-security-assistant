import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useSearchParams } from "react-router-dom";

import { FindingList } from "./components/FindingList";
import { InputPanel } from "./components/InputPanel";
import { ReportHeader } from "./components/ReportHeader";
import { RightRail } from "./components/RightRail";
import { useAnalysisStream } from "./hooks/useAnalysisStream";
import { getTrace } from "./lib/api";
import { useAnalysisStore } from "./store/analysisStore";

function Workbench() {
  const job = useAnalysisStore((state) => state.job);
  const report = useAnalysisStore((state) => state.report);
  const connectionMode = useAnalysisStore((state) => state.connectionMode);
  const selectedFindingId = useAnalysisStore((state) => state.selectedFindingId);
  const setSelectedFindingId = useAnalysisStore((state) => state.setSelectedFindingId);
  const setTraceRows = useAnalysisStore((state) => state.setTraceRows);
  const [searchParams] = useSearchParams();
  useAnalysisStream(job?.analysis_id === "demo-analysis" ? null : job?.analysis_id ?? null);

  useEffect(() => {
    const findingId = searchParams.get("finding");
    if (findingId && report.findings.some((finding) => finding.finding_id === findingId)) {
      setSelectedFindingId(findingId);
    }
  }, [report.findings, searchParams, setSelectedFindingId]);

  useEffect(() => {
    const traceId = report.analysis_metadata.analysis_trace_id;
    if (connectionMode === "demo") return;
    if (!traceId || !selectedFindingId) return;
    getTrace(traceId, selectedFindingId)
      .then(setTraceRows)
      .catch(() => undefined);
  }, [connectionMode, report.analysis_metadata.analysis_trace_id, selectedFindingId, setTraceRows]);

  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900 lg:h-screen lg:min-h-[720px] lg:flex-row lg:overflow-hidden">
      <InputPanel />
      <main className="flex min-w-0 flex-1 flex-col lg:h-full">
        <ReportHeader />
        <div className="min-h-[720px] flex-1 bg-slate-100 px-5 py-4 lg:min-h-0">
          <FindingList findings={report.findings} />
        </div>
      </main>
      <RightRail />
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <Routes>
        <Route path="/" element={<Workbench />} />
        <Route path="/reports/:contractId" element={<Workbench />} />
      </Routes>
    </BrowserRouter>
  );
}
