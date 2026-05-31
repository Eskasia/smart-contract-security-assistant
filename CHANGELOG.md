# Changelog

All notable changes to Smart Contract Security Assistant are documented here.

This project uses human-readable release notes. Dates use `YYYY-MM-DD`.

## Unreleased

### Added

- OSS readiness baseline: MIT license, contribution guide, security policy,
  code of conduct, issue templates, pull request template, and repository
  topics.
- External-reader README with project positioning, authorized-use boundary,
  quickstart, example output, current scope, limitations, and maintainer
  automation use cases.
- Public maintainer triage for oversized PR #1, split into focused follow-up
  issues #4 through #8 under the `v0.1.0` milestone.
- v0.1.0 release readiness checklist in `docs/release/001-v0.1.0-checklist.md`.

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
