# Contributing

Thank you for helping improve Smart Contract Security Assistant.

This project is a local-first Solidity security triage assistant. Contributions
should keep the tool reproducible, traceable, and explicit about authorized-use
security boundaries.

## Ground Rules

- Only submit examples, contracts, reports, or traces that you own or are
  authorized to share.
- Do not include private keys, API keys, secrets, customer data, proprietary
  audit reports, or unreleased third-party code.
- Keep security claims precise. This tool supports triage and reproducible
  review workflows; it is not a replacement for a full audit.
- Prefer small pull requests with focused tests and documentation updates.

## Development Setup

```bash
uv sync --extra audit --dev
uv run pytest
uv run ruff check .
```

Optional extras:

```bash
uv sync --extra audit --extra docs --extra rag --extra mlx --extra web --dev
```

## Common Commands

```bash
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports
uv run python eval/run_eval.py
uv run python eval/run_judge.py
uv run scsa web --host 127.0.0.1 --port 7860
```

## Pull Request Checklist

Before opening a pull request:

- Run `uv run ruff check .`.
- Run `uv run pytest`.
- Run the relevant eval command if you changed RAG, scoring, prompts, finding
  normalization, or report generation.
- Update `README.md` and `docs/handoff.md` when behavior, setup, or maintainer
  workflows change.
- Explain any skipped validation in the pull request description.

## Issue Triage

When filing an issue, include:

- The command you ran.
- The expected behavior.
- The actual behavior.
- The smallest reproducible Solidity input, if it can be shared legally.
- Your OS, Python version, and optional extras installed.

For vulnerabilities in this repository or unsafe behavior in the tool itself,
follow `SECURITY.md` instead of opening a public issue.
