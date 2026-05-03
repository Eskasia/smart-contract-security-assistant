import { useEffect } from "react";

import { getAnalysis, getReport } from "../lib/api";
import { isTerminalStatus } from "../lib/status";
import { useAnalysisStore } from "../store/analysisStore";
import type { AnalysisEvent } from "../types/api";

export function useAnalysisStream(analysisId: string | null) {
  const setJob = useAnalysisStore((state) => state.setJob);
  const setReport = useAnalysisStore((state) => state.setReport);
  const setConnectionMode = useAnalysisStore((state) => state.setConnectionMode);
  const appendFindingToken = useAnalysisStore((state) => state.appendFindingToken);

  useEffect(() => {
    if (!analysisId) return undefined;

    let cancelled = false;
    let pollingTimer: number | null = null;

    const startPolling = () => {
      setConnectionMode("polling");
      pollingTimer = window.setInterval(async () => {
        try {
          const job = await getAnalysis(analysisId);
          if (cancelled) return;
          setJob(job);
          if (isTerminalStatus(job.status)) {
            if (pollingTimer) window.clearInterval(pollingTimer);
            if (job.contract_id) {
              const report = await getReport(job.contract_id);
              if (!cancelled) setReport(report);
            }
          }
        } catch {
          if (pollingTimer) window.clearInterval(pollingTimer);
        }
      }, 1000);
    };

    const eventSource = new EventSource(`/api/analyses/${analysisId}/stream`);
    setConnectionMode("sse");

    eventSource.onmessage = async (event) => {
      const data = JSON.parse(event.data) as AnalysisEvent;
      if (data.type === "status") {
        setJob({ analysis_id: analysisId, status: data.status, message: data.message });
        if (isTerminalStatus(data.status)) eventSource.close();
      }
      if (data.type === "finding_token") appendFindingToken(data.finding_id, data.token);
      if (data.type === "finding_complete") {
        setJob({ analysis_id: analysisId, status: "running", message: data.finding.finding_id });
      }
      if (data.type === "done") {
        eventSource.close();
        setJob({
          analysis_id: analysisId,
          status: data.status ?? "finding",
          report_id: data.report_id,
          contract_id: data.contract_id ?? data.report_id,
        });
        const report = await getReport(data.contract_id ?? data.report_id);
        if (!cancelled) setReport(report);
      }
      if (data.type === "error") {
        eventSource.close();
        setJob({ analysis_id: analysisId, status: "error", message: data.message });
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      startPolling();
    };

    return () => {
      cancelled = true;
      eventSource.close();
      if (pollingTimer) window.clearInterval(pollingTimer);
    };
  }, [analysisId, appendFindingToken, setConnectionMode, setJob, setReport]);
}
