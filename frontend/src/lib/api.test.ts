import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiRequestError,
  createAnalysis,
  createImport,
  getReport,
  getReportMarkdown,
  getTrace,
  patchFindingReview,
} from "./api";

describe("createAnalysis", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("sends native build policy, external tools, and API token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ analysis_id: "analysis_001", status: "queued" }), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await createAnalysis(
      {
        input_path: "tests/contracts/VulnerableVault.sol",
        rag_mode: "fallback",
        dataset_chunks: "data/dataset_v1.0/chunks/chunks.jsonl",
        model_path: null,
        native_build_policy: "disabled",
        external_tools: ["echidna"],
        external_timeout_seconds: 90,
      },
      "dev-token",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/analyses",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer dev-token",
        }),
        body: JSON.stringify({
          input_path: "tests/contracts/VulnerableVault.sol",
          rag_mode: "fallback",
          dataset_chunks: "data/dataset_v1.0/chunks/chunks.jsonl",
          model_path: null,
          native_build_policy: "disabled",
          external_tools: ["echidna"],
          external_timeout_seconds: 90,
        }),
      }),
    );
  });

  it("sends typed JSON import requests with explicit API tokens only", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ input_path: "/tmp/imports/repo/Vault.sol" }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await createImport(
      {
        source_kind: "etherscan_api",
        contract_address: "0x1234",
        explorer_host: "api.etherscan.io",
        api_key: "etherscan-key",
      },
      "runtime-token",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/imports",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          Authorization: "Bearer runtime-token",
        }),
        body: JSON.stringify({
          source_kind: "etherscan_api",
          contract_address: "0x1234",
          explorer_host: "api.etherscan.io",
          api_key: "etherscan-key",
        }),
      }),
    );
  });

  it("encodes zip archives as base64 JSON payloads", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ input_path: "/tmp/imports/archive/Vault.sol" }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await createImport({
      source_kind: "zip_base64",
      archive_base64: "emlwLWJ5dGVz",
      archive_name: "contracts.zip",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/imports",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
        body: JSON.stringify({
          source_kind: "zip_base64",
          archive_base64: "emlwLWJ5dGVz",
          archive_name: "contracts.zip",
        }),
      }),
    );
  });

  it("encodes dynamic path segments", async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(
      new Response(JSON.stringify({}), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ));
    vi.stubGlobal("fetch", fetchMock);

    await getReport("contract/../x");
    await getReportMarkdown("contract/../x");
    await getTrace("trace/001", "finding/001");
    await patchFindingReview("contract/../x", "finding/001", {
      review_status: "false_positive",
      review_note: "safe",
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/reports/contract%2F..%2Fx",
      expect.any(Object),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/reports/contract%2F..%2Fx/markdown",
      expect.any(Object),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/traces/trace%2F001?finding_id=finding%2F001",
      expect.any(Object),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "/api/reports/contract%2F..%2Fx/findings/finding%2F001/review",
      expect.objectContaining({
        method: "PATCH",
      }),
    );
  });

  it("uses only explicit API tokens", async () => {
    window.localStorage.setItem(
      "sca_settings_v1",
      JSON.stringify({ state: { settings: { apiToken: "persisted-token" } } }),
    );
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(
      new Response(JSON.stringify({}), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ));
    vi.stubGlobal("fetch", fetchMock);

    await getReport("contract_001");
    await getReport("contract_001", "runtime-token");
    await getReportMarkdown("contract_001", "runtime-token");

    const firstHeaders = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    const secondHeaders = fetchMock.mock.calls[1][1].headers as Record<string, string>;
    const thirdHeaders = fetchMock.mock.calls[2][1].headers as Record<string, string>;
    expect(firstHeaders.Authorization).toBeUndefined();
    expect(secondHeaders.Authorization).toBe("Bearer runtime-token");
    expect(thirdHeaders.Authorization).toBe("Bearer runtime-token");
  });

  it("does not expose raw error response bodies in thrown messages", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "INTERNAL",
            message: "stack trace /Users/william/secret",
          },
        }),
        { status: 500, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getReport("contract_001")).rejects.toMatchObject({
      name: "ApiRequestError",
      status: 500,
      message: "HTTP 500: Server error.",
    } satisfies Partial<ApiRequestError>);
  });
});
