import ReactDiffViewer from "react-diff-viewer-continued";

import { useTranslation } from "../lib/i18n";

export function DiffViewerPanel({
  oldValue,
  newValue,
  splitView,
}: {
  oldValue: string;
  newValue: string;
  splitView: boolean;
}) {
  const { t } = useTranslation();

  if (!newValue.trim()) {
    return (
      <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
        {t("remediationUnavailable")}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-slate-200 text-xs">
      <ReactDiffViewer
        oldValue={oldValue}
        newValue={newValue}
        splitView={splitView}
        useDarkTheme={false}
        hideLineNumbers={false}
        styles={{
          variables: {
            light: {
              diffViewerBackground: "#ffffff",
              addedBackground: "#ecfdf5",
              removedBackground: "#fff1f2",
              wordAddedBackground: "#bbf7d0",
              wordRemovedBackground: "#fecdd3",
              addedGutterBackground: "#d1fae5",
              removedGutterBackground: "#ffe4e6",
              gutterBackground: "#f8fafc",
              gutterBackgroundDark: "#f8fafc",
              highlightBackground: "#fefce8",
              highlightGutterBackground: "#fef3c7",
              codeFoldGutterBackground: "#f8fafc",
              codeFoldBackground: "#f8fafc",
              emptyLineBackground: "#ffffff",
              gutterColor: "#475569",
              addedGutterColor: "#166534",
              removedGutterColor: "#991b1b",
              codeFoldContentColor: "#475569",
              diffViewerTitleBackground: "#f8fafc",
              diffViewerTitleColor: "#0f172a",
              diffViewerTitleBorderColor: "#e2e8f0",
            },
          },
          contentText: {
            fontFamily:
              "JetBrains Mono, SFMono-Regular, Consolas, Liberation Mono, monospace",
            fontSize: "12px",
            lineHeight: "18px",
          },
        }}
      />
    </div>
  );
}
