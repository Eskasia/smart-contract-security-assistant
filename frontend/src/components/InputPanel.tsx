import { FolderOpen, Play, RotateCcw, Upload } from "lucide-react";
import { type CSSProperties, useState } from "react";

import { createAnalysis, createImport } from "../lib/api";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import type { ExternalToolName, ImportSourceType, RagMode } from "../types/report";
import { usePersistedSettings } from "../hooks/usePersistedSettings";
import { Button } from "./ui/Button";
import { Field, fieldControlClass } from "./ui/Field";
import { ToolSelector } from "./ui/ToolSelector";

const ragModes: RagMode[] = ["quality", "balanced", "fast", "fallback"];
const importSourceTypes: ImportSourceType[] = [
  "local",
  "github_archive",
  "etherscan_api",
  "zip_base64",
];
const nativeBuildPolicies = ["trusted", "disabled"] as const;

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function importedMode(sourceType: ImportSourceType): "file" | "project" {
  return sourceType === "etherscan_api" ? "file" : "project";
}

async function encodeFileBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return btoa(binary);
}

export function InputPanel() {
  const { settings, updateSettings } = usePersistedSettings();
  const { t } = useTranslation();
  const startAnalysis = useAnalysisStore((state) => state.startAnalysis);
  const loadDemo = useAnalysisStore((state) => state.loadDemo);
  const [validationMessage, setValidationMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [sourceApiKey, setSourceApiKey] = useState("");
  const [sourceArchive, setSourceArchive] = useState<File | null>(null);

  async function handleSourcePreview(file: File | null) {
    if (!file) return;
    const source = await file.text();
    const lines = source.split(/\r?\n/).length;
    if (!file.name.endsWith(".sol")) {
      setValidationMessage(t("invalidSol"));
      return;
    }
    if (lines > 500) {
      setValidationMessage(t("singleFileLimit", { lines }));
      return;
    }
    setValidationMessage(t("fileReady", { name: file.name, lines }));
  }

  async function importSource() {
    if (settings.importSourceType === "local") return;
    if (settings.importSourceType === "zip_base64" && !sourceArchive) {
      setValidationMessage(t("zipArchiveRequired"));
      return;
    }
    if (settings.importSourceType !== "zip_base64" && !settings.importSourceValue.trim()) {
      setValidationMessage(t("sourceValueRequired"));
      return;
    }

    setIsImporting(true);
    setValidationMessage("");
    try {
      const payload =
        settings.importSourceType === "github_archive"
          ? {
              source_kind: "github_archive" as const,
              repository: settings.importSourceValue.trim(),
            }
          : settings.importSourceType === "etherscan_api"
            ? {
                source_kind: "etherscan_api" as const,
                contract_address: settings.importSourceValue.trim(),
                explorer_host: settings.importExplorerHost,
                api_key: sourceApiKey.trim() || undefined,
              }
            : {
                source_kind: "zip_base64" as const,
                archive_base64: await encodeFileBase64(sourceArchive as File),
                archive_name: sourceArchive?.name,
              };
      const result = await createImport(
        payload,
        settings.apiToken,
      );
      updateSettings({
        inputPath: result.input_path,
        inputMode: importedMode(settings.importSourceType),
        nativeBuildPolicy: "disabled",
      });
      setValidationMessage(t("sourceImported", { path: result.input_path }));
    } catch (error) {
      const message = errorMessage(error);
      setValidationMessage(t("sourceImportFailed", { message }));
    } finally {
      setIsImporting(false);
    }
  }

  async function submitAnalysis() {
    setIsSubmitting(true);
    setValidationMessage("");
    try {
      const enabledExternalTools = settings.externalTools.filter(
        (tool) => tool !== "halmos" || settings.nativeBuildPolicy === "trusted",
      );
      const externalTools: ExternalToolName[] | undefined = enabledExternalTools.length
        ? enabledExternalTools
        : undefined;
      const job = await createAnalysis(
        {
          input_path: settings.inputPath,
          rag_mode: settings.ragMode,
          dataset_chunks: settings.datasetChunks,
          model_path: settings.modelPath.trim() ? settings.modelPath : null,
          native_build_policy: settings.nativeBuildPolicy,
          external_tools: externalTools,
          external_timeout_seconds: externalTools
            ? Math.max(1, Math.trunc(settings.externalTimeoutSeconds))
            : undefined,
        },
        settings.apiToken,
      );
      startAnalysis(job, settings.apiToken.trim() ? "polling" : "sse");
    } catch (error) {
      const message = errorMessage(error);
      setValidationMessage(t("analysisSubmitFailed", { message }));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <aside
      className="flex w-full shrink-0 flex-col border-b border-slate-200 bg-surface-50 lg:h-full lg:w-[var(--left-width)] lg:border-b-0 lg:border-r"
      style={{ "--left-width": `${settings.leftColumnWidth}px` } as CSSProperties}
    >
      <div className="border-b border-slate-200 px-4 py-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-950">{t("input")}</h2>
          <Button
            type="button"
            onClick={loadDemo}
            size="icon"
            aria-label={t("loadDemo")}
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
        <div className="mt-3 grid grid-cols-2 rounded-md border border-slate-200 bg-white p-1">
          <button
            type="button"
            onClick={() => updateSettings({ inputMode: "file" })}
            aria-pressed={settings.inputMode === "file"}
            className={`rounded px-3 py-1.5 text-sm font-medium ${settings.inputMode === "file" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}
          >
            {t("fileMode")}
          </button>
          <button
            type="button"
            onClick={() => updateSettings({ inputMode: "project" })}
            aria-pressed={settings.inputMode === "project"}
            className={`rounded px-3 py-1.5 text-sm font-medium ${settings.inputMode === "project" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}
          >
            {t("projectMode")}
          </button>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-auto px-4 py-4">
        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("localPath")}</span>
          <div className="mt-1 flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 focus-within:ring-2 focus-within:ring-audit-teal">
            <FolderOpen className="h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
            <input
              value={settings.inputPath}
              onChange={(event) => updateSettings({ inputPath: event.currentTarget.value })}
              className="min-w-0 flex-1 border-0 bg-transparent text-sm text-text-strong outline-none"
            />
          </div>
        </label>

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("sourceType")}</span>
          <select
            aria-label={t("sourceType")}
            value={settings.importSourceType}
            onChange={(event) =>
              updateSettings({
                importSourceType: event.currentTarget.value as ImportSourceType,
              })
            }
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          >
            {importSourceTypes.map((sourceType) => (
              <option key={sourceType} value={sourceType}>
                {t(
                  sourceType === "local"
                    ? "localSource"
                    : sourceType === "github_archive"
                      ? "githubSource"
                      : sourceType === "etherscan_api"
                        ? "etherscanSource"
                        : "zipSource",
                )}
              </option>
            ))}
          </select>
        </label>

        {settings.importSourceType === "local" ? (
          <label className="block">
            <span className="text-xs font-medium text-slate-600">{t("sourcePreview")}</span>
            <div className="mt-1 flex items-center gap-2 rounded-md border border-dashed border-slate-300 bg-white px-3 py-3">
              <Upload className="h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
              <input
                aria-label={t("sourcePreview")}
                type="file"
                accept=".sol"
                onChange={(event) => handleSourcePreview(event.currentTarget.files?.[0] ?? null)}
                className="min-w-0 flex-1 text-xs text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white"
              />
            </div>
          </label>
        ) : null}

        {settings.importSourceType !== "local" ? (
          <>
            {settings.importSourceType === "zip_base64" ? (
              <label className="block">
                <span className="text-xs font-medium text-slate-600">{t("zipArchive")}</span>
                <div className="mt-1 flex items-center gap-2 rounded-md border border-dashed border-slate-300 bg-white px-3 py-3">
                  <Upload className="h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
                  <input
                    aria-label={t("zipArchive")}
                    type="file"
                    accept=".zip,application/zip"
                    onChange={(event) =>
                      setSourceArchive(event.currentTarget.files?.[0] ?? null)
                    }
                    className="min-w-0 flex-1 text-xs text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white"
                  />
                </div>
              </label>
            ) : (
              <label className="block">
                <span className="text-xs font-medium text-slate-600">
                  {t(
                    settings.importSourceType === "github_archive"
                      ? "githubRepository"
                      : "contractAddress",
                  )}
                </span>
                <input
                  aria-label={t(
                    settings.importSourceType === "github_archive"
                      ? "githubRepository"
                      : "contractAddress",
                  )}
                  value={settings.importSourceValue}
                  onChange={(event) =>
                    updateSettings({ importSourceValue: event.currentTarget.value })
                  }
                  className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
                />
              </label>
            )}

            {settings.importSourceType === "etherscan_api" ? (
              <>
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">
                    {t("explorerHost")}
                  </span>
                  <select
                    aria-label={t("explorerHost")}
                    value={settings.importExplorerHost}
                    onChange={(event) =>
                      updateSettings({
                        importExplorerHost: event.currentTarget.value as typeof settings.importExplorerHost,
                      })
                    }
                    className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
                  >
                    <option value="api.etherscan.io">Ethereum Mainnet</option>
                    <option value="api-sepolia.etherscan.io">Ethereum Sepolia</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-xs font-medium text-slate-600">
                    {t("sourceApiKey")}
                  </span>
                  <input
                    aria-label={t("sourceApiKey")}
                    type="password"
                    value={sourceApiKey}
                    onChange={(event) => setSourceApiKey(event.currentTarget.value)}
                    placeholder={t("optional")}
                    className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-audit-teal"
                  />
                </label>
              </>
            ) : null}

            <button
              type="button"
              onClick={importSource}
              disabled={
                isImporting ||
                isSubmitting ||
                (settings.importSourceType === "zip_base64"
                  ? !sourceArchive
                  : !settings.importSourceValue.trim())
              }
              className="inline-flex w-full items-center justify-center gap-2 rounded-sm border border-border-subtle bg-surface px-3 py-2 text-sm font-medium text-text-strong hover:bg-surface-muted disabled:cursor-not-allowed disabled:text-text-muted focus:outline-none focus:ring-2 focus:ring-audit-teal"
            >
              <Upload className="h-4 w-4" aria-hidden="true" />
              {isImporting ? t("importing") : t("importSource")}
            </button>
          </>
        ) : null}

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("ragMode")}</span>
          <select
            value={settings.ragMode}
            onChange={(event) => updateSettings({ ragMode: event.currentTarget.value as RagMode })}
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          >
            {ragModes.map((mode) => (
              <option key={mode} value={mode}>
                {mode}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("datasetChunks")}</span>
          <input
            value={settings.datasetChunks}
            onChange={(event) => updateSettings({ datasetChunks: event.currentTarget.value })}
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          />
        </label>

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("modelPath")}</span>
          <input
            value={settings.modelPath}
            onChange={(event) => updateSettings({ modelPath: event.currentTarget.value })}
            placeholder={t("optional")}
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          />
        </label>

        <Field label={t("nativeBuildPolicy")}>
          <select
            value={settings.nativeBuildPolicy}
            onChange={(event) =>
              updateSettings({
                nativeBuildPolicy: event.currentTarget.value as typeof settings.nativeBuildPolicy,
              })
            }
            className={fieldControlClass}
          >
            {nativeBuildPolicies.map((policy) => (
              <option key={policy} value={policy}>
                {t(policy === "disabled" ? "safeFallback" : "trustedProjectBuild")}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t("externalTools")}>
          <ToolSelector
            nativeBuildPolicy={settings.nativeBuildPolicy}
            value={settings.externalTools}
            onChange={(externalTools) => updateSettings({ externalTools })}
          />
        </Field>

        <label className="block">
          <span className="text-xs font-medium text-slate-600">
            {t("externalTimeoutSeconds")}
          </span>
          <input
            aria-label={t("externalTimeoutSeconds")}
            type="number"
            min={1}
            step={1}
            value={settings.externalTimeoutSeconds}
            disabled={settings.externalTools.length === 0}
            onChange={(event) => {
              const value = event.currentTarget.valueAsNumber;
              if (Number.isFinite(value)) {
                updateSettings({ externalTimeoutSeconds: value });
              }
            }}
            className="mt-1 w-full rounded-sm border border-border-subtle bg-surface px-3 py-2 text-sm text-text-strong disabled:bg-slate-50 disabled:text-text-muted focus:outline-none focus:ring-2 focus:ring-audit-teal"
          />
        </label>

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("apiToken")}</span>
          <input
            type="password"
            value={settings.apiToken}
            onChange={(event) => updateSettings({ apiToken: event.currentTarget.value })}
            placeholder={t("optional")}
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          />
        </label>

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("leftColumn")}</span>
          <input
            type="range"
            min={260}
            max={360}
            step={20}
            value={settings.leftColumnWidth}
            onChange={(event) => updateSettings({ leftColumnWidth: Number(event.currentTarget.value) })}
            className="mt-2 w-full accent-audit-teal"
          />
        </label>

        <p className="min-h-5 text-xs text-slate-600" role="status">
          {validationMessage}
        </p>
      </div>

      <div className="border-t border-slate-200 p-4">
        <Button
          type="button"
          onClick={submitAnalysis}
          disabled={isSubmitting || isImporting || !settings.inputPath.trim()}
          className="w-full"
          variant="primary"
        >
          <Play className="h-4 w-4" aria-hidden="true" />
          {isSubmitting ? t("submitting") : t("analyze")}
        </Button>
      </div>
    </aside>
  );
}
