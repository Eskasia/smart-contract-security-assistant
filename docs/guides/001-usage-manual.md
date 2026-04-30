---
title: "使用說明書"
description: "說明安裝、分析、trace 查詢、MLX probe、Web UI 與輸出檔案。"
category: "guides"
number: "001"
status: current
services: ["src/smart_contract_audit", "data/dataset_v1.0", "reports-mlx"]
related: ["design/001", "reference/001"]
last_modified: "2026-04-30"
---

# 001 — 使用說明書

## Status

current；內容已依 `src/smart_contract_audit/cli.py`、`src/smart_contract_audit/analyzer.py`、`README.md` 與 2026-04-30 本地驗證結果核對。

## Summary

本文件是專案操作手冊，覆蓋安裝、單檔 Solidity 分析、trace 查詢、MLX probe、資料清理與 Web UI。當前穩定入口是 CLI：`scsa analyze`。

## 前置條件

1. 工作目錄必須是 `/Users/william/智能合約安全分析助理 `，路徑尾端有 1 個空格。
2. Python 需符合 `pyproject.toml` 的 `>=3.11`。
3. 靜態分析需安裝 audit extra：`uv sync --extra audit --dev`。
4. 可選功能使用完整 extra：`uv sync --extra audit --extra docs --extra rag --extra mlx --extra web --dev`。

## 快速啟動

```bash
cd "/Users/william/智能合約安全分析助理 "
uv sync --extra audit --dev
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports
uv run pytest
```

預期輸出：`reports/<contract_id>.json`、`reports/<contract_id>.md`、`reports/analysis_trace.sqlite`。

## 分析合約

```bash
uv run scsa analyze <contract.sol> --out-dir reports
```

可選參數：

| 參數 | 作用 |
|---|---|
| `--out-dir` | 指定 JSON、Markdown 與 SQLite trace 輸出資料夾，預設 `reports` |
| `--trace-db` | 指定 trace SQLite 路徑，預設 `<out-dir>/analysis_trace.sqlite` |
| `--dataset-chunks` | 指定 RAG chunk JSONL，預設 `data/dataset_v1.0/chunks/chunks.jsonl` |
| `--rag-mode` | 可選 `quality`、`balanced`、`fast`、`fallback`，預設 `balanced` |
| `--model-path` | 指定 MLX 模型路徑；未指定時可走 deterministic fallback |

輸入限制：只支援單一入口 `.sol` 檔，入口檔最多 500 行；同目錄本地 import 已由 `tests/test_slither.py` 覆蓋。

## 報告狀態

| 狀態 | 含義 |
|---|---|
| `finding` | 有映射後的 Slither finding 並已寫入報告 |
| `no_finding` | Slither 沒有產生可映射 finding |
| `partial_analysis` | 分析超過時間門檻，部分 finding 標記 `partial=true` |
| `error` | 輸入、Slither、schema 或其他系統邊界失敗 |

## Trace 查詢

先從 JSON 報告讀取 `analysis_metadata.analysis_trace_id`，再查 SQLite：

```bash
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id>
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id> --finding-id f_001
```

Trace 會保存 Slither raw output、normalized finding、RAG chunk ids、packed prompt、LLM raw output、schema_valid 與 partial 狀態。

## MLX Probe

```bash
uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json
```

2026-04-30 實測：自動選到 `/Users/william/models/Qwen3.5-9B-MLX-4bit`，`load_succeeded=true`，`used_fallback=false`，`peak_rss_bytes=661,520,384`。

## 清理審計報告語料

```bash
uv run scsa clean-reports data/dataset_v1.0/raw_reports data/dataset_v1.0/chunks/chunks.jsonl
```

此命令會讀取原始報告資料夾，產生 RAG 用 JSONL chunks。

## Web UI

```bash
uv sync --extra audit --extra web --dev
uv run scsa web --host 127.0.0.1 --port 7860
```

Web UI 是可選展示入口；核心流程仍以 CLI 與測試驗證為準。

## 常見問題

| 症狀 | 檢查 |
|---|---|
| `Input must be a single .sol file.` | 輸入副檔名需為 `.sol` |
| `Input exceeds 500 lines.` | 入口合約需拆小或等多檔專案支援 |
| Slither 執行失敗 | 跑 `uv run pytest tests/test_slither.py` 確認 Slither 與 solc |
| MLX 走 fallback | 檢查 `reports-mlx/mlx_probe.json` 的 `fallback_reason` |

## References

- `README.md`
- `docs/handoff.md`
- `src/smart_contract_audit/cli.py`
- `src/smart_contract_audit/analyzer.py`
- `docs/design/001-project-architecture.md`
- `docs/reference/001-validation-procedure-log.md`
