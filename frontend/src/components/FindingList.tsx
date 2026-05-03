import { useVirtualizer } from "@tanstack/react-virtual";
import { memo, useCallback, useRef } from "react";

import { useTranslation } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import type { Finding } from "../types/report";
import { FindingCard } from "./FindingCard";
import { FindingErrorBoundary } from "./FindingErrorBoundary";

export const FindingList = memo(function FindingList({
  findings,
}: {
  findings: Finding[];
}) {
  const { t } = useTranslation();
  const parentRef = useRef<HTMLDivElement>(null);
  const selectedFindingId = useAnalysisStore((state) => state.selectedFindingId);
  const setSelectedFindingId = useAnalysisStore((state) => state.setSelectedFindingId);
  const streamTextByFinding = useAnalysisStore((state) => state.streamTextByFinding);

  const virtualizer = useVirtualizer({
    count: findings.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 720,
    overscan: 3,
  });

  const handleSelect = useCallback(
    (findingId: string) => {
      setSelectedFindingId(findingId);
      const url = new URL(window.location.href);
      url.searchParams.set("finding", findingId);
      window.history.replaceState({}, "", url);
    },
    [setSelectedFindingId],
  );

  if (!findings.length) {
    return (
      <div className="flex h-full items-center justify-center rounded-md border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-600">
        {t("noFindings")}
      </div>
    );
  }

  return (
    <div ref={parentRef} className="h-full overflow-auto pr-2" role="list" aria-label={t("findings")}>
      <div
        className="relative w-full"
        style={{ height: `${virtualizer.getTotalSize()}px` }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const finding = findings[virtualItem.index];
          return (
            <div
              key={virtualItem.key}
              ref={virtualizer.measureElement}
              data-index={virtualItem.index}
              className="absolute left-0 top-0 w-full pb-4"
              style={{ transform: `translateY(${virtualItem.start}px)` }}
              role="listitem"
            >
              <FindingErrorBoundary>
                <FindingCard
                  finding={finding}
                  selected={finding.finding_id === selectedFindingId}
                  onSelect={handleSelect}
                  streamText={streamTextByFinding[finding.finding_id]}
                />
              </FindingErrorBoundary>
            </div>
          );
        })}
      </div>
    </div>
  );
});
