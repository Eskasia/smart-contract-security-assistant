import { formatScore, formatTokens } from "../lib/format";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import { Metric } from "./Metric";
import { ReviewerPanel } from "./ReviewerPanel";
import { TracePanel } from "./TracePanel";

export function RightRail() {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const metadata = report.analysis_metadata;

  return (
    <aside className="flex w-full shrink-0 flex-col overflow-auto border-t border-slate-200 bg-surface-50 px-4 py-4 lg:h-full lg:w-[360px] lg:border-l lg:border-t-0">
      <ReviewerPanel />

      <section className="space-y-3 border-b border-slate-200 py-4">
        <h2 className="text-sm font-semibold text-slate-950">{t("metrics")}</h2>
        <dl className="grid grid-cols-2 gap-3">
          <Metric label={t("scoreFormula")} value={report.score_formula_version ?? "security_score_v1"} />
          <Metric label={t("promptTokens")} value={formatTokens(metadata.prompt_tokens)} />
          <Metric label={t("completionTokens")} value={formatTokens(metadata.completion_tokens)} />
          <Metric label={t("totalTokens")} value={formatTokens(metadata.total_tokens)} />
          <Metric label={t("localJudge")} value={formatScore(metadata.local_average_judge_score)} />
          <Metric label={t("externalJudge")} value={formatScore(metadata.external_average_judge_score)} />
        </dl>
        {metadata.errors.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
            {metadata.errors.join(" ")}
          </div>
        )}
      </section>

      <section className="space-y-3 border-b border-slate-200 py-4">
        <h2 className="text-sm font-semibold text-slate-950">{t("externalTools")}</h2>
        {report.external_tool_results && report.external_tool_results.length > 0 ? (
          <div className="space-y-2">
            {report.external_tool_results.map((result) => (
              <div key={result.tool_name} className="rounded-md border border-slate-200 bg-white p-3">
                <div className="flex items-center justify-between gap-2 text-xs">
                  <span className="font-semibold uppercase text-slate-700">
                    {result.tool_name}
                  </span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-slate-700">
                    {result.status}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-600">{result.summary}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  findings {result.findings_count}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">{t("noExternalTools")}</p>
        )}
      </section>

      <div className="py-4">
        <TracePanel />
      </div>
    </aside>
  );
}
