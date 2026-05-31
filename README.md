# Smart Contract Security Assistant

Local-first Solidity security triage assistant with Slither, normalized
findings, RAG context, MLX-ready generation, and traceable JSON/Markdown/SQLite
reports.

本專案協助維護者、審計學習者與小型 Solidity 團隊做第一輪安全初篩。LLM 只負責把 deterministic findings 轉成可讀解釋、攻擊路徑與修復建議；漏洞判定來源仍以 Slither 等靜態分析結果為準。

## Who This Is For

- OSS maintainers reviewing Solidity pull requests.
- Small audit teams that need reproducible local triage before human review.
- Hackathon or prototype teams checking obvious contract risks before release.
- Learners who want traceable examples of Slither findings and explanations.

## Authorized-Use Boundary

Only scan contracts that you own, maintain, or are explicitly authorized to review.

Do not use this project to scan private repositories, proprietary contracts,
customer audit material, or third-party code without permission. Do not include
private keys, secrets, customer data, or unpublished third-party reports in
issues, traces, examples, or pull requests.

This tool is not a formal audit replacement. Every report remains human-review
required.

## Quickstart

Prerequisites:

- Python `>=3.11`
- `uv`
- A compatible `solc` version for the target contract

Install the audit dependencies and run the fixture:

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports-demo
uv run pytest
```

The demo command writes:

- `reports-demo/10679f2de6b7.json`
- `reports-demo/10679f2de6b7.md`
- `reports-demo/analysis_trace.sqlite`

Expected summary for the fixture:

```text
overall_status: finding
finding: f_001 | reentrancy | severity 3 | withdraw | SWC-107
human_review_required: true
```

## Example Output

`tests/contracts/VulnerableVault.sol` intentionally writes state after an external call:

```solidity
function withdraw() external {
    uint256 amount = balances[msg.sender];
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "transfer failed");
    balances[msg.sender] = 0;
}
```

The generated Markdown report includes:

```text
### f_001: reentrancy

- Severity: `3`
- Detector: `reentrancy-eth`
- Location: `tests/contracts/VulnerableVault.sol:11`
- Finding confidence: `0.90`
- Explanation confidence: `0.90`
```

The JSON report includes the normalized finding, source location, evidence,
SWC reference, confidence fields, attack path, fix suggestion, tool source, and
analysis metadata.

## Common Commands

```bash
uv run scsa analyze <contract.sol> --out-dir reports
uv run scsa clean-reports data/dataset_v1.0/raw_reports data/dataset_v1.0/chunks/chunks.jsonl
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id> --finding-id f_001
uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json
uv run python scripts/build_skill_graph.py
uv run scsa web --host 127.0.0.1 --port 7860
uv run python eval/run_eval.py
uv run python eval/run_judge.py
```

Optional extras:

```bash
uv sync --extra audit --extra docs --extra rag --extra mlx --extra web --dev
```

## Current Scope

- Input: one Solidity entry file, up to 500 lines.
- Imports: local same-directory imports are covered by tests.
- Solidity: tested with `0.6.x` to `0.8.x` workflows.
- Static analysis: mapped Slither detectors include reentrancy, access control,
  unchecked external call, delegatecall, and controlled array length.
- RAG: local retrieval adds related audit chunks before explanation generation.
- MLX: Apple Silicon local generation path with deterministic fallback when no
  compatible local model/runtime is available.
- Trace: SQLite records raw Slither output, normalized findings, RAG chunks,
  prompts, LLM outputs, and partial/error states.

## Limitations

- Business-logic vulnerabilities still require human review.
- Multi-package Foundry/Hardhat project analysis is not yet v1.0 scope.
- Mythril, oracle manipulation analysis, SARIF export, and GitHub code scanning
  integration are not yet implemented.
- Generated explanations can be incomplete or wrong; use the trace and Slither
  evidence as the review anchor.

## Maintainer Automation Use Cases

This repository is intended to support maintainer workflows such as:

- Pull request review summaries for Solidity security changes.
- Issue classification for bug reports, feature requests, and unsafe usage.
- Release note drafting from merged security-tooling changes.
- Test failure triage across Slither, report generation, RAG, and evals.
- Safer explanation generation from local trace data without uploading
  unauthorized contracts.

## Validation Status

2026-05-31 local validation:

```text
uv sync --extra audit --dev
uv run ruff check .        All checks passed
uv run pytest              15 passed
```

CI runs ruff, pytest, RAG recall eval, and judge eval on pull requests to
`main`.

## Project Documents

- Handoff: `docs/handoff.md`
- Changelog: `CHANGELOG.md`
- v0.1.0 release checklist: `docs/release/001-v0.1.0-checklist.md`
- Usage manual: `docs/guides/001-usage-manual.md`
- Architecture: `docs/design/001-project-architecture.md`
- Validation log: `docs/reference/001-validation-procedure-log.md`
- Document index: `docs/DOCS_INDEX.md`
- Agent rules: `AGENTS.md`

Autonomous iteration skill graph:

- `docs/skill-graph.md`
- `graphify-out/graph.json`
- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.html`

## Contributing

See `CONTRIBUTING.md` for setup, validation, pull request expectations, and
issue triage guidance. See `SECURITY.md` before reporting vulnerabilities or
unsafe behavior in the tool itself.
