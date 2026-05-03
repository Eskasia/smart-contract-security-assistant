import type { AnalysisStatus, ReviewStatus } from "../types/report";
import { useTranslation, type TranslationKey } from "../lib/i18n";

type BadgeTone = "neutral" | "green" | "amber" | "red" | "blue";

const toneClass: Record<BadgeTone, string> = {
  neutral: "border-surface-200 bg-surface-50 text-surface-800",
  green: "border-emerald-200 bg-emerald-50 text-emerald-800",
  amber: "border-amber-200 bg-amber-50 text-amber-800",
  red: "border-red-200 bg-red-50 text-red-800",
  blue: "border-blue-200 bg-blue-50 text-blue-800",
};

export function StatusBadge({
  status,
  className = "",
}: {
  status: AnalysisStatus;
  className?: string;
}) {
  const { t } = useTranslation();
  const tone: Record<AnalysisStatus, BadgeTone> = {
    queued: "neutral",
    running: "blue",
    finding: "red",
    no_finding: "green",
    partial_analysis: "amber",
    error: "red",
  };
  const labelKey: Record<AnalysisStatus, TranslationKey> = {
    queued: "queued",
    running: "running",
    finding: "finding",
    no_finding: "noFinding",
    partial_analysis: "partialAnalysis",
    error: "error",
  };

  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${toneClass[tone[status]]} ${className}`}>
      {t(labelKey[status])}
    </span>
  );
}

export function ReviewBadge({ status }: { status: ReviewStatus }) {
  const { t } = useTranslation();
  const tone: Record<ReviewStatus, BadgeTone> = {
    pending_human_review: "amber",
    approved: "green",
    rejected: "red",
    blocked: "red",
  };
  const labelKey: Record<ReviewStatus, TranslationKey> = {
    pending_human_review: "pendingHumanReview",
    approved: "approved",
    rejected: "rejected",
    blocked: "blocked",
  };

  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${toneClass[tone[status]]}`}>
      {t(labelKey[status])}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: number }) {
  const { t } = useTranslation();
  const label = severity >= 4 ? t("critical") : severity === 3 ? t("high") : severity === 2 ? t("medium") : severity === 1 ? t("low") : t("info");
  const tone: BadgeTone = severity >= 3 ? "red" : severity === 2 ? "amber" : "blue";

  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${toneClass[tone]}`}>
      {label} · {severity}
    </span>
  );
}
