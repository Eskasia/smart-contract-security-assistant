import { useCallback, useMemo, useState, type ReactNode } from "react";
import {
  Activity,
  Copy,
  Database,
  Download,
  FileJson,
  FileText,
  GitBranch,
  Timer,
} from "lucide-react";

import { getReportMarkdown } from "../lib/api";
import { formatSecurityScore, formatTokens } from "../lib/format";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import { LanguageToggle } from "./LanguageToggle";
import { Metric } from "./Metric";
import { ReviewBadge, StatusBadge } from "./StatusBadge";

export function ReportHeader() {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const selectedFindingId = useAnalysisStore((state) => state.selectedFindingId);
  const connectionMode = useAnalysisStore((state) => state.connectionMode);
  const analysisError = useAnalysisStore((state) => state.analysisError);
  const apiToken = useSettingsStore((state) => state.settings.apiToken);
  const [actionMessage, setActionMessage] = useState("");
  const metadata = report.analysis_metadata;
  const reportFileName = useMemo(
    () => safeFileName(report.contract_id || "report"),
    [report.contract_id],
  );
  const shareUrl = useMemo(() => {
    const url = new URL(
      `/reports/${encodeURIComponent(report.contract_id)}`,
      window.location.origin,
    );
    if (selectedFindingId) {
      url.searchParams.set("finding", selectedFindingId);
    }
    return url.toString();
  }, [report.contract_id, selectedFindingId]);

  const copyReportLink = useCallback(async () => {
    if (!navigator.clipboard?.writeText) {
      setActionMessage(t("clipboardUnavailable"));
      return;
    }
    try {
      await navigator.clipboard.writeText(shareUrl);
      setActionMessage(t("reportLinkCopied"));
    } catch {
      setActionMessage(t("clipboardUnavailable"));
    }
  }, [shareUrl, t]);

  const downloadJson = useCallback(() => {
    downloadTextFile(
      `${reportFileName}.json`,
      JSON.stringify(report, null, 2),
      "application/json;charset=utf-8",
    );
    setActionMessage(t("downloadStarted"));
  }, [report, reportFileName, t]);

  const downloadMarkdown = useCallback(async () => {
    try {
      const markdown = await getReportMarkdown(report.contract_id, apiToken);
      downloadTextFile(`${reportFileName}.md`, markdown, "text/markdown;charset=utf-8");
      setActionMessage(t("downloadStarted"));
    } catch (error) {
      const message = error instanceof Error ? error.message : t("unavailable");
      setActionMessage(t("downloadFailed", { message }));
    }
  }, [apiToken, report.contract_id, reportFileName, t]);

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
          <div className="flex flex-wrap justify-start gap-2 lg:justify-end">
            <HeaderActionButton label={t("copyReportLink")} onClick={copyReportLink}>
              <Copy className="h-4 w-4" aria-hidden="true" />
            </HeaderActionButton>
            <HeaderActionButton label={t("downloadJson")} onClick={downloadJson}>
              <FileJson className="h-4 w-4" aria-hidden="true" />
            </HeaderActionButton>
            <HeaderActionButton label={t("downloadMarkdown")} onClick={downloadMarkdown}>
              <FileText className="h-4 w-4" aria-hidden="true" />
              <Download className="h-3 w-3" aria-hidden="true" />
            </HeaderActionButton>
            <LanguageToggle />
          </div>
          <dl className="grid w-full grid-cols-2 gap-3 md:grid-cols-4 lg:min-w-[360px] lg:w-auto">
            <Metric label={t("findings")} value={report.findings.length} />
            <Metric label={t("tokens")} value={formatTokens(metadata.total_tokens)} />
            <Metric label={t("securityScore")} value={formatSecurityScore(report.security_score)} />
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
      {analysisError && (
        <p
          className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"
          role="status"
        >
          {t("analysisStatusFailed", { message: analysisError })}
        </p>
      )}
      {actionMessage && (
        <p className="mt-3 text-sm text-slate-600" role="status">
          {actionMessage}
        </p>
      )}
    </header>
  );
}

function HeaderActionButton({
  children,
  label,
  onClick,
}: {
  children: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex h-8 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 text-xs font-semibold text-slate-800 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-audit-teal"
      aria-label={label}
      title={label}
    >
      {children}
      <span>{label}</span>
    </button>
  );
}

function safeFileName(value: string): string {
  return value.replace(/[^A-Za-z0-9_.-]+/g, "_").replace(/^_+|_+$/g, "") || "report";
}

function downloadTextFile(filename: string, content: string, contentType: string): void {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
