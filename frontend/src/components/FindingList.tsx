import { useVirtualizer } from "@tanstack/react-virtual";
import { memo, useCallback, useEffect, useMemo, useRef } from "react";
import { useSearchParams } from "react-router-dom";

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
  const itemRefs = useRef(new Map<string, HTMLDivElement>());
  const lastUrlSyncedFindingId = useRef("");
  const selectedFindingId = useAnalysisStore((state) => state.selectedFindingId);
  const setSelectedFindingId = useAnalysisStore((state) => state.setSelectedFindingId);
  const streamTextByFinding = useAnalysisStore((state) => state.streamTextByFinding);
  const [searchParams, setSearchParams] = useSearchParams();
  const findingIndexById = useMemo(
    () => new Map(findings.map((finding, index) => [finding.finding_id, index])),
    [findings],
  );

  useEffect(() => {
    lastUrlSyncedFindingId.current = "";
  }, [findings]);

  const virtualizer = useVirtualizer({
    count: findings.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 720,
    overscan: 3,
  });

  const handleSelect = useCallback(
    (findingId: string) => {
      setSelectedFindingId(findingId);
      const nextSearchParams = new URLSearchParams(searchParams);
      nextSearchParams.set("finding", findingId);
      setSearchParams(nextSearchParams, { replace: true });
    },
    [searchParams, setSearchParams, setSelectedFindingId],
  );

  useEffect(() => {
    if (!selectedFindingId) return;
    const urlFindingId = searchParams.get("finding") ?? "";
    if (urlFindingId !== selectedFindingId) {
      if (!urlFindingId) lastUrlSyncedFindingId.current = "";
      return;
    }
    if (lastUrlSyncedFindingId.current === selectedFindingId) return;
    const findingIndex = findingIndexById.get(selectedFindingId);
    if (findingIndex === undefined) return;
    lastUrlSyncedFindingId.current = selectedFindingId;

    virtualizer.scrollToIndex(findingIndex, { align: "center" });

    let cancelled = false;
    let frameId = 0;
    let attempts = 0;

    const focusSelectedTrigger = () => {
      if (cancelled) return;
      const findingRow = itemRefs.current.get(selectedFindingId);
      const trigger = findingRow?.querySelector<HTMLButtonElement>("button");
      if (trigger) {
        trigger.focus({ preventScroll: true });
        return;
      }
      if (attempts >= 8) return;
      attempts += 1;
      frameId = window.requestAnimationFrame(focusSelectedTrigger);
    };

    frameId = window.requestAnimationFrame(focusSelectedTrigger);

    return () => {
      cancelled = true;
      window.cancelAnimationFrame(frameId);
    };
  }, [findingIndexById, searchParams, selectedFindingId, virtualizer]);

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
              ref={(node) => {
                if (node) {
                  itemRefs.current.set(finding.finding_id, node);
                  virtualizer.measureElement(node);
                  return;
                }
                itemRefs.current.delete(finding.finding_id);
              }}
              data-index={virtualItem.index}
              data-finding-id={finding.finding_id}
              data-selected={finding.finding_id === selectedFindingId ? "true" : undefined}
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
