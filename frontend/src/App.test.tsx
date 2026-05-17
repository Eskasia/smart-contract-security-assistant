import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { FindingCard } from "./components/FindingCard";
import { InputPanel } from "./components/InputPanel";
import { ReviewerPanel } from "./components/ReviewerPanel";
import { demoReport } from "./data/demoReport";
import { defaultSettings, useAnalysisStore, useSettingsStore } from "./store/analysisStore";

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

describe("App", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    window.history.pushState({}, "", "/");
    localStorage.clear();
    useAnalysisStore.getState().loadDemo();
    useSettingsStore.setState({ settings: defaultSettings });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    window.history.pushState({}, "", "/");
  });

  it("renders the audit workbench", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "智能合約安全分析助理" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "開始分析" })).toBeInTheDocument();
    expect(await screen.findByText(/合約 10679f2de6b7/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "0G Proof" })).not.toBeInTheDocument();
  });

  it("renders dry-run 0G proof details when report metadata contains a proof", async () => {
    useAnalysisStore.getState().setReport({
      ...demoReport,
      analysis_metadata: {
        ...demoReport.analysis_metadata,
        zero_g_proof: {
          storage_root_hash: "0xabababababababababababababababababababababababababababababababab",
          storage_tx_hash: "dry-run-only",
          registry_address: "pending-live-registry",
          registry_tx_hash: "pending-live-registration",
          explorer_links: {},
        },
      },
    });
    render(<App />);

    expect(screen.getByRole("heading", { name: "0G Proof" })).toBeInTheDocument();
    expect(screen.getByText("dry-run-only")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Storage tx" })).not.toBeInTheDocument();
  });

  it("switches the interface language", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "切換語言" }));

    expect(await screen.findByRole("heading", { name: "Smart Contract Security Assistant" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();
  });

  it("loads a report route and selects the requested finding from the query string", async () => {
    const routedReport = { ...demoReport, contract_id: "route-contract" };
    useSettingsStore.setState({
      settings: { ...defaultSettings, apiToken: "route-token" },
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/reports/route-contract") {
        return new Response(JSON.stringify(routedReport), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/reports/route-contract?finding=f_002");

    render(<App />);

    expect(await screen.findByText(/合約 route-contract/)).toBeInTheDocument();
    await waitFor(() => expect(useAnalysisStore.getState().selectedFindingId).toBe("f_002"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/reports/route-contract",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer route-token",
        }),
      }),
    );
    expect(window.location.search).toBe("?finding=f_002");
  });

  it("keeps default finding selection when a routed deep-link finding id is invalid", async () => {
    const routedReport = { ...demoReport, contract_id: "route-contract" };
    useSettingsStore.setState({
      settings: { ...defaultSettings, apiToken: "route-token" },
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/reports/route-contract") {
        return new Response(JSON.stringify(routedReport), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.startsWith("/api/traces/")) {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/reports/route-contract?finding=missing");

    render(<App />);

    expect(await screen.findByText(/合約 route-contract/)).toBeInTheDocument();
    await waitFor(() => expect(useAnalysisStore.getState().selectedFindingId).toBe("f_001"));
    await waitFor(() => expect(window.location.search).toBe(""));
  });

  it("sends finding review PATCH with explicit in-memory API token", async () => {
    const routedReport = { ...demoReport, contract_id: "route-contract" };
    useSettingsStore.setState({
      settings: { ...defaultSettings, apiToken: "route-token" },
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/reports/route-contract") {
        return new Response(JSON.stringify(routedReport), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url === "/api/traces/trace_6cb6648b074e?finding_id=f_001") {
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url === "/api/reports/route-contract/findings/f_001/review") {
        return new Response(
          JSON.stringify({
            report: routedReport,
            finding: routedReport.findings[0],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/reports/route-contract?finding=f_001");

    render(<App />);

    const findingCard = await screen.findByRole("article", { name: "f_001" });
    const findingReviewNoteInput = within(findingCard).getByLabelText(/審核備註|Review note/);
    const findingSaveButton = within(findingCard).getByRole("button", {
      name: /儲存 finding 審核|Save finding review/,
    });

    fireEvent.change(findingReviewNoteInput, {
      target: { value: "reviewed in memory" },
    });
    fireEvent.click(findingSaveButton);

    await waitFor(() => expect(findingCard).toHaveTextContent(/已儲存。|Saved\./));
    const reviewPatchCall = fetchMock.mock.calls.find(([nextUrl]) =>
      String(nextUrl).includes("/api/reports/route-contract/findings/f_001/review"),
    );
    expect(reviewPatchCall).toBeDefined();
    const reviewHeaders = reviewPatchCall?.[1]?.headers as Record<string, string> | undefined;
    expect(reviewHeaders).toMatchObject({
      "Content-Type": "application/json",
      Authorization: "Bearer route-token",
    });
  });

  it("keeps routed report failures on an empty route state with a sanitized message", async () => {
    const fetchMock = vi.fn(async () => new Response(
      JSON.stringify({
        error: {
          code: "UNAUTHORIZED",
          message: "stack trace /Users/william/private-token",
        },
      }),
      {
        status: 401,
        headers: { "Content-Type": "application/json" },
      },
    ));
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/reports/private-contract");

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "無法載入報告 private-contract：HTTP 401: Authentication failed.",
    );
    expect(screen.queryByText(/合約 10679f2de6b7/)).not.toBeInTheDocument();
    expect(screen.getByText("沒有 mapped findings。")).toBeInTheDocument();
    expect(screen.queryByText(/private-token|UNAUTHORIZED|stack trace/)).not.toBeInTheDocument();
  });

  it("shows submit failure without falling back to demo report", async () => {
    useAnalysisStore.getState().startRouteLoad("route-before-submit");
    const fetchMock = vi.fn(async () => new Response(
      JSON.stringify({
        error: {
          code: "SERVER_ERROR",
          message: "raw backend stack",
        },
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    ));
    vi.stubGlobal("fetch", fetchMock);

    render(<InputPanel />);

    fireEvent.click(screen.getByRole("button", { name: "開始分析" }));

    expect(await screen.findByText("分析送出失敗：HTTP 500: Server error.")).toBeInTheDocument();
    expect(useAnalysisStore.getState().report.contract_id).toBe("route-before-submit");
    expect(useAnalysisStore.getState().connectionMode).toBe("polling");
    expect(screen.queryByText(/raw backend stack|SERVER_ERROR/)).not.toBeInTheDocument();
  });

  it("saves finding-level review feedback locally when the API is unavailable", async () => {
    useAnalysisStore.getState().setReport(demoReport);
    render(
      <FindingCard
        finding={demoReport.findings[0]}
        selected={true}
        onSelect={() => undefined}
      />,
    );

    const reviewSelect = (await screen.findAllByLabelText(
      /Finding 審核狀態|Finding review status/,
    ))[0];
    fireEvent.change(reviewSelect, { target: { value: "false_positive" } });
    fireEvent.change(screen.getAllByLabelText(/審核備註|Review note/)[0], {
      target: { value: "測試 fixture 誤報" },
    });
    fireEvent.click(
      screen.getAllByRole("button", { name: /儲存 finding 審核|Save finding review/ })[0],
    );

    expect(await screen.findByText(/已儲存在本機。|Saved locally./)).toBeInTheDocument();
  });

  it("clears transient report state when a new analysis starts", () => {
    useAnalysisStore.getState().setTraceRows(demoReport.findings.map((finding) => ({
      trace_id: "trace_001",
      finding_id: finding.finding_id,
      detector_name: finding.detector_name,
      rag_mode: "fallback",
      retrieval_duration_ms: 1,
      llm_duration_ms: 1,
      chunks_used: 1,
      slither_raw: "{}",
      normalized_finding: "{}",
      rag_chunk_ids: "[]",
      packed_prompt: "sensitive prompt",
      llm_raw_output: "{}",
      schema_valid: true,
      retry_count: 0,
      partial: false,
    })));
    useAnalysisStore.getState().appendFindingToken("f_001", "old token");

    useAnalysisStore.getState().startAnalysis(
      { analysis_id: "analysis_new", status: "queued" },
      "polling",
    );

    const state = useAnalysisStore.getState();
    expect(state.report.findings).toHaveLength(0);
    expect(state.traceRows).toHaveLength(0);
    expect(state.streamTextByFinding).toEqual({});
    expect(state.selectedFindingId).toBe("");
  });

  it("keeps the pending report status synchronized with job updates", () => {
    useAnalysisStore.getState().startAnalysis(
      { analysis_id: "analysis_pending", status: "queued" },
      "polling",
    );

    useAnalysisStore.getState().setJob({
      analysis_id: "analysis_pending",
      status: "running",
      message: "Slither running",
    });

    expect(useAnalysisStore.getState().report.overall_status).toBe("running");
    expect(useAnalysisStore.getState().report.review_reason).toBe("Slither running");
  });

  it("clears streamed finding text when the final report is committed", () => {
    useAnalysisStore.getState().appendFindingToken("f_001", "partial explanation");

    useAnalysisStore.getState().setReport(demoReport);

    expect(useAnalysisStore.getState().streamTextByFinding).toEqual({});
  });

  it("sends report review PATCH with explicit in-memory API token", async () => {
    useSettingsStore.setState({
      settings: { ...defaultSettings, apiToken: "review-token" },
    });
    useAnalysisStore.getState().setConnectionMode("polling");
    useAnalysisStore.getState().setReport(demoReport);
    const reviewedReport = { ...demoReport, review_status: "approved" as const };
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input) === `/api/reports/${demoReport.contract_id}/review`) {
        return new Response(JSON.stringify({ report: reviewedReport }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({}), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ReviewerPanel />);

    fireEvent.change(screen.getByLabelText(/審核狀態|Review status/), {
      target: { value: "approved" },
    });
    fireEvent.click(screen.getByRole("button", { name: /儲存|Save/ }));

    await waitFor(() => expect(screen.getByText(/已儲存。|Saved\./)).toBeInTheDocument());
    expect(useAnalysisStore.getState().report.review_status).toBe("approved");
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/reports/${demoReport.contract_id}/review`,
      expect.objectContaining({
        method: "PATCH",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer review-token",
        }),
      }),
    );
  });

  it("disables global review saving while an analysis report is pending", () => {
    useAnalysisStore.getState().startAnalysis(
      { analysis_id: "analysis_pending", status: "queued" },
      "polling",
    );

    render(<ReviewerPanel />);

    expect(screen.getByRole("button", { name: /儲存|Save/ })).toBeDisabled();
    expect(screen.getByText(/報告完成後才能儲存審核。|Save review after the report is complete./)).toBeInTheDocument();
  });

  it("keeps global review disabled after analysis fails before a report is committed", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    useAnalysisStore.getState().startAnalysis(
      { analysis_id: "analysis_error", status: "queued" },
      "polling",
    );
    useAnalysisStore.getState().setJob({
      analysis_id: "analysis_error",
      status: "error",
      message: "HTTP 500: Server error.",
    });

    render(<ReviewerPanel />);

    const saveButton = screen.getByRole("button", { name: /儲存|Save/ });
    expect(saveButton).toBeDisabled();
    fireEvent.click(saveButton);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.getByText(/報告完成後才能儲存審核。|Save review after the report is complete./)).toBeInTheDocument();
  });
});
