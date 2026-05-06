# 智能合約安全分析助理交接

更新日期：2026-05-07。

## 已完成內容

- Python package `smart_contract_audit` 已建立，入口命令為 `scsa`。
- 核心流程為 `.sol` 或 Solidity 專案輸入 → Slither → finding normalization → JSON schema validation → RAG retrieval → LLM explanation fallback 或 MLX runtime → JSON/Markdown report → SQLite trace。
- 2026-05-04 已新增 `src/smart_contract_audit/http_api.py` 本機 HTTP API，前端可透過 `POST /api/analyses` 觸發 `analyze_contract()`，再用 SSE、report endpoint、trace endpoint 與 review PATCH 完成真實工作流。
- 2026-05-04 已將 `analyze_contract()` 拆分為流程協調層、`analysis_context.py` 輸入解析層、`finding_processor.py` finding enrichment 層與 `report_builder.py` report 組裝層，降低 analyzer 單點耦合。
- 2026-05-01 已新增 `frontend/` React/Vite 工作台，包含三欄 triage UI、Zustand 狀態、Local Storage 設定、SSE hook、1,000 ms polling fallback、virtualized findings、syntax-highlighted vulnerable code、remediation diff、review status、finding-level review feedback 與 trace evidence panel。
- 測試覆蓋 adapter、analysis context、finding processor、report builder、analyzer、RAG、Slither 串接、Foundry、Hardhat、nested import 解析、detector expansion、security score review multiplier、MLX 記憶體估算、MLX 模型自動探索、MLX probe fallback、skill graph artifact、schema validation、端到端流程。
- Eval 腳本已存在：`eval/run_eval.py` 測 RAG recall，`eval/run_judge.py` 同時輸出 local 與 external 報告品質 judge adapter 分數。
- CI 設定在 `.github/workflows/ci.yml`，目前執行 ruff、pytest、RAG eval 與 judge eval。
- 2026-05-04 已新增 `.github/workflows/smart-contract-audit.yml`，GitHub Actions 可手動輸入 Solidity 檔案或專案目錄並上傳 `scsa-reports` artifact。
- Git baseline 已建立在 `main`，review checklist 位於 `docs/review_checklist.md`。
- 2026-05-04 公開資料測試補上 `unchecked-transfer` 與 `unused-return`，統一映射到 `unchecked_external_call`。
- 2026-05-04 已新增 `security_score_v2` 合約安全分數、finding-level review multiplier、`eval/run_public_benchmark.py` 與 `eval/public_benchmark/hf-slither50-v2-manifest.json`；目前 50 份 Hugging Face Slither 標註樣本支援類型命中率為 `36/36 = 1.0`，safe/vulnerable 平均安全分數差為 `45.05`。
- 2026-05-04 已新增 Mythril/Echidna 可選整合；Mythril JSON issues 與 Echidna failed/falsified properties 會轉成正式 findings 並寫入 trace。
- 2026-05-04 已新增 Foundry/Hardhat 原生 build preflight；成功時 Slither 使用專案框架，失敗或工具缺失時回退 solc fallback 並寫入 `analysis_metadata.errors`。
- 2026-05-04 已新增 `eval/run_public_project_builds.py` 與 `eval/public_benchmark/public-project-builds-10-manifest.json`，可用 10 個 pinned public repos 自動 clone 或讀 local path，初始化 submodules、安裝 npm dependencies、支援 Hardhat 自訂 artifacts/cache 路徑，輸出 analyzer success rate、native build success rate、`forge`/`npx` 可用性與 blocker 統計；本機實測達 `10/10` analyzer 與 `10/10` native build。
- 2026-05-04 已新增 `scsa compare-reports`，可輸出新增、修復、持續存在 findings、安全分數差異與 CI fail gate。
- 2026-05-04 已新增英文版 `README.en.md`。
- 2026-05-06 已新增 HTTP API 邊界加固：bearer token、`input_root`、request body limit、固定 CORS origin 與 CLI 啟動參數。
- 2026-05-06 已新增 native build policy：`trusted` 保留 Foundry/Hardhat 原生 build，`disabled` 略過 build scripts 並使用 Slither/solc fallback。
- 2026-05-06 前端已新增 native build policy 與 API token 控制；token 存在時改用 polling，避免 EventSource 無法帶 Authorization header。
- 2026-05-06 public benchmark 已新增 confusion matrix、precision、recall 與 F1 指標。
- 2026-05-07 已新增 0G hackathon proof flow：`scsa 0g-package` 產生 `audit-proof.json`，`integrations/0g` 提供 Storage upload、registry deploy/register 與 proof verify scripts，`scsa 0g-attach-proof` 可把 `submission-proof.json` 回寫到 report metadata，前端右欄可顯示 0G Proof panel；live deployment 欄位仍為 pending。

## 技術核心

Slither——Solidity 靜態分析工具，負責 deterministic vulnerability finding；LLM 不負責判定漏洞，只負責把 finding 轉成可讀解釋、攻擊路徑與修復建議。

RAG——Retrieval-Augmented Generation，先從審計語料與技術文件 chunk 檢索證據，再把證據放入 prompt，降低生成內容脫離資料來源的風險。

MLX——Apple Silicon 本地推理 runtime，本專案以 4-bit 權重量化估算記憶體需求，`8B` 參數模型在 4-bit 權重下約需 `4.0GB` 權重記憶體；`uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json` 會輸出模型路徑、量化位元、預估權重記憶體、fallback 原因、load_succeeded 與 peak_rss_bytes。

Trace——SQLite 分析追蹤表，保存 finding、raw Slither output、RAG chunks、prompt、LLM output、報告品質 judge score、token usage、partial 狀態、review status 與 review note，用於除錯與報告回溯；`scsa trace-dashboard` 可列出 trace id、dataset version、model version、review status。

HTTP API——本機 stdlib `ThreadingHTTPServer`，加固入口命令為 `uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --native-build-policy disabled`；支援 analysis job、SSE stream、JSON report、SQLite trace lookup、整份 report review status 與逐條 finding review 寫回。

Report——Markdown/JSON 會輸出 security score、逐條 finding review status/note、vulnerable code snippet、自然語言 explanation、attack path、fix suggestion、AI remediation code、local/external 報告品質 judge score 與 prompt/completion/total tokens；security score 是合約風險量化分數，judge score 評估報告完整度。

External tools——Mythril 是 EVM bytecode 符號執行工具，Echidna 是智能合約 fuzz 工具；Mythril JSON issues 與 Echidna failed/falsified properties 會轉成正式 finding 與 trace row，未安裝時結果為 `skipped`。

Native build preflight——Foundry/Hardhat 專案在 `trusted` 模式先跑 `forge build` 或 Hardhat compile；成功後 Slither 不帶 `--compile-force-framework solc`，失敗或工具缺失時保留 solc fallback；`disabled` 模式略過 build scripts，適合未信任 public repo。

Public project build validation——`eval/run_public_project_builds.py` 預設讀取 `eval/public_benchmark/public-project-builds-10-manifest.json`；`--preflight-only` 不 clone 即回報 framework 分布與缺失工具，完整模式會 clone、初始化 submodules、安裝 npm dependencies、處理 Hardhat 自訂 artifacts/cache 路徑並產出 `public_project_builds_summary.json`，可用 `--min-analyzer-success-rate` 與 `--min-native-build-success-rate` 設門檻。

Report comparison——兩份 JSON 報告的差異比較，用 finding type、detector、檔名與 line_start 作穩定 key；`--fail-on-high-added` 與 `--fail-on-score-drop` 可讓 CI 在安全回退時失敗。

0G proof package——`uv run scsa 0g-package reports/vulnerablevault.json --out-dir reports-0g --project-name "SCSA 0G Audit Proof" --track "Track 1: Agentic Infrastructure & OpenClaw Lab"` 產生 hash-stable `audit-proof.json`；本地驗證用 `cd integrations/0g && npm run upload -- ../../reports-0g/vulnerablevault/audit-proof.json --dry-run && npm run verify-proof -- ../../reports-0g/vulnerablevault/submission-proof.json`。Live proof 仍需設定 `ZERO_G_RPC_URL`、`ZERO_G_PRIVATE_KEY`、`ZERO_G_STORAGE_INDEXER_RPC`，先 `npm run deploy`，再設定 `ZERO_G_REGISTRY_ADDRESS` 後執行 live upload/register；`explorer_links` 欄位為 `storage_tx`、`registry`、`registration_tx`。

## 驗證結果

2026-05-06 本地驗證結果：

```text
uv run ruff check .                     all checks passed
uv run pytest                           75 passed, 2 warnings
npm run test                            8 passed
npm run build                           completed
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5  supported_hit_rate = 1.0, score_gap = 45.05, precision = 0.8621, recall = 1.0, f1 = 0.9259
uv run python eval/run_public_project_builds.py --preflight-only  missing_required_tools = []
```

2026-05-04 本地驗證結果：

```text
uv run pytest                           69 passed
uv run ruff check .                     all checks passed
npm run test                            7 passed
npm run build                           completed
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30  supported_hit_rate = 1.0, score_gap = 45.05
uv run python eval/run_public_project_builds.py --min-analyzer-success-rate 1.0 --min-native-build-success-rate 1.0  analyzer_success_rate = 1.0, native_build_success_rate = 1.0
```

2026-04-30 本地驗證結果：

```text
uv run pytest                         23 passed
uv run ruff check .                   all checks passed
uv run python eval/run_eval.py        recall_at_k = 1.0
uv run python eval/run_judge.py       local_average_judge_score = 5.0, external_average_judge_score = 5.0
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir <tmp> --rag-mode fallback  report tokens = 680/300/980, judge = 5.00/5
uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json  load_succeeded = true, peak_rss_bytes = 661,520,384
uv run python scripts/build_skill_graph.py  graphify-out artifacts generated
uv run pytest tests/test_e2e.py       2 passed, max RSS 54,231,040 bytes
```

端到端測試的記憶體使用低於 16GB 硬體上限；目前測試路徑使用 deterministic fallback。本機 `/Users/william/models/Qwen3.5-9B-MLX-4bit` 已完成 `mlx-lm` 載入 probe，峰值 RSS 661,520,384 bytes。

## 已知限制

- 目前支援單檔、Foundry、Hardhat 與 generic nested import 專案；Foundry/Hardhat 原生 build preflight 已用 10 個 pinned public repos 驗證 `10/10` analyzer 與 `10/10` native build。
- 完整 business-logic symbolic analysis 尚未納入。
- 真實外部高階模型 API judge 需透過 `EXTERNAL_JUDGE_COMMAND` 接入；預設 external adapter 是 deterministic rule adapter；兩者分數語義皆為報告品質，不是合約安全分數。

## 接手順序

1. 先跑 `uv sync --extra audit --dev` 與 `uv run pytest`。
2. 再跑 `uv run pytest tests/test_slither.py tests/test_project_input.py` 確認 Slither/solc 串接與專案級 import 解析。
3. 最後跑 `uv run python eval/run_eval.py`、`uv run python eval/run_judge.py`、`uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5`、`/usr/bin/time -l uv run pytest tests/test_e2e.py`。

前端驗證：`cd frontend && npm install && npm run build && npm run test`。API 啟動：`uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --native-build-policy disabled`。開發預覽：`cd frontend && npm run dev`，預設 URL 為 `http://127.0.0.1:5173`，API proxy 目標為 `http://127.0.0.1:8787`。

自主迭代架構：`docs/skill-graph.md` 記錄 skill graph、多 agent 分工、缺口排序、驗證命令與文件更新規則。
圖譜產物：`uv run python scripts/build_skill_graph.py` 產生本機 `graphify-out/`，該目錄不追蹤到 GitHub。

## 文件入口

- 文件索引：`docs/DOCS_INDEX.md`
- 使用說明書：`docs/guides/001-usage-manual.md`
- 專案架構書：`docs/design/001-project-architecture.md`
- 驗證程序日誌：`docs/reference/001-validation-procedure-log.md`
