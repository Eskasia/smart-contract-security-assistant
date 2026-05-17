import { useEffect } from "react";

import { getAnalysis, getReport } from "../lib/api";
import { isTerminalStatus } from "../lib/status";
import { useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import type { AnalysisEvent } from "../types/api";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function useAnalysisStream(analysisId: string | null) {
  const setJob = useAnalysisStore((state) => state.setJob);
  const setReport = useAnalysisStore((state) => state.setReport);
  const setConnectionMode = useAnalysisStore((state) => state.setConnectionMode);
  const setAnalysisError = useAnalysisStore((state) => state.setAnalysisError);
  const appendFindingToken = useAnalysisStore((state) => state.appendFindingToken);
  const apiToken = useSettingsStore((state) => state.settings.apiToken);

  useEffect(() => {
    if (!analysisId) return undefined;

    let cancelled = false;
    let pollingTimer: number | null = null;

    const loadTerminalReport = async () => {
      try {
        const job = await getAnalysis(analysisId, apiToken);
        if (cancelled) return;
        setJob(job);
        if (job.contract_id) {
          const report = await getReport(job.contract_id, apiToken);
          if (!cancelled) setReport(report);
        }
      } catch (error) {
        if (cancelled) return;
        const message = errorMessage(error);
        setAnalysisError(message);
        setJob({ analysis_id: analysisId, status: "error", message });
      }
    };

    const startPolling = () => {
      setConnectionMode("polling");
      const poll = async () => {
        try {
          const job = await getAnalysis(analysisId, apiToken);
          if (cancelled) return;
          setJob(job);
          if (isTerminalStatus(job.status)) {
            if (job.contract_id) {
              const report = await getReport(job.contract_id, apiToken);
              if (!cancelled) setReport(report);
            }
          } else {
            pollingTimer = window.setTimeout(poll, 1000);
          }
        } catch (error) {
          if (cancelled) return;
          const message = errorMessage(error);
          setAnalysisError(message);
          setJob({ analysis_id: analysisId, status: "error", message });
        }
      };
      pollingTimer = window.setTimeout(poll, 1000);
    };

    if (apiToken.trim()) {
      startPolling();
      return () => {
        cancelled = true;
        if (pollingTimer) window.clearTimeout(pollingTimer);
      };
    }

    const eventSource = new EventSource(`/api/analyses/${analysisId}/stream`);
    setConnectionMode("sse");

    eventSource.onmessage = async (event) => {
      const data = JSON.parse(event.data) as AnalysisEvent;
      if (data.type === "status") {
        setJob({ analysis_id: analysisId, status: data.status, message: data.message });
        if (isTerminalStatus(data.status)) {
          eventSource.close();
          await loadTerminalReport().catch(() => undefined);
        }
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
        await loadTerminalReport();
      }
      if (data.type === "error") {
        eventSource.close();
        setAnalysisError(data.message);
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
      if (pollingTimer) window.clearTimeout(pollingTimer);
    };
  }, [
    analysisId,
    apiToken,
    appendFindingToken,
    setAnalysisError,
    setConnectionMode,
    setJob,
    setReport,
  ]);
}
