import { Save } from "lucide-react";
import { useEffect, useState } from "react";

import { patchReviewStatus } from "../lib/api";
import { useTranslation, type TranslationKey } from "../lib/i18n";
import { useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import type { ReviewStatus } from "../types/report";
import { Metric } from "./Metric";
import { Button } from "./ui/Button";
import { Field, fieldControlClass } from "./ui/Field";

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
    <section className="space-y-4 border-b border-border-subtle pb-4">
      <div>
        <h2 className="text-sm font-semibold text-text-strong">{t("reviewer")}</h2>
        <p className="mt-1 text-xs leading-5 text-text-muted">{report.review_reason}</p>
      </div>

      <dl className="grid grid-cols-2 gap-3">
        <Metric label={t("businessReview")} value={report.business_logic_review_required ? t("required") : t("no")} />
        <Metric label={t("humanReview")} value={report.requires_human_review ? t("required") : t("no")} />
      </dl>

      <Field label={t("reviewStatus")}>
        <select
          value={draft}
          onChange={(event) => setDraft(event.currentTarget.value as ReviewStatus)}
          className={fieldControlClass}
        >
          {statuses.map((status) => (
            <option key={status} value={status}>
              {t(statusLabelKeys[status])}
            </option>
          ))}
        </select>
      </Field>

      <Button
        type="button"
        onClick={saveReviewStatus}
        disabled={reportNotReady}
        className="w-full"
      >
        <Save className="h-4 w-4" aria-hidden="true" />
        {t("save")}
      </Button>
      <p className="min-h-5 text-xs text-text-muted" role="status">
        {message || (reportNotReady ? t("reportNotReady") : "")}
      </p>
    </section>
  );
}
