# AGENTS.md

## Repository Execution Rules

- Quote paths in shell commands because contributor worktrees may contain spaces.
- Prefer running commands from the repository root.
- Do not commit generated reports, local corpora, private audit material, API keys, or secrets.
- Keep public GitHub content focused on source, tests, CI, docs, benchmark fixtures, and package metadata.

## Codex Goal Workflow

1. Inspect relevant files and tests before editing.
2. Keep one goal per PR.
3. Add or update tests before making docs-only capability claims.
4. Run the verification commands listed for the goal.
5. Summarize changed files, tests, acceptance status, and residual risk.

## Project Status

As of 2026-06-01, the core flow includes Slither integration, external tools
registry, source import, finding adapter, JSON schema validation, local RAG
fallback, MLX-ready generator, SQLite trace, Markdown/JSON reports, CLI, HTTP
API, React/Vite frontend, optional Gradio entrypoint, eval scripts, benchmark
gates, pytest tests, and Vitest tests.

## Common Verification

```bash
uv sync --extra audit --dev
uv run pytest
uv run ruff check .
git diff --check
uv run pytest tests/test_slither.py
uv run python eval/run_eval.py
uv run python eval/run_judge.py
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30
uv run python eval/run_public_project_builds.py --min-analyzer-success-rate 1.0 --min-native-build-success-rate 1.0
cd frontend && npm run test -- --run
cd frontend && npm run build
```

Verified tool versions: Slither `0.11.5`, solc `0.8.34`.

## Main Code Boundaries

- CLI: `src/smart_contract_audit/cli.py`
- Analysis flow: `src/smart_contract_audit/analyzer.py`
- Slither integration: `src/smart_contract_audit/slither_runner.py`
- Finding mapping: `src/smart_contract_audit/finding_adapter.py`
- RAG: `src/smart_contract_audit/rag/`
- MLX interface: `src/smart_contract_audit/llm/mlx_runtime.py`
- Trace: `src/smart_contract_audit/trace/`
- Validation schema: `src/smart_contract_audit/validation/`

## Git Hygiene

- Ignore unrelated local changes.
- Do not revert user changes unless explicitly requested.
- Do not stage generated `reports*/`, `graphify-out/`, `knowledge-graph-out/`,
  `.local/`, presentation exports, raw public-project corpora, `.ship/`, or
  `.claude/` artifacts.

## Documentation Rules

- New functionality should update `README.md`, `docs/handoff.md`, and
  `docs/DOCS_INDEX.md` when those files are affected.
- Use exact dates in `YYYY-MM-DD` format.
- Keep the public GitHub entrypoint in `README.md`.
- Do not restore separate `README.en.md` or `README.hackathon.md` entrypoints.
