# Smart Contract Security Assistant (SCSA)

[![CI](https://github.com/Eskasia/smart-contract-security-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Eskasia/smart-contract-security-assistant/actions/workflows/ci.yml)
[![Python >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Security Policy](https://img.shields.io/badge/security-policy-teal)](SECURITY.md)

Local-first evidence workbench for Solidity security triage.

SCSA turns deterministic analyzer output into reviewable security evidence: Slither findings, optional external-tool signals, local RAG context, MLX-ready explanations, SQLite traces, JSON/Markdown reports, benchmark gates, and a React reviewer UI.

本專案協助維護者、審計學習者與小型 Solidity 團隊完成第一輪安全初篩。漏洞事實來自 Slither 與外部安全工具；LLM 只負責把既有 evidence 轉成可讀解釋、攻擊路徑與修復建議。

> Automated triage only. SCSA improves repeatability, evidence capture, and review handoff. Every report remains human-review required.

## Why SCSA Exists

Smart contract review often produces fragmented evidence: scanner JSON, terminal logs, failed fuzzing output, screenshots, Markdown notes, and reviewer comments. SCSA keeps those pieces in one local workflow so a reviewer can trace each finding from analyzer output to report, UI decision, and CI gate.

Core design:

- Evidence first: raw tool output, normalized findings, retrieved context, prompts, generated explanations, and reviewer notes stay inspectable.
- Local first: source code and generated artifacts remain on the machine running the analysis.
- Deterministic before AI: LLM output explains findings; analyzer output remains the security fact source.
- Human in the loop: every report is a triage handoff for qualified review.
- CI-ready: report comparison, public benchmark, RAG eval, judge eval, frontend tests, and build checks can fail regressions.

## At A Glance

| Question | Answer |
|---|---|
| Primary use | Local Solidity finding triage before manual audit or pull-request review |
| Core analyzer | Slither |
| Optional tools | Aderyn, Echidna, Medusa, Mythril, Halmos |
| Inputs | `.sol`, Foundry, Hardhat, nested imports, GitHub archive, Etherscan API, ZIP |
| Outputs | JSON report, Markdown report, SQLite trace, external-tool artifacts, Aderyn SARIF path |
| Interfaces | CLI, local HTTP API, React/Vite workbench, legacy Gradio UI |
| AI boundary | AI explains evidence; AI does not create vulnerability facts |
| Trust boundary | Imported sources are untrusted unless explicitly trusted by the caller |

## Terminology

- Deterministic finding — a finding produced by a security analyzer or trusted tool output, not inferred directly by an LLM.
- RAG — local retrieval of relevant audit/context chunks before generating an explanation.
- MLX — Apple Silicon local model runtime used for optional local generation.
- SQLite trace — local database rows that preserve analyzer output, normalized findings, prompts, generation output, and review state.
- SARIF — static-analysis result format used by code scanning systems; SCSA tracks Aderyn SARIF as an artifact path.
- Native build policy — setting that controls whether Foundry/Hardhat build scripts may run for a source tree.

## Architecture

```mermaid
graph TD
  Source["Solidity source / Foundry / Hardhat / ZIP / GitHub / Etherscan"] --> Import["Source import guardrails"]
  Import --> Policy["Native build policy"]
  Policy --> Slither["Slither static analysis"]
  Policy --> External["Optional external tools"]
  Slither --> Normalize["Finding normalization"]
  External --> Normalize
  Normalize --> Schema["JSON schema validation"]
  Schema --> RAG["Local RAG retrieval"]
  RAG --> Explain["Deterministic or MLX-ready explanation"]
  Explain --> Report["JSON + Markdown report"]
  Normalize --> Trace["SQLite trace"]
  Report --> Review["React reviewer workbench"]
  Trace --> Review
  Report --> CI["CI gates / comparison / benchmark"]
```

Knowledge graph spec: [`docs/knowledge-graph.md`](docs/knowledge-graph.md). Rebuild local graph artifacts with:

```bash
uv run python scripts/build_knowledge_graph.py
```

Generated files go to `knowledge-graph-out/`, which is intentionally ignored by Git.

## Relation To Security Tools

SCSA is an evidence and review layer around established analyzers. It does not replace them.

| Project | What it is known for | How SCSA uses or complements it |
|---|---|---|
| [Slither](https://github.com/crytic/slither) | Static analysis framework with detector and CI workflows | Primary deterministic finding source and detector mapping |
| [Aderyn](https://github.com/Cyfrin/aderyn) | Solidity static analyzer with Markdown/JSON/SARIF reports | Optional static finding signal and SARIF artifact tracking |
| [Echidna](https://github.com/crytic/echidna) | Property-based smart contract fuzzing | Optional invariant/property failure signal |
| [Medusa](https://github.com/crytic/medusa) | Parallelized coverage-guided Solidity fuzzing | Optional fuzzer failure signal |
| [Mythril](https://github.com/ConsenSysDiligence/mythril) | Symbolic execution for EVM bytecode | Optional symbolic issue signal |
| [Halmos](https://github.com/a16z/halmos) | Symbolic testing for EVM smart contracts | Optional trusted Foundry proof-failure signal |

## Who This Is For

- Solidity developers performing pre-audit checks.
- Open-source maintainers reviewing Solidity pull requests.
- Web3 teams that need repeatable local security triage.
- Audit learners who want traceable examples of findings and explanations.
- Small audit teams that need structured report handoff before deeper review.

## Quick Start

Prerequisites:

- Python `>=3.11`
- `uv`
- A compatible `solc` version for the target contract

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports-demo --native-build-policy disabled
uv run pytest
```

Expected fixture summary:

```text
overall_status: finding
finding: f_001 | reentrancy | severity 3 | withdraw | SWC-107
human_review_required: true
```

Generated artifacts:

```text
reports-demo/<contract_id>.json
reports-demo/<contract_id>.md
reports-demo/analysis_trace.sqlite
```

## Example Finding

`tests/contracts/VulnerableVault.sol` intentionally writes state after an external call:

```solidity
function withdraw() external {
    uint256 amount = balances[msg.sender];
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "transfer failed");
    balances[msg.sender] = 0;
}
```

The generated report records the normalized finding, source location, detector evidence, SWC reference, attack path, fix suggestion, tool source, confidence fields, trace id, and review status.

## Web Workbench

Start the local API:

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
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The workbench supports source import, analysis submit, SSE/polling status, external-tool selection, finding review, trace evidence lookup, report deep links, remediation diff review, JSON/Markdown downloads, and artifact path inspection. API tokens are kept in frontend memory state and are not persisted to `localStorage`.

## CLI Cookbook

```bash
# Analyze a single contract or project
uv run scsa analyze <contract.sol|project-dir> --out-dir reports

# Use a safe default for imported or untrusted projects
uv run scsa analyze <contract.sol|project-dir> --out-dir reports --native-build-policy disabled

# Attach optional external tools when their binaries are installed
uv run scsa analyze <contract.sol|project-dir> --out-dir reports \
  --external-tool aderyn \
  --external-tool echidna \
  --external-tool medusa \
  --external-tool mythril

# Enable Halmos only for a trusted Foundry project
uv run scsa analyze <foundry-project-dir> --out-dir reports \
  --native-build-policy trusted \
  --external-tool halmos

# Import a GitHub repository into a guarded local staging directory
uv run scsa import-source \
  --github-url https://github.com/OpenZeppelin/openzeppelin-contracts \
  --out-dir reports-api/imports

# Import verified contract source from Etherscan-compatible API
uv run scsa import-source \
  --etherscan-api-host api.etherscan.io \
  --address 0x0000000000000000000000000000000000000000 \
  --out-dir reports-api/imports

# Compare two reports for CI regression gates
uv run scsa compare-reports reports/base.json reports/head.json \
  --output reports/comparison.md \
  --fail-on-high-added \
  --fail-on-score-drop 10

# Inspect trace evidence
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id>
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id> --finding-id f_001
uv run scsa trace-dashboard reports/analysis_trace.sqlite

# Probe local MLX runtime availability
uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json

# Create and attach an optional 0G audit proof package
uv run scsa 0g-package reports/<contract_id>.json --out-dir reports-0g
uv run scsa 0g-attach-proof reports/<contract_id>.json reports-0g/<contract_id>/audit-proof.json
```

Optional extras:

```bash
uv sync --extra audit --extra docs --extra rag --extra mlx --extra web --dev
```

## Output Contract

| Output | Purpose |
|---|---|
| JSON report | Machine-readable findings, score, metadata, review state, and external-tool summaries |
| Markdown report | Human-readable audit triage handoff |
| SQLite trace | Raw analyzer output, normalized finding, RAG chunks, prompt, generation output, and review notes |
| External-tool artifacts | Tool-specific JSON/text output and SARIF artifact paths |
| Comparison report | Added, fixed, and persistent findings across two reports |
| 0G proof package | Optional report hash/proof metadata package for hackathon or external verification workflows |

## Security Boundaries

- Only scan contracts that you own, maintain, or are explicitly authorized to review.
- Do not upload private keys, secrets, customer contracts, proprietary audit reports, or unauthorized third-party code.
- `POST /api/imports` rejects path traversal, symlink entries, special files, nested archives, unsafe redirects, non-allowlisted hosts, and oversized remote responses.
- Imported sources are treated as untrusted and should run with `native_build_policy=disabled` unless explicitly trusted by the caller.
- The HTTP API supports bearer token, fixed CORS origin, `input_root`, request body limit, import size limits, and server-side native build policy ceiling.
- Halmos requires trusted Foundry project mode; untrusted/imported sources cannot enable that flow.
- Generated explanations can be incomplete or wrong; use trace rows and analyzer evidence as the review anchor.

## Validation

Last full local verification on 2026-05-31:

```text
uv run pytest -q                     106 passed
uv run ruff check .                  all checks passed
cd frontend && npm run test -- --run 35 passed
cd frontend && npm run build         completed
git diff --check                     passed
```

CI gates:

```bash
uv run ruff check .
uv run pytest
uv run python eval/run_eval.py
uv run python eval/run_judge.py
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5
uv run python eval/run_public_project_builds.py --preflight-only
cd frontend && npm run test -- --run
cd frontend && npm run build
git diff --check
```

Latest recorded public benchmark summary: 50 cases, 100.00% supported-label hit rate, 86.21% precision, 100.00% recall, and 92.59% F1. See [`docs/reference/002-public-benchmark-leaderboard.md`](docs/reference/002-public-benchmark-leaderboard.md).

## GitHub Actions

- `.github/workflows/ci.yml` runs lint, tests, RAG eval, judge eval, public benchmark, public project build preflight, frontend test/build, and whitespace checks on pushes and pull requests.
- `.github/workflows/smart-contract-audit.yml` provides a manual audit workflow that runs `scsa analyze`, optionally compares against a baseline report, and uploads generated reports as the `scsa-reports` artifact.

## Limitations

- Business-logic, economic-mechanism, oracle, cross-contract, governance, MEV, and flash-loan risks require human review.
- External-tool precision depends on installed binaries, project buildability, detector coverage, and configured timeout.
- Native Foundry/Hardhat builds execute project scripts; keep untrusted native builds disabled.
- Local RAG quality depends on the dataset chunks available on the operator machine.
- MLX generation requires a compatible Apple Silicon runtime and model; deterministic fallback remains valid when no local model is available.
- SCSA cannot certify a third-party codebase as safe to deploy.

## Project Docs

- [`CHANGELOG.md`](CHANGELOG.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`SECURITY.md`](SECURITY.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`docs/DOCS_INDEX.md`](docs/DOCS_INDEX.md)
- [`docs/guides/001-usage-manual.md`](docs/guides/001-usage-manual.md)
- [`docs/design/001-project-architecture.md`](docs/design/001-project-architecture.md)
- [`docs/design/005-ui-design-system.md`](docs/design/005-ui-design-system.md)
- [`docs/knowledge-graph.md`](docs/knowledge-graph.md)
- [`docs/release/001-v0.1.0-checklist.md`](docs/release/001-v0.1.0-checklist.md)
- [`docs/community/001-v0.1.0-tester-feedback.md`](docs/community/001-v0.1.0-tester-feedback.md)
- [`docs/reference/002-public-benchmark-leaderboard.md`](docs/reference/002-public-benchmark-leaderboard.md)

## Tester Feedback Wanted

Smart Contract Security Assistant v0.1.0 is collecting independent quickstart feedback from Solidity/Web3 users. If you can run the fixture locally, please leave your environment, command result, and usability feedback in issue #12:

https://github.com/Eskasia/smart-contract-security-assistant/issues/12

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, validation, pull request expectations, and issue triage guidance. See [`SECURITY.md`](SECURITY.md) before reporting vulnerabilities or unsafe behavior in the tool itself.
