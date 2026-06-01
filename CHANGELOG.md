# Changelog

All notable changes to Smart Contract Security Assistant are documented here.

This project uses human-readable release notes. Dates use `YYYY-MM-DD`.

## Unreleased

### Changed

- Defaulted CLI/API analysis to `native_build_policy=disabled`; trusted native
  builds now require explicit opt-in.
- Added HTTP API fail-closed checks for tokenless `/api/*` access by default,
  non-local hosts without `--api-token`, mismatched request origins, non-JSON
  write bodies, token-authenticated wildcard CORS, job concurrency, event
  buffering, and report read size.
- Archived historical release/community docs and kept `schema/report.schema.json`
  as the single public schema directory.

## v0.2.0 - 2026-06-01

### Added

- HTTP API and React/Vite reviewer workbench from PR #15, including report
  review flow, trace evidence panels, and frontend validation coverage.
- Evidence platform roadmap implementation from PR #16: Evidence Graph storage,
  SCSA-native post-analysis rules, standards mapping, tool attribution, license
  boundary docs, and generated compliance artifacts.
- Phase 3 advanced evidence surface: sandbox-only exploit validation records,
  fuzz seed suggestions, formal property drafts, DeFi profit signal, and
  EVMbench adapter gates.
- Expanded CI and release gates for paired variants, groundedness,
  sandbox-only exploit validation, fuzz/property suggestions, EVMbench adapter,
  SBOM/license inventory generation, frontend tests, and frontend build.
- v0.2.0 release readiness checklist in
  `docs/archive/release/002-v0.2.0-checklist.md`.

### Changed

- Released v0.2.0 as the evidence platform release because the merged scope is
  a platform expansion, not a patch update to v0.1.0.
- Keep issue #12 as the v0.1.0 tester feedback entry because it links to the
  already published v0.1.0 release.

### Validation

- `git pull origin main`
- `uv run ruff check .`
- `uv run pytest` — 116 passed
- `uv run python scripts/check_tool_matrix.py`
- `cd frontend && npm run test -- --run` — 35 passed
- `cd frontend && npm run build`

## v0.1.0 - 2026-05-31

### Added

- OSS readiness baseline: MIT license, contribution guide, security policy,
  code of conduct, issue templates, pull request template, and repository
  topics.
- External-reader README with project positioning, authorized-use boundary,
  quickstart, example output, current scope, limitations, and maintainer
  automation use cases.
- Public maintainer triage for oversized PR #1, split into focused follow-up
  issues #4 through #8 under the `v0.1.0` milestone.
- v0.1.0 release readiness checklist in `docs/archive/release/001-v0.1.0-checklist.md`.

### Changed

- Consolidated public project positioning into the main `README.md` as the
  single GitHub entry point for SCSA's local evidence workbench narrative.
- Moved hackathon-specific reproduction and live proof references to
  `docs/archive/hackathon/` instead of maintaining a separate hackathon README.

### Validation

- `uv sync --extra audit --dev`
- `uv run ruff check .`
- `uv run pytest`
- `uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports-demo`
- `uv run python eval/run_eval.py`
- `uv run python eval/run_judge.py`

### Known Limitations

- Business-logic, economic-mechanism, oracle, cross-contract, and flash-loan
  risks require human review.
- Multi-package Foundry/Hardhat project analysis is tracked separately.
- Frontend workbench, public benchmark gates, source import hardening, and
  report export workflows are tracked in focused follow-up issues.
