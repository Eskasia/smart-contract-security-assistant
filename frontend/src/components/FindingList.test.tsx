import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { defaultSettings, useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import { demoReport } from "../data/demoReport";
import { FindingList } from "./FindingList";

vi.mock("@tanstack/react-virtual", () => ({
  useVirtualizer: vi.fn((options: { count: number }) => {
    const count = options.count;
    const virtualItems = Array.from({ length: count }, (_, index) => ({
      index,
      key: String(index),
      start: index * 720,
      end: (index + 1) * 720,
      size: 720,
      lane: 0,
    }));
    return {
      getVirtualItems: () => virtualItems,
      getTotalSize: () => count * 720,
      scrollToIndex: vi.fn(),
      measureElement: vi.fn(),
    };
  }),
}));

describe("FindingList", () => {
  let originalRequestAnimationFrame: typeof window.requestAnimationFrame;
  let originalCancelAnimationFrame: typeof window.cancelAnimationFrame;

  beforeEach(() => {
    useAnalysisStore.getState().loadDemo();
    useSettingsStore.setState({ settings: defaultSettings });
    originalRequestAnimationFrame = window.requestAnimationFrame;
    originalCancelAnimationFrame = window.cancelAnimationFrame;
    window.requestAnimationFrame = vi.fn(() => 1);
    window.cancelAnimationFrame = vi.fn();
  });

  afterEach(() => {
    window.requestAnimationFrame = originalRequestAnimationFrame;
    window.cancelAnimationFrame = originalCancelAnimationFrame;
    vi.restoreAllMocks();
  });

  it("focuses the selected finding when deep-link matches it", () => {
    useAnalysisStore.setState({ selectedFindingId: "f_002" });
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");

    render(
      <MemoryRouter initialEntries={["/?finding=f_002"]}>
        <Routes>
          <Route path="/" element={<FindingList findings={demoReport.findings} />} />
        </Routes>
      </MemoryRouter>,
    );

    act(() => {
      // run the requestAnimationFrame callback synchronously
      const callback = (window.requestAnimationFrame as ReturnType<typeof vi.fn>).mock.calls[0]?.[0];
      if (callback) callback(0);
    });

    expect(screen.getByRole("button", { name: /access_control/i })).toBeInTheDocument();
    expect(focusSpy).toHaveBeenCalledWith(expect.objectContaining({ preventScroll: true }));
    expect(useAnalysisStore.getState().selectedFindingId).toBe("f_002");
  });

  it("does not autofocus when deep-link id is missing in findings", () => {
    useAnalysisStore.setState({ selectedFindingId: "f_001" });
    const focusSpy = vi.spyOn(HTMLElement.prototype, "focus");

    render(
      <MemoryRouter initialEntries={["/?finding=not_exists"]}>
        <Routes>
          <Route path="/" element={<FindingList findings={demoReport.findings} />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(focusSpy).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /reentrancy/i })).toBeInTheDocument();
    expect(useAnalysisStore.getState().selectedFindingId).toBe("f_001");
  });
});
