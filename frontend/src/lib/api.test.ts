import { afterEach, describe, expect, it, vi } from "vitest";

import { createAnalysis } from "./api";

describe("createAnalysis", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends native build policy and API token", async () => {
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
        }),
      }),
    );
  });
});
