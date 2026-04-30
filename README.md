# 智能合約安全分析助理

本專案是 Solidity 智能合約安全初篩 MVP：單檔 `.sol` 輸入後，系統執行 Slither 靜態分析、標準化 findings、檢索本地知識庫、產生可追溯報告，並輸出 JSON、Markdown 與 SQLite trace。

## 快速啟動

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports
uv run pytest
```

可選功能依需求安裝：

```bash
uv sync --extra audit --extra docs --extra rag --extra mlx --extra web --dev
```

## 常用命令

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

## 目前範圍

- 輸入限制：單一入口 `.sol` 檔，入口檔最多 500 行；同目錄本地 import 可由 Slither 解析，Solidity `0.6.x` 至 `0.8.x`。
- 靜態分析：Slither detector 映射 reentrancy、access control、unchecked external call、delegatecall、controlled array length。
- RAG——Retrieval-Augmented Generation，先從本地語料找相關 chunk，再把 chunk 放入 LLM prompt 生成解釋。
- MLX——Apple Silicon 本地推理 runtime；目前有 4-bit 量化記憶體估算、`mlx-lm` 生成介面與 `scsa mlx-probe` 載入狀態記錄，支援自動探索本機 MLX 模型，未設定模型或 runtime 不可用時走 deterministic fallback。
- Trace——SQLite 追蹤每個 finding 的 Slither raw output、標準化結果、RAG chunk、prompt 與 LLM output。

## 驗證狀態

2026-04-30 驗證通過：`uv run pytest` 共 15 passed，`uv run ruff check .` 通過，`uv run python eval/run_eval.py` 召回率 1.0，`uv run python eval/run_judge.py` 平均分 5.0，`uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json` 已載入本機 4bit 模型，峰值 RSS 661,520,384 bytes，`uv run python scripts/build_skill_graph.py` 可產生 graph artifact，`pytest tests/test_e2e.py` 最大 resident set size 54,231,040 bytes。CI 已接入 ruff、pytest、RAG recall eval、judge eval。

`review` 技能的 git diff 審查目前無法完整執行，因為此資料夾沒有 `.git` repository 邊界，也沒有 `.claude/skills/review/checklist.md`。

## 產品報告 PPT

最終產品報告位於：

```text
elite-product-report/final-output/智能合約安全分析助理_產品報告.pptx
```

2026-04-30 已用 `unzip -t` 檢查 PPTX 壓縮資料，結果為 no errors detected。可預覽 HTML 位於 `elite-product-report/index.html`，縮圖總覽位於 `elite-product-report/screenshots/contact-sheet.png`。

其他歷史版本：

- `deck-smart-contract-security-assistant/output/output.pptx`
- `huashu-redesign/output/huashu-redesign-image.pptx`
- `huashu-redesign/output/huashu-redesign-editable.pptx`
- `huashu-product-report/output/product-report-fathom-image.pptx`
- `huashu-product-report/output/product-report-fathom-editable.pptx`

## 交接文件

完整接手資訊在 `docs/handoff.md`。使用說明書在 `docs/guides/001-usage-manual.md`，專案架構書在 `docs/design/001-project-architecture.md`，驗證程序日誌在 `docs/reference/001-validation-procedure-log.md`，文件索引在 `docs/DOCS_INDEX.md`。專案內 agent 操作規則在 `AGENTS.md`。

自主迭代用 skill graph 在 `docs/skill-graph.md`，定義多 agent 分工、能力節點、缺口排序與驗證閉環；可重建產物位於 `graphify-out/graph.json`、`graphify-out/GRAPH_REPORT.md`、`graphify-out/graph.html`。
