# Codex for OSS Application Package

Status: draft application package
Updated: 2026-06-01

This package gives concise, public-evidence-backed text for a Codex for OSS
application. It does not submit the application and does not claim adoption
that is not recorded in `docs/adoption/metrics.md`.

## Repository

- Repository: <https://github.com/Eskasia/smart-contract-security-assistant>
- License: MIT
- Package name: `smart-contract-security-assistant`
- Primary interface: CLI with HTTP API, React/Vite reviewer UI, optional Gradio
  entry point, and manual GitHub Actions workflow.

## Maintainer role

The applicant is the primary maintainer of SCSA. The maintainer workflow covers
authorized Solidity pull request triage, issue triage, release regression
comparison, report review handoff, benchmark gates, documentation updates, and
safe external tester feedback processing.

## Current evidence snapshot

Snapshot date: 2026-06-01

| Item | Current evidence |
|---|---|
| GitHub stars | 0, verified from GitHub repo API on 2026-06-01 |
| GitHub forks | 0, verified from GitHub repo API on 2026-06-01 |
| External testers | 0 logged current-phase external testers |
| Public triage cases | 0 authorized public triage cases |
| Testimonials | 0 permissioned testimonials |
| Monthly downloads | 0; PyPI JSON returned 404 on 2026-06-01 and GitHub releases have no assets |
| External OSS adoptions | 0 public adoption links |
| Latest published release | v0.2.0 evidence platform release |
| Hardening status | v0.2.1 final hardening release readiness docs exist; tag and GitHub release pending |
| Benchmark evidence | 50 public cases, 100.00% supported-label hit rate, 86.21% precision, 100.00% recall, 92.59% F1 |

## Why this repo qualifies

<!-- app-field: qualification -->
```text
I am the primary maintainer of SCSA, a public MIT Solidity security triage workbench for OSS maintainers. It converts mapped Slither and optional external-tool evidence into JSON/Markdown reports, SQLite traces, PR regression gates, benchmark checks, and reviewer handoff artifacts. Adoption metrics are tracked conservatively; current external adoption remains unclaimed until public evidence exists.
```

## API credits use

<!-- app-field: api_credits_use -->
```text
API credits would support maintainer automation for SCSA: PR triage summaries, issue classification, regression report comparison, release checklist drafting, and evidence-grounded reviewer handoff text. The workflow only analyzes repositories I maintain or repositories whose maintainers explicitly authorize testing and public-safe summaries.
```

## Codex Security use

<!-- app-field: codex_security_use -->
```text
Codex Security would be used to review SCSA itself and explicitly authorized test repositories, focusing on API safety, source-import boundaries, dependency/tooling risk, report sanitization, and CI hardening. It would not be used to scan private or third-party targets without authorization.
```

## Additional information

<!-- app-field: additional_information -->
```text
SCSA keeps vulnerability facts grounded in analyzer output. Reports remain human-review required and do not certify contracts as safe. Current public evidence includes fail-closed API defaults, native-build-safe source handling, mapped detector scope, reproducible benchmark gates, package metadata, outreach assets, and empty-but-structured adoption logs.
```

## Evidence links

- Evidence index:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/docs/adoption/codex-for-oss-evidence.md>
- Adoption metrics:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/docs/adoption/metrics.md>
- Maintainer workflow:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/docs/maintainer-workflow.md>
- Security policy:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/SECURITY.md>
- Public benchmark leaderboard:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/docs/reference/002-public-benchmark-leaderboard.md>
- Benchmark reproducibility:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/docs/reference/benchmark-reproducibility.md>
- Public report schema:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/schema/report.schema.json>
- Reusable PR triage workflow:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/docs/templates/scsa-pr-triage.yml>
- External adoption log:
  <https://github.com/Eskasia/smart-contract-security-assistant/blob/main/docs/adoption/external-adoptions.md>

## Do-not-submit items

- Do not claim external testers, testimonials, public triage cases, downloads,
  stars, forks, or external OSS adoptions beyond `docs/adoption/metrics.md`.
- Do not submit private repository names, private audit material, customer
  identifiers, raw local paths, secrets, API keys, or unpublished findings.
- Do not describe SCSA as a full audit product, audit certification, or
  replacement for qualified human review.
- Do not claim Codex Security would scan private or third-party repositories
  without explicit maintainer authorization.
