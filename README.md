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

2026-05-04 已串接本機 HTTP API，位置為 `src/smart_contract_audit/http_api.py`。React/Vite 前端位於 `frontend/`，畫面為三欄審計 triage 工作台：左欄輸入與 RAG/模型設定，中欄 finding、vulnerable code、AI explanation、attack path、remediation diff 與逐條 finding 審核回饋，右欄 metadata、judge、token usage、review status 與 trace evidence。

```bash
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api
cd frontend
npm install
npm run dev
npm run build
npm run test
```

開發伺服器預設為 `http://127.0.0.1:5173`，`/api/*` 會 proxy 到 `http://127.0.0.1:8787`。本機 API 支援 `POST /api/analyses`、`GET /api/analyses/{id}`、`GET /api/analyses/{id}/stream`、`GET /api/reports/{contract_id}`、`GET /api/traces/{trace_id}`、`PATCH /api/reports/{contract_id}/review` 與 `PATCH /api/reports/{contract_id}/findings/{finding_id}/review`；API 無法連線時，前端才載入 demo report。

## 常用命令

```bash
uv run scsa analyze <contract.sol> --out-dir reports
uv run scsa analyze <contract.sol> --out-dir reports --external-tool mythril --external-tool echidna
uv run scsa compare-reports reports/base.json reports/head.json --output reports/comparison.md --fail-on-high-added --fail-on-score-drop 10
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
uv run python eval/run_public_project_builds.py --min-analyzer-success-rate 1.0 --min-native-build-success-rate 1.0
```

## 目前範圍

- 輸入限制：支援單一 `.sol`、Foundry、Hardhat 與 generic nested import 專案；Foundry/Hardhat 會先嘗試原生 build，失敗時回退 Slither/solc 並寫入錯誤原因；單檔最多 500 行，專案最多 500 個 Solidity 檔與 100,000 行。
- 靜態分析：Slither detector 映射 reentrancy、access control、unchecked external call（含 `unchecked-transfer`、`unused-return`）、delegatecall、controlled array length、oracle、price manipulation、privilege escalation、upgrade risk。
- RAG——Retrieval-Augmented Generation，先從本地語料找相關 chunk，再把 chunk 放入 LLM prompt 生成解釋。
- MLX——Apple Silicon 本地推理 runtime；目前有 4-bit 量化記憶體估算、`mlx-lm` 生成介面與 `scsa mlx-probe` 載入狀態記錄，支援自動探索本機 MLX 模型，未設定模型或 runtime 不可用時走 deterministic fallback。
- HTTP API——本機 stdlib server，將前端分析、SSE 狀態、report 讀取、trace lookup、整份 report review status 與逐條 finding review 寫回串到 `analyze_contract()`、JSON report 與 SQLite trace。
- Analyzer modules——`analyze_contract()` 僅保留流程協調；`analysis_context.py` 負責輸入解析、限制檢查、contract id 與人工審核原因，`finding_processor.py` 負責 finding enrichment、RAG、LLM fallback、token 統計與 trace finding 寫入，`report_builder.py` 負責 report metadata、security score、overall/review status 與 trace finish。
- Trace——SQLite 追蹤每個 finding 的 Slither raw output、標準化結果、RAG chunk、prompt、LLM output、報告品質 judge score、token usage、review status 與 review note。
- Security score——0–100 合約安全分數，公式版本為 `security_score_v2`，依 severity、finding confidence、finding review status、partial analysis 與 business logic review penalty 計算；`false_positive` 懲罰係數為 0.0，`fixed` 懲罰係數為 0.2。
- External tools——可選 `--external-tool mythril` 與 `--external-tool echidna`；Mythril JSON issues 與 Echidna failed/falsified properties 會轉成正式 findings 並寫入 trace；未安裝時以 `skipped` 記錄。
- Report comparison——`compare-reports` 會輸出新增、修復、持續存在 findings 與安全分數差異，可用 `--fail-on-high-added`、`--fail-on-score-drop 10` 作 CI fail gate。
- Benchmark——`eval/run_public_benchmark.py` 預設讀取 `eval/public_benchmark/hf-slither50-v2-manifest.json`，目前固定 50 份 Hugging Face Slither 標註樣本；支援類型命中率為 `36/36 = 1.0`，safe/vulnerable 平均安全分數差為 `45.05`。
- Public project build validation——`eval/run_public_project_builds.py` 預設讀取 `eval/public_benchmark/public-project-builds-10-manifest.json`，`--preflight-only` 不 clone 即回報 10 個 public repos、framework 分布、`forge`/`npx` 可用性；完整模式會自動 clone、初始化 submodules、安裝 npm dependencies、支援 Hardhat 自訂 artifacts/cache 路徑，輸出 analyzer success rate、native build success rate 與 native build blocker 統計。2026-05-04 實測 10 個 pinned public repos 達 `10/10` analyzer 與 `10/10` native build。
- Report——Markdown/JSON 直接輸出 security score、逐條 finding review status/note、vulnerable code snippet、自然語言 explanation、attack path、fix suggestion、AI remediation code、local/external 報告品質 judge score 與 prompt/completion/total tokens；judge score 評估報告完整度，security score 才是合約風險量化分數。

GitHub Actions：`.github/workflows/smart-contract-audit.yml` 提供手動掃描入口，輸入 Solidity 檔案或專案目錄後會產生 `scsa-reports` artifact；提供 `baseline_report` 時會額外產生 `comparison.md` 並可用高危新增或分數下降門檻讓 CI 失敗。

## 驗證狀態

2026-05-04 驗證通過：`uv run pytest` 共 69 passed，`uv run ruff check .` 通過，`npm run test` 共 7 passed，`npm run build` 通過，`uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30` 支援類型命中率 `1.0`，平均安全分數差 `45.05`，`uv run python eval/run_public_project_builds.py --min-analyzer-success-rate 1.0 --min-native-build-success-rate 1.0` 達 `10/10` analyzer 與 `10/10` native build。2026-05-01 驗證通過：`uv run python eval/run_eval.py` 召回率 1.0，`uv run python eval/run_judge.py` local/external 報告品質平均分皆 5.0；`VulnerableVault.sol` 實測報告輸出 prompt/completion/total tokens 為 `680/300/980`，local/external 報告品質 judge score 皆 `5.00/5`。CI 已接入 ruff、pytest、RAG recall eval、judge eval。

Git baseline 已建立在 `main`，review checklist 位於 `docs/review_checklist.md`。

## 交接文件

完整接手資訊在 `docs/handoff.md`。使用說明書在 `docs/guides/001-usage-manual.md`，專案架構書在 `docs/design/001-project-architecture.md`，驗證程序日誌在 `docs/reference/001-validation-procedure-log.md`，文件索引在 `docs/DOCS_INDEX.md`。專案內 agent 操作規則在 `AGENTS.md`。

自主迭代用 skill graph 在 `docs/skill-graph.md`，定義多 agent 分工、能力節點、缺口排序與驗證閉環；`graphify-out/` 為本機可重建輸出，不追蹤到 GitHub。
