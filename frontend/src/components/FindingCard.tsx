import { Clipboard, FileWarning, Save, ShieldCheck } from "lucide-react";
import { lazy, memo, Suspense, useCallback, useEffect, useState } from "react";

import { formatLocation, formatScore, formatTokens } from "../lib/format";
import { patchFindingReview } from "../lib/api";
import { useTranslation, type TranslationKey } from "../lib/i18n";
import { useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import type { Finding, FindingReviewStatus } from "../types/report";
import { CodeBlock } from "./CodeBlock";
import { Metric } from "./Metric";
import { SeverityBadge } from "./StatusBadge";

const LazyDiffViewerPanel = lazy(() =>
  import("./DiffViewerPanel").then((module) => ({ default: module.DiffViewerPanel })),
);

const findingReviewStatuses: FindingReviewStatus[] = [
  "unreviewed",
  "true_positive",
  "false_positive",
  "accepted_risk",
  "fixed",
];

const findingReviewLabelKeys: Record<FindingReviewStatus, TranslationKey> = {
  unreviewed: "unreviewed",
  true_positive: "truePositive",
  false_positive: "falsePositive",
  accepted_risk: "acceptedRisk",
  fixed: "fixed",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

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
  const apiToken = useSettingsStore((state) => state.settings.apiToken);
  const updateSettings = useSettingsStore((state) => state.updateSettings);
  const contractId = useAnalysisStore((state) => state.report.contract_id);
  const connectionMode = useAnalysisStore((state) => state.connectionMode);
  const setReport = useAnalysisStore((state) => state.setReport);
  const updateFindingReview = useAnalysisStore((state) => state.updateFindingReview);
  const vulnerableCode = finding.vulnerable_code ?? "";
  const remediationCode = finding.remediation_code ?? "";
  const explanation = streamText || finding.explanation;
  const [reviewDraft, setReviewDraft] = useState<FindingReviewStatus>(
    finding.review_status ?? "unreviewed",
  );
  const [reviewNote, setReviewNote] = useState(finding.review_note ?? "");
  const [reviewMessage, setReviewMessage] = useState("");

  useEffect(() => {
    setReviewDraft(finding.review_status ?? "unreviewed");
    setReviewNote(finding.review_note ?? "");
    setReviewMessage("");
  }, [finding.finding_id, finding.review_status, finding.review_note]);

  const copyRemediation = useCallback(async () => {
    if (remediationCode) await navigator.clipboard.writeText(remediationCode);
  }, [remediationCode]);

  const saveFindingReview = useCallback(async () => {
    try {
      const response = await patchFindingReview(
        contractId,
        finding.finding_id,
        {
          review_status: reviewDraft,
          review_note: reviewNote,
        },
        apiToken,
      );
      setReport(response.report);
      setReviewMessage(t("saved"));
    } catch (error) {
      if (connectionMode === "demo") {
        updateFindingReview(finding.finding_id, reviewDraft, reviewNote);
        setReviewMessage(t("savedLocally"));
      } else {
        setReviewMessage(t("saveFailed", { message: errorMessage(error) }));
      }
    }
  }, [
    connectionMode,
    contractId,
    finding.finding_id,
    reviewDraft,
    reviewNote,
    apiToken,
    setReport,
    t,
    updateFindingReview,
  ]);

  return (
    <article
      role="article"
      aria-label={finding.finding_id}
      className={`rounded-md border bg-white p-4 transition ${selected ? "border-audit-teal ring-2 ring-teal-100" : "border-slate-200"}`}
    >
      <button
        type="button"
        onClick={() => onSelect(finding.finding_id)}
        aria-current={selected ? "true" : undefined}
        aria-pressed={selected}
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

      <div className="mt-4 grid gap-3 border-t border-slate-200 pt-3 md:grid-cols-[minmax(170px,220px)_minmax(0,1fr)_auto]">
        <label className="block">
          <span className="text-xs font-medium text-slate-600">
            {t("findingReviewStatus")}
          </span>
          <select
            value={reviewDraft}
            onChange={(event) =>
              setReviewDraft(event.currentTarget.value as FindingReviewStatus)
            }
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          >
            {findingReviewStatuses.map((status) => (
              <option key={status} value={status}>
                {t(findingReviewLabelKeys[status])}
              </option>
            ))}
          </select>
        </label>
        <label className="block min-w-0">
          <span className="text-xs font-medium text-slate-600">{t("reviewNote")}</span>
          <input
            value={reviewNote}
            maxLength={2000}
            onChange={(event) => setReviewNote(event.currentTarget.value)}
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          />
        </label>
        <button
          type="button"
          onClick={saveFindingReview}
          className="inline-flex h-10 items-center justify-center gap-2 self-end rounded-md border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-900 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          aria-label={t("saveFindingReview")}
        >
          <Save className="h-4 w-4" aria-hidden="true" />
          <span>{t("save")}</span>
        </button>
        <p className="min-h-5 text-xs text-slate-600 md:col-span-3" role="status">
          {reviewMessage}
        </p>
      </div>

      <div className="mt-4 space-y-4">
        <section aria-labelledby={`${finding.finding_id}-code`}>
          <h3 id={`${finding.finding_id}-code`} className="mb-2 text-sm font-semibold text-slate-900">
            {t("vulnerableCode")}
          </h3>
          <CodeBlock code={vulnerableCode} />
        </section>

        <section aria-labelledby={`${finding.finding_id}-explanation`}>
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
