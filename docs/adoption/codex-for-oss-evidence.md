# Codex for OSS Evidence

Status: current evidence index; external adoption evidence is not yet complete.
Updated: 2026-06-01

This page is the public evidence index for short Codex for OSS application
answers. It records only repo-verifiable claims and keeps adoption metrics
separate from local engineering evidence.

## Maintainer role

SCSA is maintained as an analysis-artifact-local-first Solidity security
evidence platform for authorized maintainers and reviewers. The maintainer
workflow focuses on:

- Running reproducible analysis on repository-owned or explicitly authorized
  Solidity code.
- Turning analyzer output into JSON, Markdown, trace, and Evidence Graph
  artifacts.
- Preserving human-review boundaries for security findings and deployment
  decisions.

## Repository purpose

SCSA provides first-pass Solidity security triage and evidence handoff. It is
not an audit certification product.

Core repository evidence:

- CLI, HTTP API, React/Vite reviewer UI, and optional Gradio entry point.
- Slither-based mapped findings with deterministic standards mapping.
- Optional external-tool result capture for Aderyn, Echidna, Halmos, Medusa,
  and Mythril when installed and explicitly selected.
- Evidence Graph nodes, edges, claims, trace SQLite, report schema validation,
  benchmark gates, and local RAG explanation support.
- Safe defaults for untrusted/imported source: native build policy disabled and
  human review required.

## Current validation status

Latest local verification recorded for v0.2.1 final hardening release readiness:

- Date: 2026-06-01
- `uv run ruff check .`: passed
- `uv run pytest`: 140 passed
- `uv run python scripts/sync_report_schema.py --check`: passed
- `cd frontend && npm ci`: installed 274 packages, audited 275 packages, 0 vulnerabilities
- `cd frontend && npm run test -- --run`: 35 passed
- `cd frontend && npm run build`: passed
- `uv build`: built source distribution and wheel artifacts
- `git diff --check`: passed

Release evidence:

- v0.2.0 is published as the evidence platform release, not audit
  certification.
- v0.2.1 hardening is release-ready for tagging after the finalization PR is
  merged and GitHub Actions is green. It covers API fail-closed defaults, mapped
  detector claim boundaries, public schema sync, and public AGENTS cleanup.
- Checklist:
  [`docs/archive/release/003-v0.2.1-hardening-checklist.md`](../archive/release/003-v0.2.1-hardening-checklist.md)

## Maintainer workflows

- Maintainer workflow guide:
  [`docs/maintainer-workflow.md`](../maintainer-workflow.md)
- Security policy:
  [`SECURITY.md`](../../SECURITY.md)
- Usage manual:
  [`docs/guides/001-usage-manual.md`](../guides/001-usage-manual.md)
- Review checklist:
  [`docs/review_checklist.md`](../review_checklist.md)

Workflow coverage:

- Pull request triage for authorized Solidity changes.
- Issue triage with report and trace references.
- Release regression comparison with baseline and candidate reports.
- Evidence handoff through JSON, Markdown, SQLite trace, and CI artifacts.

## Case studies

Repository-owned, reproducible case studies:

| Case | Scope | Evidence |
|---|---|---|
| 001 | Single-file PR triage fixture | [`docs/case-studies/001-pr-triage-vulnerable-vault.md`](../case-studies/001-pr-triage-vulnerable-vault.md) |
| 002 | Hardhat project triage fixture | [`docs/case-studies/002-hardhat-project-triage.md`](../case-studies/002-hardhat-project-triage.md) |
| 003 | Foundry project triage and Halmos boundary fixture | [`docs/case-studies/003-foundry-project-triage.md`](../case-studies/003-foundry-project-triage.md) |

These are local fixtures, not external adoption claims.

## Security and authorized-use boundary

- Only scan contracts that you own, maintain, or are explicitly authorized to
  review.
- Imported GitHub, Etherscan, archive, and remote payload sources are treated as
  untrusted.
- Native Foundry and Hardhat builds execute project tooling and remain disabled
  by default.
- Halmos requires trusted local Foundry project mode.
- The HTTP API requires bearer token authentication for `/api/*` by default and
  fail-closes on unsafe host/token/CORS combinations.
- SCSA reports analyzer evidence and reviewer-facing suggestions; it does not
  certify contracts as safe to deploy.

Reference docs:

- [`docs/reference/tool-attribution.md`](../reference/tool-attribution.md)
- [`docs/reference/license-boundary.md`](../reference/license-boundary.md)
- [`docs/reference/standards-mapping.md`](../reference/standards-mapping.md)
- [`docs/reference/phase3-advanced-evidence.md`](../reference/phase3-advanced-evidence.md)

## Benchmark and CI evidence

Benchmark evidence:

- Public benchmark leaderboard:
  [`docs/reference/002-public-benchmark-leaderboard.md`](../reference/002-public-benchmark-leaderboard.md)
- Benchmark reproducibility:
  [`docs/reference/benchmark-reproducibility.md`](../reference/benchmark-reproducibility.md)
- Latest recorded public benchmark summary: 50 cases, 100.00%
  supported-label hit rate, 86.21% precision, 100.00% recall, and 92.59% F1.
- Phase 2 paired variants currently cover 15 pairs across 5 vulnerability
  types with `paired_pass_rate = 1.0`.
- Groundedness eval requires `unsupported_security_claims = 0`.

CI evidence:

- `.github/workflows/ci.yml` runs compliance generation, lint, tests, RAG eval,
  judge eval, paired variant benchmark, groundedness eval, sandbox exploit
  validation, fuzz/property suggestion evals, EVMbench adapter, public
  benchmark, public project build preflight, frontend test/build, and whitespace
  checks.
- `.github/workflows/smart-contract-audit.yml` provides a manual audit workflow
  that runs `scsa analyze`, optionally compares baseline/candidate reports, and
  uploads `scsa-reports`.

## Adoption metrics

Canonical adoption metrics tracker:
[`docs/adoption/metrics.md`](metrics.md)

Latest weekly adoption update: 2026-06-01. Public GitHub API showed 0 stars and
0 forks; PyPI JSON still returned 404; no completed tester feedback issue,
testimonial, public triage case, release asset download, or external OSS
adoption link is logged.

Pre-application consistency audit:
[`docs/adoption/evidence-consistency-audit.md`](evidence-consistency-audit.md)

The tracker is intentionally conservative: repository-owned fixtures and local
validation runs do not count as external testers, public triage cases,
testimonials, downloads, or external OSS adoptions.

## External tester evidence

External tester evidence is pending Phase 2. Current repo evidence does not
claim external users, production deployments, downloads, or third-party audit
results.

Tester onboarding:
[`docs/adoption/tester-onboarding.md`](tester-onboarding.md)

Feedback processing workflow:
[`docs/adoption/feedback-processing.md`](feedback-processing.md)

Outreach kit:
[`docs/adoption/outreach-kit.md`](outreach-kit.md)

External adoption log:
[`docs/adoption/external-adoptions.md`](external-adoptions.md)

Public triage protocol and case log:
[`docs/adoption/public-triage-protocol.md`](public-triage-protocol.md),
[`docs/adoption/public-triage-cases.md`](public-triage-cases.md)

Planned Phase 2 evidence fields:

- Tester GitHub handle
- Repository tested
- Authorization basis
- Command run
- Report artifact summary
- Feedback issue link
- Permission to quote

## Testimonials

Testimonials log:
[`docs/adoption/testimonials.md`](testimonials.md)

No testimonials are recorded for the current adoption phase. Future testimonial
entries must include explicit permission to quote and must not include private
contract code, secrets, customer identifiers, or proprietary audit material.

## Application text

Application package:
[`docs/adoption/codex-for-oss-application.md`](codex-for-oss-application.md)

Short application summary:

```text
SCSA is an analysis-artifact-local-first Solidity security evidence platform for
authorized maintainers. It turns analyzer output into reviewable findings,
Evidence Graph claims, trace artifacts, benchmark gates, and human-review
handoff docs. It is not audit certification.
```

Evidence-backed claim:

```text
The repo includes fail-closed API defaults, native-build-safe source handling,
mapped standards evidence, SBOM/license attribution, benchmark gates, and three
repository-owned triage case studies for single-file, Hardhat, and Foundry
workflows.
```
