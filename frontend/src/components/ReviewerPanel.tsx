import { Save } from "lucide-react";
import { useEffect, useState } from "react";

import { patchReviewStatus } from "../lib/api";
import { useTranslation, type TranslationKey } from "../lib/i18n";
import { useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import type { ReviewStatus } from "../types/report";
import { Metric } from "./Metric";

const statuses: ReviewStatus[] = ["pending_human_review", "approved", "rejected", "blocked"];
const statusLabelKeys: Record<ReviewStatus, TranslationKey> = {
  pending_human_review: "pendingHumanReview",
  approved: "approved",
  rejected: "rejected",
  blocked: "blocked",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function ReviewerPanel() {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const connectionMode = useAnalysisStore((state) => state.connectionMode);
  const setReport = useAnalysisStore((state) => state.setReport);
  const updateReviewStatus = useAnalysisStore((state) => state.updateReviewStatus);
  const apiToken = useSettingsStore((state) => state.settings.apiToken);
  const [draft, setDraft] = useState<ReviewStatus>(report.review_status);
  const [message, setMessage] = useState("");
  const reportNotReady =
    !report.analysis_metadata.analysis_trace_id ||
    report.overall_status === "queued" ||
    report.overall_status === "running";

  useEffect(() => {
    setDraft(report.review_status);
  }, [report.review_status]);

  async function saveReviewStatus() {
    if (reportNotReady) {
      setMessage(t("reportNotReady"));
      return;
    }
    try {
      const response = await patchReviewStatus(
        report.contract_id,
        { review_status: draft },
        apiToken,
      );
      setReport(response.report);
      setMessage(t("saved"));
    } catch (error) {
      if (connectionMode === "demo") {
        updateReviewStatus(draft);
        setMessage(t("savedLocally"));
      } else {
        setMessage(t("saveFailed", { message: errorMessage(error) }));
      }
    }
  }

  return (
    <section className="space-y-4 border-b border-slate-200 pb-4">
      <div>
        <h2 className="text-sm font-semibold text-slate-950">{t("reviewer")}</h2>
        <p className="mt-1 text-xs leading-5 text-slate-600">{report.review_reason}</p>
      </div>

      <dl className="grid grid-cols-2 gap-3">
        <Metric label={t("businessReview")} value={report.business_logic_review_required ? t("required") : t("no")} />
        <Metric label={t("humanReview")} value={report.requires_human_review ? t("required") : t("no")} />
      </dl>

      <label className="block">
        <span className="text-xs font-medium text-slate-600">{t("reviewStatus")}</span>
        <select
          value={draft}
          onChange={(event) => setDraft(event.currentTarget.value as ReviewStatus)}
          className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
        >
          {statuses.map((status) => (
            <option key={status} value={status}>
              {t(statusLabelKeys[status])}
            </option>
          ))}
        </select>
      </label>

      <button
        type="button"
        onClick={saveReviewStatus}
        disabled={reportNotReady}
        className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400 focus:outline-none focus:ring-2 focus:ring-audit-teal"
      >
        <Save className="h-4 w-4" aria-hidden="true" />
        {t("save")}
      </button>
      <p className="min-h-5 text-xs text-slate-600" role="status">
        {message || (reportNotReady ? t("reportNotReady") : "")}
      </p>
    </section>
  );
}
