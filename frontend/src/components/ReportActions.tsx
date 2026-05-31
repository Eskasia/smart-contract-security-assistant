import { useCallback, useMemo, type ReactNode } from "react";
import { Copy, Download, FileJson, FileText } from "lucide-react";

import { getReportMarkdown } from "../lib/api";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import { Button } from "./ui/Button";

type ReportActionsProps = {
  selectedFindingId: string | null;
  onActionMessage: (message: string) => void;
};

export function ReportActions({ selectedFindingId, onActionMessage }: ReportActionsProps) {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const apiToken = useSettingsStore((state) => state.settings.apiToken);
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
      onActionMessage(t("clipboardUnavailable"));
      return;
    }
    try {
      await navigator.clipboard.writeText(shareUrl);
      onActionMessage(t("reportLinkCopied"));
    } catch {
      onActionMessage(t("clipboardUnavailable"));
    }
  }, [onActionMessage, shareUrl, t]);

  const downloadJson = useCallback(() => {
    downloadTextFile(
      `${reportFileName}.json`,
      JSON.stringify(report, null, 2),
      "application/json;charset=utf-8",
    );
    onActionMessage(t("downloadStarted"));
  }, [onActionMessage, report, reportFileName, t]);

  const downloadMarkdown = useCallback(async () => {
    try {
      const markdown = await getReportMarkdown(report.contract_id, apiToken);
      downloadTextFile(`${reportFileName}.md`, markdown, "text/markdown;charset=utf-8");
      onActionMessage(t("downloadStarted"));
    } catch (error) {
      const message = error instanceof Error ? error.message : t("unavailable");
      onActionMessage(t("downloadFailed", { message }));
    }
  }, [apiToken, onActionMessage, report.contract_id, reportFileName, t]);

  return (
    <>
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
    </>
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
    <Button
      type="button"
      onClick={onClick}
      size="sm"
      aria-label={label}
      title={label}
    >
      {children}
      <span>{label}</span>
    </Button>
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
