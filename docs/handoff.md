# 智能合約安全分析助理交接

更新日期：2026-05-04。

## 已完成內容

- Python package `smart_contract_audit` 已建立，入口命令為 `scsa`。
- 核心流程為 `.sol` 或 Solidity 專案輸入 → Slither → finding normalization → JSON schema validation → RAG retrieval → LLM explanation fallback 或 MLX runtime → JSON/Markdown report → SQLite trace。
- 2026-05-04 已新增 `src/smart_contract_audit/http_api.py` 本機 HTTP API，前端可透過 `POST /api/analyses` 觸發 `analyze_contract()`，再用 SSE、report endpoint、trace endpoint 與 review PATCH 完成真實工作流。
- 2026-05-01 已新增 `frontend/` React/Vite 工作台，包含三欄 triage UI、Zustand 狀態、Local Storage 設定、SSE hook、1,000 ms polling fallback、virtualized findings、syntax-highlighted vulnerable code、remediation diff、review status 與 trace evidence panel。
- 測試覆蓋 adapter、analyzer、RAG、Slither 串接、Foundry、Hardhat、nested import 解析、detector expansion、MLX 記憶體估算、MLX 模型自動探索、MLX probe fallback、skill graph artifact、schema validation、端到端流程。
- Eval 腳本已存在：`eval/run_eval.py` 測 RAG recall，`eval/run_judge.py` 同時輸出 local 與 external 報告品質 judge adapter 分數。
- CI 設定在 `.github/workflows/ci.yml`，目前執行 ruff、pytest、RAG eval 與 judge eval。
- 2026-05-04 已新增 `.github/workflows/smart-contract-audit.yml`，GitHub Actions 可手動輸入 Solidity 檔案或專案目錄並上傳 `scsa-reports` artifact。
- Git baseline 已建立在 `main`，review checklist 位於 `.claude/skills/review/checklist.md` 與 `docs/review_checklist.md`。
- 2026-05-04 公開資料測試補上 `unchecked-transfer` 與 `unused-return`，統一映射到 `unchecked_external_call`。
- 2026-05-04 已新增 `security_score_v1` 合約安全分數、`eval/run_public_benchmark.py` 與 `eval/public_benchmark/hf-slither50-v2-manifest.json`；目前 50 份 Hugging Face Slither 標註樣本支援類型命中率為 `36/36 = 1.0`，safe/vulnerable 平均安全分數差為 `45.05`。
- 2026-05-04 已新增 Mythril/Echidna 可選整合，`--external-tool mythril --external-tool echidna` 會把結果寫入 `external_tool_results`。
- 2026-05-04 已新增英文版 `README.en.md`。

## 技術核心

Slither——Solidity 靜態分析工具，負責 deterministic vulnerability finding；LLM 不負責判定漏洞，只負責把 finding 轉成可讀解釋、攻擊路徑與修復建議。

RAG——Retrieval-Augmented Generation，先從審計語料與技術文件 chunk 檢索證據，再把證據放入 prompt，降低生成內容脫離資料來源的風險。

MLX——Apple Silicon 本地推理 runtime，本專案以 4-bit 權重量化估算記憶體需求，`8B` 參數模型在 4-bit 權重下約需 `4.0GB` 權重記憶體；`uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json` 會輸出模型路徑、量化位元、預估權重記憶體、fallback 原因、load_succeeded 與 peak_rss_bytes。

Trace——SQLite 分析追蹤表，保存 finding、raw Slither output、RAG chunks、prompt、LLM output、報告品質 judge score、token usage、partial 狀態與 review status，用於除錯與報告回溯；`scsa trace-dashboard` 可列出 trace id、dataset version、model version、review status。

HTTP API——本機 stdlib `ThreadingHTTPServer`，入口命令為 `uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api`；支援 analysis job、SSE stream、JSON report、SQLite trace lookup 與 review status 寫回。

Report——Markdown/JSON 會輸出 security score、vulnerable code snippet、自然語言 explanation、attack path、fix suggestion、AI remediation code、local/external 報告品質 judge score 與 prompt/completion/total tokens；security score 是合約風險量化分數，judge score 評估報告完整度。

External tools——Mythril 是 EVM bytecode 符號執行工具，Echidna 是智能合約 fuzz 工具；本專案只做可選摘要整合，未安裝時結果為 `skipped`。

## 驗證結果

2026-05-04 本地驗證結果：

```text
uv run pytest                           35 passed
uv run ruff check .                     all checks passed
npm run test                            6 passed
npm run build                           completed
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30  supported_hit_rate = 1.0, score_gap = 45.05
```

2026-04-30 本地驗證結果：

```text
uv run pytest                         23 passed
uv run ruff check .                   all checks passed
uv run python eval/run_eval.py        recall_at_k = 1.0
uv run python eval/run_judge.py       local_average_judge_score = 5.0, external_average_judge_score = 5.0
uv run python scripts/validate_chunks.py data/web50/chunks.jsonl --max-unknown-rate 0.4 --min-eligible 400  unknown_rate = 0.1916, eligible_chunks = 637
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir <tmp> --rag-mode fallback  report tokens = 680/300/980, judge = 5.00/5
uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json  load_succeeded = true, peak_rss_bytes = 661,520,384
uv run python scripts/build_skill_graph.py  graphify-out artifacts generated
uv run pytest tests/test_e2e.py       2 passed, max RSS 54,231,040 bytes
```

端到端測試的記憶體使用低於 16GB 硬體上限；目前測試路徑使用 deterministic fallback。本機 `/Users/william/models/Qwen3.5-9B-MLX-4bit` 已完成 `mlx-lm` 載入 probe，峰值 RSS 661,520,384 bytes。

## 產品報告輸出

最終 PPTX：`elite-product-report/final-output/智能合約安全分析助理_產品報告.pptx`。

來源檔：

- `elite-product-report/src/product-report.md`
- `elite-product-report/src/generate.mjs`
- `elite-product-report/slides/*.html`
- `elite-product-report/shared/tokens.css`

驗證命令：

```bash
cd elite-product-report
node scripts/render.mjs
node scripts/export_deck_pptx.mjs
unzip -t final-output/智能合約安全分析助理_產品報告.pptx
```

## 已知限制

- 目前支援單檔、Foundry、Hardhat 與 generic nested import 專案；尚未執行真實 Forge 或 Hardhat build artifact workflow。
- Mythril 與完整 business-logic symbolic analysis 尚未納入。
- 真實外部高階模型 API judge 需透過 `EXTERNAL_JUDGE_COMMAND` 接入；預設 external adapter 是 deterministic rule adapter；兩者分數語義皆為報告品質，不是合約安全分數。

## 接手順序

1. 先跑 `uv sync --extra audit --dev` 與 `uv run pytest`。
2. 再跑 `uv run pytest tests/test_slither.py tests/test_project_input.py` 確認 Slither/solc 串接與專案級 import 解析。
3. 最後跑 `uv run python eval/run_eval.py`、`uv run python eval/run_judge.py`、`uv run python scripts/validate_chunks.py data/web50/chunks.jsonl --max-unknown-rate 0.4 --min-eligible 400`、`/usr/bin/time -l uv run pytest tests/test_e2e.py`。

前端驗證：`cd frontend && npm install && npm run build && npm run test`。API 啟動：`uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api`。開發預覽：`cd frontend && npm run dev`，預設 URL 為 `http://127.0.0.1:5173`，API proxy 目標為 `http://127.0.0.1:8787`。

自主迭代架構：`docs/skill-graph.md` 記錄 skill graph、多 agent 分工、缺口排序、驗證命令與文件更新規則。
圖譜產物：`uv run python scripts/build_skill_graph.py` 產生 `graphify-out/graph.json`、`graphify-out/GRAPH_REPORT.md`、`graphify-out/graph.html`。

## 文件入口

- 文件索引：`docs/DOCS_INDEX.md`
- 使用說明書：`docs/guides/001-usage-manual.md`
- 專案架構書：`docs/design/001-project-architecture.md`
- 驗證程序日誌：`docs/reference/001-validation-procedure-log.md`
