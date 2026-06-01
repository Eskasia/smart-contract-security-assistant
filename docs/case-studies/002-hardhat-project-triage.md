# Case Study 002 - Hardhat Project Triage

Status: current
Updated: 2026-06-01

This case study shows how a maintainer can triage a repository-owned Hardhat
fixture while keeping native project scripts disabled by default.

## Goal

Ground the Hardhat support claim in a reproducible local workflow:

- Identify the Solidity project type.
- Run SCSA with `--native-build-policy disabled`.
- Review generated report and trace artifacts.
- Keep trusted native builds limited to explicitly authorized local projects.

## Input project type

- Fixture: `tests/fixtures/solidity_projects/hardhat`
- Project type: `hardhat`
- Config file: `tests/fixtures/solidity_projects/hardhat/hardhat.config.js`
- Entry contract:
  `tests/fixtures/solidity_projects/hardhat/contracts/HardhatVault.sol`
- Imported contract:
  `tests/fixtures/solidity_projects/hardhat/contracts/lib/SharedVault.sol`
- Source files analyzed: `2`

The fixture contains a cross-file reentrancy pattern: `HardhatVault.withdraw`
sends ETH before clearing `SharedVault.balances[msg.sender]`.

## Native build policy disabled

Safe default command:

```bash
uv run scsa analyze tests/fixtures/solidity_projects/hardhat \
  --out-dir reports-case-study-002 \
  --native-build-policy disabled
```

In the 2026-06-01 sample run, SCSA classified the input as a Hardhat project
directory and did not run Hardhat native build scripts. The report metadata
recorded:

- Input kind: `project_directory`
- Project type: `hardhat`
- Native build status: `Native build disabled by policy.`
- solc preparation: `Using system solc 0.8.35 for pragma-compatible 0.8.19.`
- Overall status: `finding`
- Review status: `pending_human_review`
- Human review required: `true`

This is the expected mode for pull requests, imported source, downloaded
archives, and any project where the maintainer has not explicitly accepted the
native build risk.

## Trusted native build caveat

Trusted mode is an explicit high-risk local action. Use it only when all of the
following are true:

- The project is local and repository-owned.
- The reviewer has inspected the project scripts and dependencies.
- Running Hardhat or package-manager scripts is acceptable on the review
  machine.
- The input is not an imported third-party source bundle.

Example trusted local command:

```bash
uv run scsa analyze tests/fixtures/solidity_projects/hardhat \
  --out-dir reports-case-study-002-trusted \
  --native-build-policy trusted
```

Do not enable trusted native builds for GitHub imports, Etherscan imports,
customer-provided archives, or unreviewed pull request content.

## Commands

Reproduce the safe-default case study:

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/fixtures/solidity_projects/hardhat \
  --out-dir reports-case-study-002 \
  --native-build-policy disabled
```

Inspect the generated local artifacts:

```bash
ls reports-case-study-002
```

Confirm the expected finding fields:

```bash
jq '.analysis_metadata.project_type,
    .analysis_metadata.errors,
    .findings[0].finding_id,
    .findings[0].vulnerability_type,
    .findings[0].detector_name,
    .requires_human_review' \
  reports-case-study-002/8d6e6f506e1f.json
```

## Expected artifacts

Generated files are local artifacts and are ignored by Git:

- `reports-case-study-002/8d6e6f506e1f.json`
- `reports-case-study-002/8d6e6f506e1f.md`
- `reports-case-study-002/analysis_trace.sqlite`

Expected report evidence from the safe-default run:

- Contract ID: `8d6e6f506e1f`
- Trace ID: `trace_895067f4202d`
- Finding ID: `f_001`
- Vulnerability: `reentrancy`
- Detector: `reentrancy-eth`
- Severity: `3`
- Location:
  `tests/fixtures/solidity_projects/hardhat/contracts/HardhatVault.sol:6-11`
- Standards: `SC08:2026`, `SCWE-046`, `SCSVS-CODE`, `SWC-107`
- Evidence graph status: `supported`
- Unsupported security claims: `0`
- Exploit validation: `not_attempted`

Reviewer decision for this fixture:

- Treat `f_001` as a true positive for the repository-owned fixture.
- Require human review before applying the conclusion to production code.
- Keep `--native-build-policy disabled` for untrusted PR or imported input.

## Known limitations

- This case study uses a local fixture, not an external adoption example.
- Disabled mode does not execute Hardhat compile, test, deploy, or package
  scripts.
- Trusted mode can run native project tooling and must be explicitly selected.
- Imported projects must not use trusted native builds.
- SCSA reports analyzer evidence; it does not certify that a Hardhat project is
  safe to deploy.
- Business logic, economic risk, dependency risk, and upgrade risk still require
  human review.
