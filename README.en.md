# Smart Contract Security Assistant

Local-first Solidity security triage assistant that runs Slither, normalizes findings, retrieves local audit knowledge, generates readable remediation reports, and writes JSON, Markdown, and SQLite trace artifacts.

## Quick Start

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --rag-mode fallback
```

The command writes:

- `reports/<contract_id>.json`
- `reports/<contract_id>.md`
- `reports/analysis_trace.sqlite`

## Web UI

```bash
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The React UI sends analysis requests to `http://127.0.0.1:8787` through the Vite proxy.

## Main Features

- Input support: single `.sol` files, Foundry projects, Hardhat projects, and generic Solidity projects with nested imports.
- Static analysis: Slither detector mapping for reentrancy, access control, unchecked external calls, delegatecall, array length manipulation, oracle issues, price manipulation, privilege escalation, and upgrade risk.
- Report quality: local and external judge adapters score report completeness on a 0-5 scale.
- Security score: `security_score_v1` returns a 0-100 contract risk score based on severity, confidence, partial analysis state, and business logic review requirements.
- Traceability: SQLite trace rows store raw Slither output, normalized findings, RAG chunk ids, prompts, LLM output, token usage, judge scores, and review status.
- Optional external tools: `--external-tool mythril` and `--external-tool echidna` attach symbolic execution and fuzzing summaries when those tools are installed.

## Commands

```bash
uv run scsa analyze <contract.sol|project-dir> --out-dir reports
uv run scsa analyze <contract.sol|project-dir> --out-dir reports --external-tool mythril --external-tool echidna
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id>
uv run scsa trace-dashboard reports/analysis_trace.sqlite
uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30
```

## Public Benchmark

The default public benchmark reads `eval/public_benchmark/hf-slither50-v2-manifest.json`, which contains 50 Solidity 0.8-compatible samples from `mwritescode/slither-audited-smart-contracts`.

Validated on 2026-05-04:

- Analyzer success: `50/50`
- Supported label hit rate: `36/36 = 1.0`
- Safe average score: `92.75`
- Vulnerable average score: `47.70`
- Safe minus vulnerable score gap: `45.05`

## GitHub Actions

The workflow `.github/workflows/smart-contract-audit.yml` adds a manual audit button in GitHub Actions. It accepts a Solidity file or project directory, runs `scsa analyze`, and uploads the generated reports as the `scsa-reports` artifact.

## Validation

```bash
uv run ruff check .
uv run pytest
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30
cd frontend && npm run test && npm run build
```

## Scope

This project is an automated triage assistant. It can reduce review time and make findings easier to understand, but high-value contracts still need manual review by qualified smart contract auditors.
