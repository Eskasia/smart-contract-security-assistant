import { useMemo } from "react";

import { formatLocation } from "../lib/format";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import { Metric } from "./Metric";

function preformatted(value: string | null | undefined, fallback: string) {
  if (!value) return fallback;
  return value;
}

export function TracePanel() {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const selectedFindingId = useAnalysisStore((state) => state.selectedFindingId);
  const traceRows = useAnalysisStore((state) => state.traceRows);
  const selectedTrace = useMemo(
    () => traceRows.find((row) => row.finding_id === selectedFindingId),
    [selectedFindingId, traceRows],
  );
  const selectedFinding = report.findings.find((finding) => finding.finding_id === selectedFindingId);

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-950">{t("traceEvidence")}</h2>
        <p className="mt-1 break-words text-xs text-slate-600">
          {report.analysis_metadata.analysis_trace_id}
        </p>
        {selectedFinding ? (
          <p className="mt-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs leading-5 text-slate-700 lg:hidden">
            {selectedFinding.vulnerability_type} · {formatLocation(selectedFinding.location)}
          </p>
        ) : null}
      </div>

      <dl className="grid grid-cols-2 gap-3">
        <Metric label={t("ragMode")} value={selectedTrace?.rag_mode ?? report.analysis_metadata.rag_mode} />
        <Metric label={t("chunks")} value={selectedTrace?.chunks_used ?? 0} />
        <Metric label={t("retrieval")} value={`${selectedTrace?.retrieval_duration_ms ?? 0} ms`} />
        <Metric label="LLM" value={`${selectedTrace?.llm_duration_ms ?? 0} ms`} />
      </dl>

      <div className="space-y-2">
        <details className="rounded-md border border-slate-200 bg-white p-3" open>
          <summary className="cursor-pointer text-sm font-medium text-slate-900">{t("slitherEvidence")}</summary>
          <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-700">
            {preformatted(selectedTrace?.slither_raw ?? selectedFinding?.evidence, t("unavailable"))}
          </pre>
        </details>
        <details className="rounded-md border border-slate-200 bg-white p-3">
          <summary className="cursor-pointer text-sm font-medium text-slate-900">{t("normalizedFinding")}</summary>
          <pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-700">
            {preformatted(selectedTrace?.normalized_finding, t("unavailable"))}
          </pre>
        </details>
        <details className="rounded-md border border-slate-200 bg-white p-3">
          <summary className="cursor-pointer text-sm font-medium text-slate-900">{t("ragChunkIds")}</summary>
          <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-700">
            {preformatted(selectedTrace?.rag_chunk_ids, t("unavailable"))}
          </pre>
        </details>
        <details className="rounded-md border border-slate-200 bg-white p-3">
          <summary className="cursor-pointer text-sm font-medium text-slate-900">{t("packedPrompt")}</summary>
          <pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-700">
            {preformatted(selectedTrace?.packed_prompt, t("unavailable"))}
          </pre>
        </details>
        <details className="rounded-md border border-slate-200 bg-white p-3">
          <summary className="cursor-pointer text-sm font-medium text-slate-900">{t("llmRawOutput")}</summary>
          <pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-slate-700">
            {preformatted(selectedTrace?.llm_raw_output, t("unavailable"))}
          </pre>
        </details>
      </div>
    </section>
  );
}
