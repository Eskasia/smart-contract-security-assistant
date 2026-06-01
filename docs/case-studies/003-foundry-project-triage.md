# Case Study 003 - Foundry Project Triage

Status: current
Updated: 2026-06-01

This case study shows the safe default for a repository-owned Foundry fixture
and the explicit boundary for optional Halmos analysis.

## Safe default

Safe default command:

```bash
uv run scsa analyze tests/fixtures/solidity_projects/foundry \
  --out-dir reports-case-study-003 \
  --native-build-policy disabled
```

In the 2026-06-01 sample run, SCSA classified the input as a Foundry project
directory and did not run Foundry native build scripts. The report metadata
recorded:

- Input kind: `project_directory`
- Project type: `foundry`
- Source files analyzed: `2`
- Native build status: `Native build disabled by policy.`
- solc preparation: `Using system solc 0.8.35 for pragma-compatible 0.8.19.`
- Overall status: `finding`
- Review status: `pending_human_review`
- Human review required: `true`

This is the expected mode for pull requests, imported source, downloaded
archives, and any project where the reviewer has not explicitly accepted the
native build risk.

## Trusted local project mode

Trusted mode is an explicit local action that may execute Foundry project
tooling. Use it only when all of the following are true:

- The project is local and repository-owned.
- The reviewer has inspected `foundry.toml`, remappings, scripts, dependencies,
  and generated artifacts.
- Running native project build tooling is acceptable on the review machine.
- The input is not an imported GitHub, Etherscan, archive, or other third-party
  source bundle.

Trusted local command:

```bash
uv run scsa analyze tests/fixtures/solidity_projects/foundry \
  --out-dir reports-case-study-003-trusted \
  --native-build-policy trusted
```

Do not use trusted native build mode to bypass the safe default for unreviewed
pull request content or imported source.

## Halmos preflight behavior

Halmos is optional and native-build dependent. It requires a trusted Foundry
project.

Safe-default command with Halmos requested:

```bash
uv run scsa analyze tests/fixtures/solidity_projects/foundry \
  --out-dir reports-case-study-003-halmos-disabled \
  --native-build-policy disabled \
  --external-tool halmos
```

The 2026-06-01 sample run did not run Halmos. It added an external-tool preflight
record instead:

```json
{
  "tool_name": "halmos",
  "command": ["halmos"],
  "status": "skipped",
  "findings_count": 0,
  "summary": "halmos requires a trusted Foundry project; skipped optional analysis.",
  "execution_mode": "native build dependent"
}
```

Trusted local Halmos command:

```bash
uv run scsa analyze tests/fixtures/solidity_projects/foundry \
  --out-dir reports-case-study-003-halmos-trusted \
  --native-build-policy trusted \
  --external-tool halmos
```

This command is only appropriate for an explicitly trusted local Foundry
project. If Halmos is unavailable or fails, the report records tool status as
`skipped` or `error`; it does not convert optional symbolic testing into audit
certification.

## Commands

Reproduce the safe-default case study:

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/fixtures/solidity_projects/foundry \
  --out-dir reports-case-study-003 \
  --native-build-policy disabled
```

Confirm the expected finding fields:

```bash
jq '.analysis_metadata.project_type,
    .analysis_metadata.errors,
    .findings[0].finding_id,
    .findings[0].vulnerability_type,
    .findings[0].detector_name,
    .requires_human_review' \
  reports-case-study-003/bf3fc87177ca.json
```

Confirm disabled-mode Halmos preflight behavior:

```bash
uv run scsa analyze tests/fixtures/solidity_projects/foundry \
  --out-dir reports-case-study-003-halmos-disabled \
  --native-build-policy disabled \
  --external-tool halmos

jq '.external_tool_results' \
  reports-case-study-003-halmos-disabled/bf3fc87177ca.json
```

## Expected artifacts

Generated files are local artifacts and are ignored by Git:

- `reports-case-study-003/bf3fc87177ca.json`
- `reports-case-study-003/bf3fc87177ca.md`
- `reports-case-study-003/analysis_trace.sqlite`
- `reports-case-study-003-halmos-disabled/bf3fc87177ca.json`
- `reports-case-study-003-halmos-disabled/bf3fc87177ca.md`
- `reports-case-study-003-halmos-disabled/analysis_trace.sqlite`

Expected report evidence from the safe-default run:

- Contract ID: `bf3fc87177ca`
- Trace ID: `trace_3fe7bca30dd2`
- Finding ID: `f_001`
- Vulnerability: `reentrancy`
- Detector: `reentrancy-eth`
- Severity: `3`
- Location:
  `tests/fixtures/solidity_projects/foundry/src/FoundryVault.sol:6-11`
- Standards: `SC08:2026`, `SCWE-046`, `SCSVS-CODE`, `SWC-107`
- Evidence graph status: `supported`
- Unsupported security claims: `0`
- Exploit validation: `not_attempted`
- Exploit validation mode: `sandbox_only`

Reviewer decision for this fixture:

- Treat `f_001` as a true positive for the repository-owned fixture.
- Require human review before applying the conclusion to production code.
- Keep `--native-build-policy disabled` for untrusted PR or imported input.
- Treat Halmos output as optional supporting evidence, not a final audit result.

## Rejection behavior for imported/untrusted source

Imported sources remain untrusted even when the API server itself is configured
for trusted local analysis. The API forces imported inputs back to
`native_build_policy=disabled`.

API rejection examples:

- A request that tries to upgrade server-disabled policy to
  `native_build_policy=trusted` returns validation error `422`.
- A request with `external_tools: ["halmos"]` and
  `native_build_policy: "disabled"` returns validation error `422` with message
  `halmos requires native_build_policy trusted.`
- Imported GitHub, Etherscan, archive, and remote payload sources must not use
  trusted native build mode.

Minimal API payload that is rejected:

```json
{
  "input_path": "<imported-staging-path>",
  "external_tools": ["halmos"],
  "native_build_policy": "disabled"
}
```

Expected validation message:

```text
halmos requires native_build_policy trusted.
```

## Limitations

- This case study uses a local fixture, not an external adoption example.
- Disabled mode does not execute `forge build`, Foundry scripts, tests, or
  package-manager scripts.
- Trusted mode can run native project tooling and must be explicitly selected.
- Halmos requires a trusted Foundry project and may still be skipped or fail
  depending on local tool installation.
- Imported projects cannot enable trusted native build or Halmos flow.
- SCSA reports analyzer evidence; it does not certify that a Foundry project is
  safe to deploy.
- Business logic, economic risk, dependency risk, and upgrade risk still require
  human review.
