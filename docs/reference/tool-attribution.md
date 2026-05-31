# Tool Attribution

Updated: 2026-06-01

SCSA is an evidence orchestration and review layer. It integrates with external
security tools but does not claim ownership of their detector, fuzzer, symbolic
execution, or build engines.

Machine-readable attribution lives in `tool_matrix.yml`. This page is the
reviewer-facing summary.

This page tracks external analyzer, fuzzer, symbolic-testing, and build-tool
integrations. Python and npm package dependency licenses are covered by the
generated SBOM/license inventory artifacts under `reports/sbom/` and
`reports/licenses/`.

| Tool | Category | Required | Bundled | License | Role in SCSA |
|---|---|---:|---:|---|---|
| Slither | static analysis | true | false | AGPL-3.0 | Primary deterministic finding source. |
| Aderyn | static analysis | false | false | GPL-3.0 | Optional static finding signal and SARIF artifact source. |
| Echidna | fuzzing | false | false | AGPL-3.0 | Optional property/invariant failure signal. |
| Medusa | fuzzing | false | false | AGPL-3.0 | Optional coverage-guided fuzzer failure signal. |
| Mythril | symbolic execution | false | false | MIT | Optional symbolic issue and SWC signal. |
| Halmos | symbolic testing | false | false | AGPL-3.0 | Optional trusted Foundry proof-failure signal. |
| Foundry | native build | false | false | Apache-2.0 OR MIT | Optional trusted project build preflight. |
| Hardhat | native build | false | false | MIT | Optional trusted project build preflight. |

## Consumption Boundary

- Findings created by external tools are normalized into SCSA's report schema.
- External raw output and artifact paths remain traceable.
- A missing optional tool is recorded as `skipped`, not silently converted into a failed SCSA finding.
- Halmos requires trusted Foundry mode; imported or untrusted sources cannot enable that path.

## Maintainer Checklist

- Add every new external tool to `tool_matrix.yml`.
- Add every new external tool to `THIRD_PARTY_NOTICES.md`.
- Keep README wording aligned with the matrix.
- Keep dependency license wording aligned with generated SBOM/license artifacts.
- Run `uv run python scripts/check_tool_matrix.py` before merging attribution changes.
