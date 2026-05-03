import { Activity, Database, GitBranch, Timer } from "lucide-react";

import { formatScore, formatTokens } from "../lib/format";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import { LanguageToggle } from "./LanguageToggle";
import { Metric } from "./Metric";
import { ReviewBadge, StatusBadge } from "./StatusBadge";

export function ReportHeader() {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const connectionMode = useAnalysisStore((state) => state.connectionMode);
  const metadata = report.analysis_metadata;

  return (
    <header className="border-b border-slate-200 bg-white px-5 py-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={report.overall_status} />
            <ReviewBadge status={report.review_status} />
            <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-700">
              {connectionMode.toUpperCase()}
            </span>
          </div>
          <h1 className="mt-2 text-xl font-semibold tracking-normal text-slate-950">
            {t("appTitle")}
          </h1>
          <p className="mt-1 truncate text-sm text-slate-600">
            {t("contract")} {report.contract_id} · {t("trace")} {metadata.analysis_trace_id}
          </p>
        </div>
        <div className="flex w-full flex-col gap-3 lg:w-auto">
          <div className="flex justify-start lg:justify-end">
            <LanguageToggle />
          </div>
          <dl className="grid w-full grid-cols-2 gap-3 md:grid-cols-4 lg:min-w-[360px] lg:w-auto">
            <Metric label={t("findings")} value={report.findings.length} />
            <Metric label={t("tokens")} value={formatTokens(metadata.total_tokens)} />
            <Metric label={t("localJudge")} value={formatScore(metadata.local_average_judge_score)} />
            <Metric label={t("duration")} value={`${metadata.total_duration_ms} ms`} />
          </dl>
        </div>
      </div>

      <div className="mt-4 grid gap-3 border-t border-slate-100 pt-3 text-sm text-slate-700 md:grid-cols-4">
        <div className="flex min-w-0 items-center gap-2">
          <Database className="h-4 w-4 text-audit-teal" aria-hidden="true" />
          <span className="truncate">{metadata.dataset_version}</span>
        </div>
        <div className="flex min-w-0 items-center gap-2">
          <Activity className="h-4 w-4 text-audit-blue" aria-hidden="true" />
          <span className="truncate">{metadata.model_version}</span>
        </div>
        <div className="flex min-w-0 items-center gap-2">
          <GitBranch className="h-4 w-4 text-audit-amber" aria-hidden="true" />
          <span className="truncate">solc {metadata.solc_version ?? "unknown"}</span>
        </div>
        <div className="flex min-w-0 items-center gap-2">
          <Timer className="h-4 w-4 text-audit-green" aria-hidden="true" />
          <span className="truncate">slither {metadata.slither_version ?? "unknown"}</span>
        </div>
      </div>
    </header>
  );
}
