import { Clipboard, FileWarning, ShieldCheck } from "lucide-react";
import { lazy, memo, Suspense, useCallback } from "react";

import { formatLocation, formatScore, formatTokens } from "../lib/format";
import { useTranslation } from "../lib/i18n";
import { useSettingsStore } from "../store/analysisStore";
import type { Finding } from "../types/report";
import { CodeBlock } from "./CodeBlock";
import { Metric } from "./Metric";
import { SeverityBadge } from "./StatusBadge";

const LazyDiffViewerPanel = lazy(() =>
  import("./DiffViewerPanel").then((module) => ({ default: module.DiffViewerPanel })),
);

export const FindingCard = memo(function FindingCard({
  finding,
  selected,
  onSelect,
  streamText,
}: {
  finding: Finding;
  selected: boolean;
  onSelect: (findingId: string) => void;
  streamText?: string;
}) {
  const { t } = useTranslation();
  const diffMode = useSettingsStore((state) => state.settings.diffMode);
  const updateSettings = useSettingsStore((state) => state.updateSettings);
  const vulnerableCode = finding.vulnerable_code ?? "";
  const remediationCode = finding.remediation_code ?? "";
  const explanation = streamText || finding.explanation;

  const copyRemediation = useCallback(async () => {
    if (remediationCode) await navigator.clipboard.writeText(remediationCode);
  }, [remediationCode]);

  return (
    <article
      role="article"
      aria-label={finding.finding_id}
      className={`rounded-md border bg-white p-4 transition ${selected ? "border-audit-teal ring-2 ring-teal-100" : "border-slate-200"}`}
    >
      <button
        type="button"
        onClick={() => onSelect(finding.finding_id)}
        className="flex w-full items-start justify-between gap-3 text-left"
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={finding.severity} />
            <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-700">
              {finding.detector_name}
            </span>
          </div>
          <h2 className="mt-2 text-base font-semibold text-slate-950">
            {finding.vulnerability_type}
          </h2>
          <p className="mt-1 break-words text-sm text-slate-600">
            {formatLocation(finding.location)}
          </p>
        </div>
        {finding.partial ? (
          <FileWarning className="mt-1 h-5 w-5 shrink-0 text-amber-600" aria-label={t("partialFinding")} />
        ) : (
          <ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-emerald-700" aria-label={t("schemaValid")} />
        )}
      </button>

      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label={t("findingConfidence")} value={finding.finding_confidence.toFixed(2)} />
        <Metric label={t("explanationConfidence")} value={finding.explanation_confidence.toFixed(2)} />
        <Metric label={t("localJudge")} value={formatScore(finding.local_judge_score)} />
        <Metric label={t("externalJudge")} value={formatScore(finding.external_judge_score)} />
      </div>

      <div className="mt-4 space-y-4">
        <section aria-labelledby={`${finding.finding_id}-code`}>
          <h3 id={`${finding.finding_id}-code`} className="mb-2 text-sm font-semibold text-slate-900">
            {t("vulnerableCode")}
          </h3>
          <CodeBlock code={vulnerableCode} />
        </section>

        <section aria-live="polite" aria-labelledby={`${finding.finding_id}-explanation`}>
          <h3 id={`${finding.finding_id}-explanation`} className="mb-2 text-sm font-semibold text-slate-900">
            {t("aiExplanation")}
          </h3>
          <p className="text-sm leading-6 text-slate-700">{explanation || t("deterministicOnly")}</p>
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          <section>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("attackPath")}</h3>
            <p className="text-sm leading-6 text-slate-700">{finding.attack_path || t("notGenerated")}</p>
          </section>
          <section>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("fixSuggestion")}</h3>
            <p className="text-sm leading-6 text-slate-700">{finding.fix_suggestion || t("notGenerated")}</p>
          </section>
        </div>

        <section aria-labelledby={`${finding.finding_id}-diff`}>
          <div className="mb-2 flex items-center justify-between gap-2">
            <h3 id={`${finding.finding_id}-diff`} className="text-sm font-semibold text-slate-900">
              {t("remediationDiff")}
            </h3>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={diffMode === "split"}
                  onChange={(event) =>
                    updateSettings({ diffMode: event.currentTarget.checked ? "split" : "inline" })
                  }
                  className="h-4 w-4 rounded border-slate-300 text-audit-teal focus:ring-audit-teal"
                />
                {t("split")}
              </label>
              <button
                type="button"
                onClick={copyRemediation}
                className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-audit-teal"
                aria-label={t("copyRemediationCode")}
              >
                <Clipboard className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          </div>
          <Suspense
            fallback={
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                {t("loadingDiff")}
              </div>
            }
          >
            <LazyDiffViewerPanel
              oldValue={vulnerableCode}
              newValue={remediationCode}
              splitView={diffMode === "split"}
            />
          </Suspense>
        </section>

        <dl className="grid grid-cols-3 gap-3 border-t border-slate-200 pt-3">
          <Metric label={t("promptTokens")} value={formatTokens(finding.prompt_tokens)} />
          <Metric label={t("completionTokens")} value={formatTokens(finding.completion_tokens)} />
          <Metric label={t("totalTokens")} value={formatTokens(finding.total_tokens)} />
        </dl>
      </div>
    </article>
  );
});
