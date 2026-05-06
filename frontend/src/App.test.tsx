import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { App } from "./App";
import { FindingCard } from "./components/FindingCard";
import { demoReport } from "./data/demoReport";
import { useAnalysisStore } from "./store/analysisStore";

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    useAnalysisStore.getState().loadDemo();
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
});
