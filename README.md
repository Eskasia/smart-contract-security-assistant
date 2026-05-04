# 智能合約安全分析助理

本專案是 Solidity 智能合約安全初篩工具：單檔 `.sol`、Foundry、Hardhat 或 nested import 專案輸入後，系統執行 Slither 靜態分析、標準化 findings、檢索本地知識庫、產生可追溯報告，並輸出 JSON、Markdown 與 SQLite trace。

English README: `README.en.md`

## 快速啟動

```bash
uv sync --extra audit --dev
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api
uv run pytest
```

可選功能依需求安裝：

```bash
uv sync --extra audit --extra docs --extra rag --extra mlx --extra web --dev
```

## 前端工作台

2026-05-04 已串接本機 HTTP API，位置為 `src/smart_contract_audit/http_api.py`。React/Vite 前端位於 `frontend/`，畫面為三欄審計 triage 工作台：左欄輸入與 RAG/模型設定，中欄 finding、vulnerable code、AI explanation、attack path、remediation diff，右欄 metadata、judge、token usage、review status 與 trace evidence。

```bash
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api
cd frontend
npm install
npm run dev
npm run build
npm run test
```

開發伺服器預設為 `http://127.0.0.1:5173`，`/api/*` 會 proxy 到 `http://127.0.0.1:8787`。本機 API 支援 `POST /api/analyses`、`GET /api/analyses/{id}`、`GET /api/analyses/{id}/stream`、`GET /api/reports/{contract_id}`、`GET /api/traces/{trace_id}` 與 `PATCH /api/reports/{contract_id}/review`；API 無法連線時，前端才載入 demo report。

## 常用命令

```bash
uv run scsa analyze <contract.sol> --out-dir reports
uv run scsa analyze <contract.sol> --out-dir reports --external-tool mythril --external-tool echidna
uv run scsa analyze tests/fixtures/solidity_projects/foundry --out-dir reports
uv run scsa clean-reports data/dataset_v1.0/raw_reports data/dataset_v1.0/chunks/chunks.jsonl
uv run scsa trace-lookup reports/analysis_trace.sqlite <trace_id> --finding-id f_001
uv run scsa trace-dashboard reports/analysis_trace.sqlite
uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api
uv run python scripts/build_skill_graph.py
uv run scsa web --host 127.0.0.1 --port 7860
uv run python eval/run_eval.py
uv run python eval/run_judge.py
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30
uv run python scripts/validate_chunks.py data/web50/chunks.jsonl --max-unknown-rate 0.4 --min-eligible 400
```

## 目前範圍

- 輸入限制：支援單一 `.sol`、Foundry、Hardhat 與 generic nested import 專案；單檔最多 500 行，專案最多 100 個 Solidity 檔與 5,000 行。
- 靜態分析：Slither detector 映射 reentrancy、access control、unchecked external call（含 `unchecked-transfer`、`unused-return`）、delegatecall、controlled array length、oracle、price manipulation、privilege escalation、upgrade risk。
- RAG——Retrieval-Augmented Generation，先從本地語料找相關 chunk，再把 chunk 放入 LLM prompt 生成解釋。
- MLX——Apple Silicon 本地推理 runtime；目前有 4-bit 量化記憶體估算、`mlx-lm` 生成介面與 `scsa mlx-probe` 載入狀態記錄，支援自動探索本機 MLX 模型，未設定模型或 runtime 不可用時走 deterministic fallback。
- HTTP API——本機 stdlib server，將前端分析、SSE 狀態、report 讀取、trace lookup 與 review status 寫回串到 `analyze_contract()`、JSON report 與 SQLite trace。
- Trace——SQLite 追蹤每個 finding 的 Slither raw output、標準化結果、RAG chunk、prompt、LLM output、報告品質 judge score、token usage 與 review status。
- Security score——0–100 合約安全分數，公式版本為 `security_score_v1`，依 severity、finding confidence、partial analysis 與 business logic review penalty 計算。
- External tools——可選 `--external-tool mythril` 與 `--external-tool echidna`，工具已安裝時會把符號執行與 fuzz 摘要寫入 JSON/Markdown；未安裝時以 `skipped` 記錄。
- Benchmark——`eval/run_public_benchmark.py` 預設讀取 `eval/public_benchmark/hf-slither50-v2-manifest.json`，目前固定 50 份 Hugging Face Slither 標註樣本；支援類型命中率為 `36/36 = 1.0`，safe/vulnerable 平均安全分數差為 `45.05`。
- Report——Markdown/JSON 直接輸出 security score、vulnerable code snippet、自然語言 explanation、attack path、fix suggestion、AI remediation code、local/external 報告品質 judge score 與 prompt/completion/total tokens；judge score 評估報告完整度，security score 才是合約風險量化分數。

GitHub Actions：`.github/workflows/smart-contract-audit.yml` 提供手動掃描入口，輸入 Solidity 檔案或專案目錄後會產生 `scsa-reports` artifact。

## 驗證狀態

2026-05-04 驗證通過：`uv run pytest` 共 31 passed，`uv run ruff check .` 通過，`npm run test` 共 6 passed，`npm run build` 通過，`uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30` 支援類型命中率 `1.0`，平均安全分數差 `45.05`。2026-05-01 驗證通過：`uv run python eval/run_eval.py` 召回率 1.0，`uv run python eval/run_judge.py` local/external 報告品質平均分皆 5.0，Web50 corpus 為 `unknown_rate=0.1916`、`eligible_chunks=637`；`VulnerableVault.sol` 實測報告輸出 prompt/completion/total tokens 為 `680/300/980`，local/external 報告品質 judge score 皆 `5.00/5`。CI 已接入 ruff、pytest、RAG recall eval、judge eval。

Git baseline 已建立在 `main`，review checklist 位於 `.claude/skills/review/checklist.md` 與 `docs/review_checklist.md`。

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
