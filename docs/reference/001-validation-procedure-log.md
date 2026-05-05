---
title: "驗證程序日誌"
description: "記錄 2026-05-04 本地驗證命令、結果、產物與剩餘限制。"
category: "reference"
number: "001"
status: current
services: ["tests", "eval", "frontend", "docs"]
related: ["guides/001", "design/001"]
last_modified: "2026-05-04"
---

# 001 — 驗證程序日誌

## Status

current；本日誌記錄 2026-05-04 在 `/Users/william/智能合約安全分析助理 ` 內實際執行或驗證過的命令與產物。

## Summary

本輪驗證覆蓋 lint、pytest、50 份 public benchmark、10 份 pinned public repo native build、前端測試/build、RAG eval、judge eval、E2E memory、MLX probe 與 skill graph。結論：核心 Python 流程、專案級 Solidity 輸入、報告治理與文件產物可重建；Git baseline 已建立在 `main`。

## Environment

| 項目 | 值 |
|---|---|
| 日期 | 2026-05-04 |
| 專案根目錄 | `/Users/william/智能合約安全分析助理 ` |
| Python package | `smart-contract-security-assistant` |
| Slither | `0.11.5` |
| solc | `0.8.34` |
| MLX model | `/Users/william/models/Qwen3.5-9B-MLX-4bit` |

## Procedure Log

| 程序 | 命令 | 結果 |
|---|---|---|
| Lint | `uv run ruff check .` | `All checks passed!` |
| Unit + integration tests | `uv run pytest` | `69 passed, 2 warnings in 13.65s` |
| Frontend tests | `cd frontend && npm run test` | `2 files`, `7 passed` |
| Frontend build | `cd frontend && npm run build` | build completed |
| RAG recall eval | `uv run python eval/run_eval.py` | `cases=8`, `recall_at_k=1.0` |
| Judge eval | `uv run python eval/run_judge.py` | `cases=4`, `local_average_judge_score=5.0`, `external_average_judge_score=5.0` |
| Project input | `uv run pytest tests/test_project_input.py` | `9 passed`；Foundry、Hardhat、nested imports、native build args、自訂 Hardhat artifacts/cache 路徑均通過 |
| Public project build harness | `uv run pytest tests/test_public_project_builds.py` | `8 passed`；local manifest summary、native build threshold、commit ref checkout、10 repo manifest pinning、preflight missing tools、dependency install fallback 均通過 |
| Public benchmark | `uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30` | `cases=50`, `supported_hit_rate=1.0`, `average_score_gap_safe_minus_vulnerable=45.05` |
| Public project build validation | `uv run python eval/run_public_project_builds.py --min-analyzer-success-rate 1.0 --min-native-build-success-rate 1.0` | `cases=10`, `analyzer_success_rate=1.0`, `native_build_success_rate=1.0` |
| Enhanced report | `uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir <tmp> --rag-mode fallback` | Markdown 含第 11–16 行 vulnerable code、AI remediation code、judge `5.00/5`、tokens `680/300/980` |
| E2E memory | `/usr/bin/time -l uv run pytest tests/test_e2e.py` | `2 passed`, maximum resident set size `54,231,040 bytes` |
| MLX probe | `uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json` | `load_succeeded=true`, `used_fallback=false`, `duration_ms=7145`, `peak_rss_bytes=661,520,384` |
| Skill graph | `uv run python scripts/build_skill_graph.py` | `nodes=25`, `edges=22`, `remaining_gaps=[]`, generated at `2026-04-30T03:17:50+00:00` |

## Warning Log

`uv run pytest -q` 出現 2 個 SWIG deprecation warnings 與 1 個 process-exit 後的 `swigvarlink` warning；觸發測試是 `tests/test_validation_and_mlx.py::test_mlx_probe_records_fallback_without_model_path`。這些 warning 未造成測試失敗。

## Artifacts

| 產物 | 路徑 |
|---|---|
| MLX probe | 本機 `reports-mlx/mlx_probe.json`，不追蹤到 GitHub |
| Skill graph | 本機 `graphify-out/`，不追蹤到 GitHub |

## Remaining Limits

- `.codex/ship/scripts/preflight.sh` 不存在，`/review` skill 的 preflight 無法執行。
- Foundry/Hardhat 原生 build preflight 已用 10 repo pinned manifest 驗證 `10/10` analyzer 與 `10/10` native build。
- 完整 business-logic symbolic analysis 尚未納入。

## References

- `README.md`
- `docs/handoff.md`
- `docs/guides/001-usage-manual.md`
- `docs/design/001-project-architecture.md`
