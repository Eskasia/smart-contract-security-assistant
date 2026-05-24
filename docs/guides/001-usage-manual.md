---
title: "使用說明書"
description: "說明安裝、分析、API 加固、trace 查詢、MLX probe、Web UI 與輸出檔案。"
category: "guides"
number: "001"
status: current
services: ["src/smart_contract_audit", "data/dataset_v1.0", "eval"]
related: ["design/001", "reference/001"]
last_modified: "2026-05-24"
---

# 001 — 使用說明書

## Status

current；內容已依 `src/smart_contract_audit/cli.py`、`src/smart_contract_audit/analyzer.py`、`src/smart_contract_audit/http_api.py`、`eval/run_public_benchmark.py`、`README.md` 與 2026-05-24 report export 更新核對。

## Summary

本文件是專案操作手冊，覆蓋安裝、單檔或專案級 Solidity 分析、API 加固、native build policy、trace 查詢、MLX probe、資料清理與 Web UI。當前穩定入口是 CLI：`scsa analyze`。

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
uv run scsa analyze tests/fixtures/solidity_projects/foundry --out-dir reports-foundry
uv run pytest
```

預期輸出：`reports/<contract_id>.json`、`reports/<contract_id>.md`、`reports/analysis_trace.sqlite`。
報告會直接包含 security score、漏洞原始碼片段、AI remediation code、local/external 報告品質 judge score 與 prompt/completion/total token usage；security score 是 0–100 合約風險量化分數，judge score 評估報告完整度。

## 分析合約

```bash
uv run scsa analyze <contract.sol|project-dir> --out-dir reports
```

可選參數：

| 參數 | 作用 |
|---|---|
| `--out-dir` | 指定 JSON、Markdown 與 SQLite trace 輸出資料夾，預設 `reports` |
| `--trace-db` | 指定 trace SQLite 路徑，預設 `<out-dir>/analysis_trace.sqlite` |
| `--dataset-chunks` | 指定 RAG chunk JSONL，預設 `data/dataset_v1.0/chunks/chunks.jsonl` |
| `--rag-mode` | 可選 `quality`、`balanced`、`fast`、`fallback`，預設 `balanced` |
| `--model-path` | 指定 MLX 模型路徑；未指定時可走 deterministic fallback |
| `--native-build-policy` | 可選 `trusted` 或 `disabled`；`disabled` 會略過 Foundry/Hardhat build scripts 並用 Slither/solc fallback |

輸入限制：支援單一 `.sol`、Foundry、Hardhat 與 generic nested import 專案；Foundry/Hardhat 在 `trusted` 模式會先嘗試原生 build，失敗時回退 Slither/solc 並寫入錯誤原因；單檔最多 500 行，專案最多 500 個 Solidity 檔與 100,000 行。

## HTTP API 加固啟動

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

`--native-build-policy disabled` 會略過未信任 Foundry/Hardhat 專案的 build scripts，改用 Slither/solc fallback；前端設定 API token 後會改用 polling，因為瀏覽器 EventSource 無法帶 Authorization header。

Report 讀取端點為 `GET /api/reports/{contract_id}`，Markdown 下載端點為 `GET /api/reports/{contract_id}/markdown`；兩者都使用同一組 bearer token、CORS 與 `contract_id` path segment 驗證。前端下載 JSON/Markdown 時使用 `Authorization` header，不會把 API token 放入 deep link。

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
uv run scsa trace-dashboard reports/analysis_trace.sqlite
```

Trace 會保存 Slither raw output、normalized finding、RAG chunk ids、packed prompt、LLM raw output、schema_valid、partial 狀態、報告品質 judge score、token usage 與 review status。

## Finding 審核回饋

前端 finding card 可保存 `unreviewed`、`true_positive`、`false_positive`、`accepted_risk`、`fixed` 與備註；API endpoint 是 `PATCH /api/reports/{contract_id}/findings/{finding_id}/review`。`false_positive` 會把該 finding 的安全分數懲罰係數設為 `0.0`，`fixed` 係數為 `0.2`，並同步更新 JSON report、Markdown report 與 SQLite `trace_findings.review_status/review_note`。

## Public Benchmark

```bash
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5
```

此命令預設讀取 `eval/public_benchmark/hf-slither50-v2-manifest.json`，目前固定 50 份 Hugging Face Slither 標註樣本；2026-05-06 實測支援類型命中率為 `36/36 = 1.0`，safe/vulnerable 平均安全分數差為 `45.05`，precision `0.8621`，recall `1.0`，F1 `0.9259`，輸出寫入 `reports-public/benchmark/summary.json`。

## External Tools

```bash
uv run scsa analyze <contract.sol|project-dir> --out-dir reports --external-tool mythril --external-tool echidna
```

Mythril——EVM bytecode 符號執行工具；Echidna——智能合約 fuzz 工具。Mythril JSON issues 與 Echidna failed/falsified properties 會轉成正式 findings 與 trace row，工具不存在時以 `skipped` 記錄。

## GitHub Actions

`.github/workflows/smart-contract-audit.yml` 提供手動掃描入口，輸入 Solidity 檔案或專案目錄後會上傳 `scsa-reports` artifact；提供 `baseline_report` 時會額外產生 `comparison.md`。

## Report Comparison

```bash
uv run scsa compare-reports reports/base.json reports/head.json --output reports/comparison.md --fail-on-high-added --fail-on-score-drop 10
```

Report comparison——報告差異比較，會列出新增、修復、持續存在 findings 與安全分數差異；`--fail-on-high-added` 會在新增 severity 3 finding 時回傳 exit code 2。

## MLX Probe

```bash
uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json
```

2026-04-30 實測：自動選到 `/Users/william/models/Qwen3.5-9B-MLX-4bit`，`load_succeeded=true`，`used_fallback=false`，`peak_rss_bytes=661,520,384`。

## 清理審計報告語料

```bash
uv run scsa clean-reports <raw-report-dir> <output-chunks.jsonl>
uv run python scripts/validate_chunks.py <output-chunks.jsonl> --max-unknown-rate 0.4 --min-eligible 400
```

此命令會讀取原始報告資料夾，產生 RAG 用 JSONL chunks。

## Web UI

```bash
uv sync --extra audit --extra web --dev
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --native-build-policy disabled
cd frontend && npm run dev
```

React/Vite Web UI 是主要審查工作台；Gradio 入口仍可用 `uv run scsa web --host 127.0.0.1 --port 7860` 啟動。

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
