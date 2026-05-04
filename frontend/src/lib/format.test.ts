import { describe, expect, it } from "vitest";

import { formatLocation, formatScore, formatSecurityScore, severityLabel } from "./format";

describe("format helpers", () => {
  it("formats source locations with line ranges", () => {
    expect(
      formatLocation({
        file: "contracts/Vault.sol",
        function: "withdraw",
        line_start: 11,
        line_end: 16,
      }),
    ).toBe("contracts/Vault.sol:11-16");
  });

  it("formats empty judge scores as zero", () => {
    expect(formatScore(undefined)).toBe("0.00/5");
  });

  it("formats empty security score as one hundred", () => {
    expect(formatSecurityScore(undefined)).toBe("100.00/100");
  });

  it("maps numeric severity to labels", () => {
    expect(severityLabel(3)).toBe("High");
  });
});
