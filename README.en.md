# Smart Contract Security Assistant

Local-first Solidity security triage assistant that runs Slither, normalizes findings, retrieves local audit knowledge, generates readable remediation reports, and writes JSON, Markdown, and SQLite trace artifacts with finding-level review feedback.

## Quick Start

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --rag-mode fallback
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --native-build-policy disabled
```

The analysis command writes:

- `reports/<contract_id>.json`
- `reports/<contract_id>.md`
- `reports/analysis_trace.sqlite`

## Web UI

```bash
uv run scsa api \
  --host 127.0.0.1 \
  --port 8787 \
  --out-dir reports-api \
  --input-root "$PWD" \
  --api-token dev-token \
  --cors-origin http://127.0.0.1:5173 \
  --max-request-bytes 1048576 \
  --native-build-policy disabled
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The React UI sends analysis requests to `http://127.0.0.1:8787` through the Vite proxy. `--native-build-policy disabled` skips Foundry/Hardhat build scripts for untrusted projects and uses Slither/solc fallback.

## Main Features

- Input support: single `.sol` files, Foundry projects, Hardhat projects, and generic Solidity projects with nested imports.
- Project build support: Foundry/Hardhat native builds run before Slither in trusted mode; `--native-build-policy disabled` skips build scripts for untrusted projects. The public build harness initializes submodules, installs npm dependencies, and handles custom Hardhat artifacts/cache paths.
- Local API hardening: bearer token auth, allowed `input_root`, request body limit, non-wildcard CORS, and native build policy controls.
- Static analysis: Slither detector mapping for reentrancy, access control, unchecked external calls, delegatecall, array length manipulation, oracle issues, price manipulation, privilege escalation, and upgrade risk.
- Report quality: local and external judge adapters score report completeness on a 0-5 scale.
- Security score: `security_score_v2` returns a 0-100 contract risk score based on severity, confidence, finding review status, partial analysis state, and business logic review requirements.
- Traceability: SQLite trace rows store raw Slither output, normalized findings, RAG chunk ids, prompts, LLM output, token usage, judge scores, review status, and review notes.
- Review feedback: `PATCH /api/reports/{contract_id}/findings/{finding_id}/review` saves `unreviewed`, `true_positive`, `false_positive`, `accepted_risk`, or `fixed`; `false_positive` uses a 0.0 score multiplier and `fixed` uses 0.2 until a fresh scan confirms removal.
- Optional external tools: `--external-tool mythril` and `--external-tool echidna` attach symbolic execution and fuzzing summaries when those tools are installed.

## Commands

```bash
uv run scsa analyze <contract.sol|project-dir> --out-dir reports
uv run scsa analyze <contract.sol|project-dir> --out-dir reports --external-tool mythril --external-tool echidna
uv run scsa compare-reports reports/base.json reports/head.json --output reports/comparison.md --fail-on-high-added --fail-on-score-drop 10
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id>
uv run scsa trace-dashboard reports/analysis_trace.sqlite
uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5
uv run python eval/run_public_project_builds.py --preflight-only
```

## 0G Hackathon Proof Package

The local reproducible path generates the audit report, builds the 0G proof package, creates `submission-proof.json` with dry-run data, and attaches proof metadata back to the report. Live 0G upload and registration require environment variables plus a deployed registry.

```bash
mkdir -p reports
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --native-build-policy disabled > reports/latest-analysis.json
REPORT_ID=$(uv run python -c 'import json; print(json.load(open("reports/latest-analysis.json"))["contract_id"])')
uv run scsa 0g-package reports/latest-analysis.json --out-dir reports-0g --project-name "SCSA 0G Audit Proof" --track "Track 1: Agentic Infrastructure & OpenClaw Lab"
cd integrations/0g
npm install
npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json" --dry-run
npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"
cd ../..
uv run scsa 0g-attach-proof reports/latest-analysis.json "reports-0g/$REPORT_ID/submission-proof.json"
```

Live mode requires `ZERO_G_RPC_URL`, `ZERO_G_PRIVATE_KEY`, and `ZERO_G_STORAGE_INDEXER_RPC`; run `npm run deploy`, export the printed registry address as `ZERO_G_REGISTRY_ADDRESS`, then run `npm run upload -- ...` and `npm run register -- ...`.

`submission-proof.json` uses `storage_tx`, `registry`, and `registration_tx` under `explorer_links`.

## Public Benchmark

The default public benchmark reads `eval/public_benchmark/hf-slither50-v2-manifest.json`, which contains 50 Solidity 0.8-compatible samples from `mwritescode/slither-audited-smart-contracts`.

Validated on 2026-05-06:

- Analyzer success: `50/50`
- Supported label hit rate: `36/36 = 1.0`
- Safe average score: `92.75`
- Vulnerable average score: `47.70`
- Safe minus vulnerable score gap: `45.05`
- Confusion matrix: true positive `25`, true negative `21`, false positive `4`, false negative `0`
- Classification metrics: precision `0.8621`, recall `1.0`, F1 `0.9259`

## Public Project Build Validation

`eval/run_public_project_builds.py` reads `eval/public_benchmark/public-project-builds-10-manifest.json` by default. Validated on 2026-05-06: `--preflight-only` reported `missing_required_tools=[]`. Validated on 2026-05-04: 10 pinned public repos reached `10/10` analyzer success and `10/10` native build success.

## GitHub Actions

The workflow `.github/workflows/smart-contract-audit.yml` adds a manual audit button in GitHub Actions. It accepts a Solidity file or project directory, runs `scsa analyze`, and uploads the generated reports as the `scsa-reports` artifact. When `baseline_report` is provided, it also writes `comparison.md` and can fail on new severity 3 findings or a configurable score drop.

## Validation

Validated on 2026-05-06: ruff passed, Python tests reached `75 passed`, frontend tests reached `8 passed`, frontend build completed, public benchmark reached precision `0.8621`, recall `1.0`, and F1 `0.9259`.

```bash
uv run ruff check .
uv run pytest
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5
uv run python eval/run_public_project_builds.py --min-analyzer-success-rate 1.0 --min-native-build-success-rate 1.0
cd frontend && npm run test && npm run build
```

## Scope

This project is an automated triage assistant. It can reduce review time and make findings easier to understand, but high-value contracts still need manual review by qualified smart contract auditors.
