import { CheckCircle2, FlaskConical, ScanSearch, ShieldCheck, Sigma } from "lucide-react";

import { useTranslation } from "../../lib/i18n";
import type { ExternalToolName, NativeBuildPolicy } from "../../types/report";

const toolRows: Array<{
  descriptionKey:
    | "aderynDescription"
    | "echidnaDescription"
    | "medusaDescription"
    | "halmosDescription";
  icon: typeof ScanSearch;
  labelKey: "aderyn" | "echidna" | "medusa" | "halmos";
  name: ExternalToolName;
  requiresTrusted?: boolean;
}> = [
  {
    name: "aderyn",
    labelKey: "aderyn",
    descriptionKey: "aderynDescription",
    icon: ScanSearch,
  },
  {
    name: "echidna",
    labelKey: "echidna",
    descriptionKey: "echidnaDescription",
    icon: FlaskConical,
  },
  {
    name: "medusa",
    labelKey: "medusa",
    descriptionKey: "medusaDescription",
    icon: Sigma,
  },
  {
    name: "halmos",
    labelKey: "halmos",
    descriptionKey: "halmosDescription",
    icon: ShieldCheck,
    requiresTrusted: true,
  },
];

export function ToolSelector({
  nativeBuildPolicy,
  onChange,
  value,
}: {
  nativeBuildPolicy: NativeBuildPolicy;
  onChange: (tools: ExternalToolName[]) => void;
  value: ExternalToolName[];
}) {
  const { t } = useTranslation();
  const selected = new Set(value);

  function toggle(tool: ExternalToolName, disabled: boolean) {
    if (disabled) return;
    const next = selected.has(tool)
      ? value.filter((item) => item !== tool)
      : [...value, tool];
    onChange(next);
  }

  return (
    <div className="space-y-2">
      {toolRows.map((tool) => {
        const Icon = tool.icon;
        const disabled = Boolean(tool.requiresTrusted && nativeBuildPolicy !== "trusted");
        const checked = selected.has(tool.name) && !disabled;
        return (
          <button
            key={tool.name}
            type="button"
            aria-pressed={checked}
            aria-label={t(tool.labelKey)}
            disabled={disabled}
            onClick={() => toggle(tool.name, disabled)}
            className={`w-full rounded-md border p-3 text-left transition focus:outline-none focus:ring-2 focus:ring-audit-teal disabled:cursor-not-allowed ${
              checked
                ? "border-audit-teal bg-emerald-50"
                : "border-border-subtle bg-surface hover:bg-surface-muted"
            } ${disabled ? "opacity-55" : ""}`}
          >
            <span className="flex items-start gap-3">
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-audit-teal" aria-hidden="true" />
              <span className="min-w-0 flex-1">
                <span className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-text-strong">{t(tool.labelKey)}</span>
                  {checked ? (
                    <CheckCircle2 className="h-4 w-4 text-audit-green" aria-hidden="true" />
                  ) : null}
                </span>
                <span className="mt-1 block text-xs leading-5 text-text-muted">
                  {t(tool.descriptionKey)}
                </span>
                {disabled ? (
                  <span className="mt-1 block text-xs font-medium text-audit-amber">
                    {t("halmosRequiresTrusted")}
                  </span>
                ) : null}
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

