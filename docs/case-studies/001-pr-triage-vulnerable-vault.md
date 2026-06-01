# Case Study 001 - VulnerableVault PR Triage

Status: current
Updated: 2026-06-01

This case study shows how a maintainer can use SCSA to triage a Solidity pull
request with an intentionally vulnerable local fixture.

## Goal

Demonstrate a complete PR triage path from analyzer command to report evidence,
trace evidence, and reviewer decision for `tests/contracts/VulnerableVault.sol`.

## Authorization Boundary

The input is a repository-owned test fixture. Do not use this workflow on
external repositories, third-party contracts, customer code, or private audit
material unless you are explicitly authorized to review that code.

## Input

- Fixture: `tests/contracts/VulnerableVault.sol`
- Contract: `VulnerableVault`
- Function under review: `withdraw`
- Fixture status: intentionally vulnerable

The fixture writes `balances[msg.sender] = 0` after sending ETH with
`msg.sender.call{value: amount}("")`, which is the expected reentrancy pattern.

## Commands

```bash
uv run scsa analyze tests/contracts/VulnerableVault.sol \
  --out-dir reports-case-study-001 \
  --native-build-policy disabled
```

Generated `reports-case-study-001/` files are local artifacts and are ignored by
Git. Tracked evidence for this case study is limited to sanitized excerpts:

- `docs/case-studies/artifacts/001-report-summary.md`
- `docs/case-studies/artifacts/001-trace-summary.md`

## Expected Finding

- Expected vulnerability: reentrancy
- Expected detector: `reentrancy-eth`
- Expected finding id: `f_001`
- Expected severity: `3`
- Expected status: `finding`
- Human review required: yes

## Report Evidence

The 2026-06-01 sample run produced:

- Contract ID: `3fca00c06c2f`
- Status: `finding`
- Reviewer status: `pending_human_review`
- Security score: `73.00/100`
- Finding location: `tests/contracts/VulnerableVault.sol:11-16`
- Standards: `SC08:2026`, `SCWE-046`, `SCSVS-CODE`, `SWC-107`
- External tools: none executed

See `docs/case-studies/artifacts/001-report-summary.md` for the sanitized
report excerpt.

## Trace Evidence

The 2026-06-01 sample run produced one trace row for `f_001`.

Sanitized trace evidence:

- Trace final status: `finding`
- Finding rows: `1`
- Detector: `reentrancy-eth`
- RAG chunks used: `3`
- Schema valid: `true`
- Review status: `unreviewed`
- Unsupported security claims: `0`

See `docs/case-studies/artifacts/001-trace-summary.md` for the sanitized trace
excerpt.

## Reviewer Decision

Suggested reviewer decision for this fixture:

- Treat `f_001` as a true positive for the intentionally vulnerable fixture.
- Require a human reviewer before merging any analogous production change.
- Prefer checks-effects-interactions and a reentrancy guard for remediation.
- Keep `--native-build-policy disabled` for untrusted PR input.

This decision is for the local fixture only. It is not audit certification for
any third-party codebase.

## What Codex Would Automate

Codex can help maintainers:

- Run the exact SCSA triage command on authorized PR input.
- Summarize the JSON and Markdown report.
- Extract trace evidence and redact local-only paths.
- Draft a PR comment with finding count, severity, and human-review status.
- Compare a baseline report and candidate report before release.

Codex should not claim the contract is safe to deploy, skip human review, or
scan unauthorized repositories.

## Limitations

- This case study uses a local fixture, not an external adoption example.
- SCSA promotes only mapped detector output into formal findings.
- LLM text explains analyzer evidence and does not create vulnerability facts.
- Advanced evidence remains reviewer-facing; exploit validation is not attempted
  in this default run.
- Business logic and economic risks still require human review.

## Reproduce

1. Install dependencies:

   ```bash
   uv sync --extra audit --dev
   ```

2. Run the case study command:

   ```bash
   uv run scsa analyze tests/contracts/VulnerableVault.sol \
     --out-dir reports-case-study-001 \
     --native-build-policy disabled
   ```

3. Inspect generated local artifacts:

   ```bash
   ls reports-case-study-001
   ```

4. Confirm the report contains `f_001`, `reentrancy`, and
   `requires_human_review=true`.
