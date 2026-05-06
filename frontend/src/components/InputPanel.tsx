import { FolderOpen, Play, RotateCcw, Upload } from "lucide-react";
import { type CSSProperties, useState } from "react";

import { createAnalysis } from "../lib/api";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import type { RagMode } from "../types/report";
import { usePersistedSettings } from "../hooks/usePersistedSettings";

const ragModes: RagMode[] = ["quality", "balanced", "fast", "fallback"];
const nativeBuildPolicies = ["trusted", "disabled"] as const;

export function InputPanel() {
  const { settings, updateSettings } = usePersistedSettings();
  const { t } = useTranslation();
  const setJob = useAnalysisStore((state) => state.setJob);
  const setConnectionMode = useAnalysisStore((state) => state.setConnectionMode);
  const loadDemo = useAnalysisStore((state) => state.loadDemo);
  const [validationMessage, setValidationMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  async function submitAnalysis() {
    setIsSubmitting(true);
    setValidationMessage("");
    try {
      const job = await createAnalysis({
        input_path: settings.inputPath,
        rag_mode: settings.ragMode,
        dataset_chunks: settings.datasetChunks,
        model_path: settings.modelPath.trim() ? settings.modelPath : null,
        native_build_policy: settings.nativeBuildPolicy,
      }, settings.apiToken);
      setJob(job);
      setConnectionMode(settings.apiToken.trim() ? "polling" : "sse");
    } catch {
      loadDemo();
      setValidationMessage(t("apiFallback"));
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
          <button
            type="button"
            onClick={loadDemo}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-audit-teal"
            aria-label={t("loadDemo")}
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        <div className="mt-3 grid grid-cols-2 rounded-md border border-slate-200 bg-white p-1">
          <button
            type="button"
            onClick={() => updateSettings({ inputMode: "file" })}
            className={`rounded px-3 py-1.5 text-sm font-medium ${settings.inputMode === "file" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}
          >
            {t("fileMode")}
          </button>
          <button
            type="button"
            onClick={() => updateSettings({ inputMode: "project" })}
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
              className="min-w-0 flex-1 border-0 bg-transparent text-sm text-slate-900 outline-none"
            />
          </div>
        </label>

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("sourcePreview")}</span>
          <div className="mt-1 flex items-center gap-2 rounded-md border border-dashed border-slate-300 bg-white px-3 py-3">
            <Upload className="h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
            <input
              type="file"
              accept=".sol"
              onChange={(event) => handleSourcePreview(event.currentTarget.files?.[0] ?? null)}
              className="min-w-0 flex-1 text-xs text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white"
            />
          </div>
        </label>

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

        <label className="block">
          <span className="text-xs font-medium text-slate-600">{t("nativeBuildPolicy")}</span>
          <select
            value={settings.nativeBuildPolicy}
            onChange={(event) =>
              updateSettings({
                nativeBuildPolicy: event.currentTarget.value as typeof settings.nativeBuildPolicy,
              })
            }
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          >
            {nativeBuildPolicies.map((policy) => (
              <option key={policy} value={policy}>
                {t(policy === "disabled" ? "safeFallback" : "trustedProjectBuild")}
              </option>
            ))}
          </select>
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

        <p className="min-h-5 text-xs text-slate-600" aria-live="polite">
          {validationMessage}
        </p>
      </div>

      <div className="border-t border-slate-200 p-4">
        <button
          type="button"
          onClick={submitAnalysis}
          disabled={isSubmitting || !settings.inputPath.trim()}
          className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400 focus:outline-none focus:ring-2 focus:ring-audit-teal"
        >
          <Play className="h-4 w-4" aria-hidden="true" />
          {isSubmitting ? t("submitting") : t("analyze")}
        </button>
      </div>
    </aside>
  );
}
