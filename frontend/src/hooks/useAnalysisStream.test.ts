import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { defaultSettings, useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import * as api from "../lib/api";
import { demoReport } from "../data/demoReport";
import { useAnalysisStream } from "./useAnalysisStream";

describe("useAnalysisStream", () => {
  beforeEach(() => {
    useAnalysisStore.getState().loadDemo();
    useSettingsStore.setState({
      settings: { ...defaultSettings, apiToken: "stream-token" },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("advances polling to terminal status and loads report", async () => {
    vi.useFakeTimers();
    const getAnalysisMock = vi.spyOn(api, "getAnalysis")
      .mockResolvedValueOnce({
        analysis_id: "analysis-abc",
        status: "queued",
      })
      .mockResolvedValueOnce({
        analysis_id: "analysis-abc",
        status: "running",
      })
      .mockResolvedValueOnce({
        analysis_id: "analysis-abc",
        status: "finding",
        contract_id: "route-contract",
      });

    const getReportMock = vi.spyOn(api, "getReport").mockResolvedValue(demoReport);

    renderHook(() => useAnalysisStream("analysis-abc"));

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    expect(getAnalysisMock).toHaveBeenCalledTimes(3);
    expect(getAnalysisMock).toHaveBeenNthCalledWith(1, "analysis-abc", "stream-token");
    expect(getAnalysisMock).toHaveBeenNthCalledWith(2, "analysis-abc", "stream-token");
    expect(getAnalysisMock).toHaveBeenNthCalledWith(3, "analysis-abc", "stream-token");
    expect(getReportMock).toHaveBeenCalledTimes(1);
    expect(getReportMock).toHaveBeenCalledWith("route-contract", "stream-token");
    expect(useAnalysisStore.getState().job?.status).toBe("finding");
    expect(useAnalysisStore.getState().report.findings).toHaveLength(demoReport.findings.length);
  });

  it("stops polling when unmounted", async () => {
    vi.useFakeTimers();
    const getAnalysisMock = vi.spyOn(api, "getAnalysis").mockResolvedValue({
      analysis_id: "analysis-stop",
      status: "queued",
    });

    const { unmount } = renderHook(() => useAnalysisStream("analysis-stop"));

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    expect(getAnalysisMock).toHaveBeenCalledTimes(1);

    unmount();
    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(getAnalysisMock).toHaveBeenCalledTimes(1);
  });

  it("captures polling failure into store error state", async () => {
    vi.useFakeTimers();
    const getAnalysisMock = vi.spyOn(api, "getAnalysis").mockRejectedValue(
      new Error("temporary stream failure"),
    );

    renderHook(() => useAnalysisStream("analysis-error"));

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    expect(getAnalysisMock).toHaveBeenCalledTimes(1);
    expect(useAnalysisStore.getState().analysisError).toBe("temporary stream failure");
    expect(useAnalysisStore.getState().job).toMatchObject({
      status: "error",
      analysis_id: "analysis-error",
      message: "temporary stream failure",
    });
  });
});
