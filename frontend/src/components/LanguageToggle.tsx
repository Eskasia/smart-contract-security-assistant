import { Languages } from "lucide-react";

import { useTranslation } from "../lib/i18n";

export function LanguageToggle() {
  const { locale, t, toggleLocale } = useTranslation();
  const label = locale === "zh" ? "English" : "中文";

  return (
    <button
      type="button"
      onClick={toggleLocale}
      className="inline-flex h-8 items-center gap-2 rounded-md border border-slate-200 bg-white px-2.5 text-xs font-semibold text-slate-800 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-audit-teal"
      aria-label={t("switchLanguage")}
    >
      <Languages className="h-4 w-4" aria-hidden="true" />
      {label}
    </button>
  );
}
