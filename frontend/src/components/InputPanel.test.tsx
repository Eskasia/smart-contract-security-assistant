import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { InputPanel } from "./InputPanel";
import { defaultSettings, useAnalysisStore, useSettingsStore } from "../store/analysisStore";

describe("InputPanel", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
    useAnalysisStore.getState().loadDemo();
    useSettingsStore.setState({ settings: defaultSettings });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("imports a GitHub source and reuses the returned path for analysis with Echidna enabled", async () => {
    useSettingsStore.setState({
      settings: {
        ...defaultSettings,
        apiToken: "runtime-token",
        nativeBuildPolicy: "trusted",
      },
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/imports") {
        return new Response(JSON.stringify({ input_path: "/tmp/imports/repo/Vault.sol" }), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url === "/api/analyses") {
        return new Response(JSON.stringify({ analysis_id: "analysis_123", status: "queued" }), {
          status: 202,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`Unexpected URL: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<InputPanel />);

    fireEvent.change(screen.getByLabelText("來源類型"), {
      target: { value: "github_archive" },
    });
    fireEvent.change(screen.getByLabelText("GitHub repository"), {
      target: { value: "https://github.com/org/repo" },
    });
    fireEvent.click(screen.getByRole("button", { name: "匯入來源" }));

    await waitFor(() => {
      expect(useSettingsStore.getState().settings.inputPath).toBe("/tmp/imports/repo/Vault.sol");
      expect(useSettingsStore.getState().settings.nativeBuildPolicy).toBe("disabled");
    });

    fireEvent.click(screen.getByLabelText("Echidna"));
    fireEvent.change(screen.getByLabelText("外部逾時（秒）"), {
      target: { value: "90" },
    });
    fireEvent.click(screen.getByRole("button", { name: "開始分析" }));

    await waitFor(() =>
      expect(useAnalysisStore.getState().job?.analysis_id).toBe("analysis_123"),
    );

    const importRequest = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(importRequest?.headers).toMatchObject({
      Authorization: "Bearer runtime-token",
      "Content-Type": "application/json",
    });
    expect(JSON.parse(String(importRequest?.body))).toMatchObject({
      source_kind: "github_archive",
      repository: "https://github.com/org/repo",
    });

    const analysisRequest = fetchMock.mock.calls[1]?.[1] as RequestInit | undefined;
    expect(analysisRequest?.headers).toMatchObject({
      Authorization: "Bearer runtime-token",
      "Content-Type": "application/json",
    });
    expect(JSON.parse(String(analysisRequest?.body))).toMatchObject({
      input_path: "/tmp/imports/repo/Vault.sol",
      external_tools: ["echidna"],
      external_timeout_seconds: 90,
    });
  });

  it("uploads zip archives through the import workflow as base64 JSON", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/imports") {
        return new Response(JSON.stringify({ input_path: "/tmp/imports/archive/Vault.sol" }), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`Unexpected URL: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<InputPanel />);

    fireEvent.change(screen.getByLabelText("來源類型"), {
      target: { value: "zip_base64" },
    });

    const archive = new File(["zip-bytes"], "contracts.zip", { type: "application/zip" });
    fireEvent.change(screen.getByLabelText("ZIP 檔"), {
      target: { files: [archive] },
    });
    fireEvent.click(screen.getByRole("button", { name: "匯入來源" }));

    await waitFor(() =>
      expect(useSettingsStore.getState().settings.inputPath).toBe(
        "/tmp/imports/archive/Vault.sol",
      ),
    );

    const importRequest = fetchMock.mock.calls[0]?.[1] as RequestInit | undefined;
    expect(importRequest?.headers).toMatchObject({
      "Content-Type": "application/json",
    });
    expect(JSON.parse(String(importRequest?.body))).toMatchObject({
      source_kind: "zip_base64",
      archive_name: "contracts.zip",
      archive_base64: "emlwLWJ5dGVz",
    });
  });
});
