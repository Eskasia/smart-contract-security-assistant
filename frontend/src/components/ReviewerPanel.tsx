import { Save } from "lucide-react";
import { useEffect, useState } from "react";

import { patchReviewStatus } from "../lib/api";
import { useTranslation, type TranslationKey } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import type { ReviewStatus } from "../types/report";
import { Metric } from "./Metric";

const statuses: ReviewStatus[] = ["pending_human_review", "approved", "rejected", "blocked"];
const statusLabelKeys: Record<ReviewStatus, TranslationKey> = {
  pending_human_review: "pendingHumanReview",
  approved: "approved",
  rejected: "rejected",
  blocked: "blocked",
};

export function ReviewerPanel() {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const updateReviewStatus = useAnalysisStore((state) => state.updateReviewStatus);
  const [draft, setDraft] = useState<ReviewStatus>(report.review_status);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setDraft(report.review_status);
  }, [report.review_status]);

  async function saveReviewStatus() {
    try {
      const response = await patchReviewStatus(report.contract_id, { review_status: draft });
      updateReviewStatus(response.report.review_status);
      setMessage(t("saved"));
    } catch {
      updateReviewStatus(draft);
      setMessage(t("savedLocally"));
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
        className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-audit-teal"
      >
        <Save className="h-4 w-4" aria-hidden="true" />
        {t("save")}
      </button>
      <p className="min-h-5 text-xs text-slate-600" aria-live="polite">
        {message}
      </p>
    </section>
  );
}
