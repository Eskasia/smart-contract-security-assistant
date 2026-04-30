---
title: "驗證程序日誌"
description: "記錄 2026-04-30 本地驗證命令、結果、產物與剩餘限制。"
category: "reference"
number: "001"
status: current
services: ["tests", "eval", "reports-mlx", "graphify-out", "elite-product-report"]
related: ["guides/001", "design/001"]
last_modified: "2026-04-30"
---

# 001 — 驗證程序日誌

## Status

current；本日誌記錄 2026-04-30 在 `/Users/william/智能合約安全分析助理 ` 內實際執行或驗證過的命令與產物。

## Summary

本輪驗證覆蓋 lint、pytest、RAG eval、judge eval、E2E memory、MLX probe、skill graph、簡報輸出與 browser-use artifact 檢查。結論：核心 Python MVP、文件與簡報產物可重建；正式 diff review 仍缺 `.git` baseline。

## Environment

| 項目 | 值 |
|---|---|
| 日期 | 2026-04-30 |
| 專案根目錄 | `/Users/william/智能合約安全分析助理 ` |
| Python package | `smart-contract-security-assistant` |
| Slither | `0.11.5` |
| solc | `0.8.34` |
| MLX model | `/Users/william/models/Qwen3.5-9B-MLX-4bit` |

## Procedure Log

| 程序 | 命令 | 結果 |
|---|---|---|
| Lint | `uv run ruff check .` | `All checks passed!` |
| Unit + integration tests | `uv run pytest -q` | `15 passed, 2 warnings in 4.28s` |
| RAG recall eval | `uv run python eval/run_eval.py` | `cases=4`, `recall_at_k=1.0` |
| Judge eval | `uv run python eval/run_judge.py` | `cases=2`, `average_judge_score=5.0`, `judge_model=local-rule-judge` |
| E2E memory | `/usr/bin/time -l uv run pytest tests/test_e2e.py` | `2 passed`, maximum resident set size `54,231,040 bytes` |
| MLX probe | `uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json` | `load_succeeded=true`, `used_fallback=false`, `duration_ms=7145`, `peak_rss_bytes=661,520,384` |
| Skill graph | `uv run python scripts/build_skill_graph.py` | `nodes=25`, `edges=22`, `remaining_gaps=[]`, generated at `2026-04-30T03:17:50+00:00` |
| Product report HTML | `cd elite-product-report && node src/generate.mjs && node scripts/render.mjs` | `status=ok`, `slides=12`, contact sheet generated |
| Product report PPTX | `cd elite-product-report && node scripts/export_deck_pptx.mjs --slides slides --out output/elite-product-report-image.pptx --mode image --width 1280 --height 720` | 12 slides exported |
| PPTX integrity | `unzip -t final-output/智能合約安全分析助理_產品報告.pptx` | `No errors detected` |
| Browser artifact check | browser-use `iab` backend | `graph.html` 顯示 `2026-04-30` 與 `15 passed`；簡報第 2/11 頁顯示新數值 |

## Warning Log

`uv run pytest -q` 出現 2 個 SWIG deprecation warnings 與 1 個 process-exit 後的 `swigvarlink` warning；觸發測試是 `tests/test_validation_and_mlx.py::test_mlx_probe_records_fallback_without_model_path`。這些 warning 未造成測試失敗。

## Artifacts

| 產物 | 路徑 |
|---|---|
| MLX probe | `reports-mlx/mlx_probe.json` |
| Skill graph JSON | `graphify-out/graph.json` |
| Skill graph HTML | `graphify-out/graph.html` |
| Product report PPTX | `elite-product-report/final-output/智能合約安全分析助理_產品報告.pptx` |
| Product report contact sheet | `elite-product-report/screenshots/contact-sheet.png` |

## Remaining Limits

- 專案目錄截至 2026-04-30 沒有 `.git` repository 邊界，無法做 `origin/HEAD...HEAD` review scope。
- `.codex/ship/scripts/preflight.sh` 不存在，`/review` skill 的 preflight 無法執行。
- Mythril、Foundry、Hardhat plugin、多檔 import resolution、oracle manipulation 分析尚未納入 v1.0。

## References

- `README.md`
- `docs/handoff.md`
- `docs/guides/001-usage-manual.md`
- `docs/design/001-project-architecture.md`
