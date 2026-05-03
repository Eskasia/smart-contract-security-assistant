import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders the audit workbench", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "智能合約安全分析助理" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "開始分析" })).toBeInTheDocument();
    expect(await screen.findByText(/合約 10679f2de6b7/)).toBeInTheDocument();
  });

  it("switches the interface language", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "切換語言" }));

    expect(await screen.findByRole("heading", { name: "Smart Contract Security Assistant" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();
  });
});
