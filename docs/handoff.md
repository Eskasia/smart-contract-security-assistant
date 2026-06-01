# 智能合約安全分析助理交接

更新日期：2026-06-01。

## 已完成內容

- Python package `smart_contract_audit` 已建立，入口命令為 `scsa`。
- 核心流程為 `.sol` 或 Solidity 專案輸入 → Slither → finding normalization → JSON schema validation → RAG retrieval → LLM explanation fallback 或 MLX runtime → JSON/Markdown report → SQLite trace。
- 2026-05-04 已新增 `src/smart_contract_audit/http_api.py` 本機 HTTP API，前端可透過 `POST /api/analyses` 觸發 `analyze_contract()`，再用 SSE、report endpoint、trace endpoint 與 review PATCH 完成真實工作流。
- 2026-05-04 已將 `analyze_contract()` 拆分為流程協調層、`analysis_context.py` 輸入解析層、`finding_processor.py` finding enrichment 層與 `report_builder.py` report 組裝層，降低 analyzer 單點耦合。
- 2026-05-01 已新增 `frontend/` React/Vite 工作台，包含三欄 triage UI、Zustand 狀態、Local Storage 設定、SSE hook、1,000 ms polling fallback、virtualized findings、syntax-highlighted vulnerable code、remediation diff、review status、finding-level review feedback 與 trace evidence panel。
- 測試覆蓋 adapter、analysis context、finding processor、report builder、analyzer、RAG、Slither 串接、Foundry、Hardhat、nested import 解析、detector expansion、security score review multiplier、MLX 記憶體估算、MLX 模型自動探索、MLX probe fallback、knowledge graph artifact、schema validation、端到端流程。
- Eval 腳本已存在：`eval/run_eval.py` 測 RAG recall，`eval/run_judge.py` 同時輸出 local 與 external 報告品質 judge adapter 分數。
- CI 設定在 `.github/workflows/ci.yml`，目前執行 dependency sync、tool attribution、SBOM/license inventory、ruff、pytest、RAG eval、judge eval、paired variants、RAG groundedness、sandbox exploit validation、fuzz seed suggestions、formal property suggestions、EVMbench adapter、public benchmark、public project preflight、frontend test/build 與 whitespace check。
- 2026-05-04 已新增 `.github/workflows/smart-contract-audit.yml`，GitHub Actions 可手動輸入 Solidity 檔案或專案目錄並上傳 `scsa-reports` artifact。
- Git baseline 已建立在 `main`，review checklist 位於 `docs/review_checklist.md`。
- 2026-05-04 公開資料測試補上 `unchecked-transfer` 與 `unused-return`，統一映射到 `unchecked_external_call`。
- 2026-05-04 已新增 `security_score_v2` 合約安全分數、finding-level review multiplier、`eval/run_public_benchmark.py` 與 `eval/public_benchmark/hf-slither50-v2-manifest.json`；目前 50 份 Hugging Face Slither 標註樣本支援類型命中率為 `36/36 = 1.0`，safe/vulnerable 平均安全分數差為 `45.05`。
- 2026-05-04 已新增 Mythril/Echidna 可選整合；Mythril JSON issues 與 Echidna failed/falsified properties 會轉成正式 findings 並寫入 trace。
- 2026-05-04 已新增 Foundry/Hardhat 原生 build preflight；成功時 Slither 使用專案框架，失敗或工具缺失時回退 solc fallback 並寫入 `analysis_metadata.errors`。
- 2026-05-04 已新增 `eval/run_public_project_builds.py` 與 `eval/public_benchmark/public-project-builds-10-manifest.json`，可用 10 個 pinned public repos 自動 clone 或讀 local path，初始化 submodules、安裝 npm dependencies、支援 Hardhat 自訂 artifacts/cache 路徑，輸出 analyzer success rate、native build success rate、`forge`/`npx` 可用性與 blocker 統計；本機實測達 `10/10` analyzer 與 `10/10` native build。
- 2026-05-04 已新增 `scsa compare-reports`，可輸出新增、修復、持續存在 findings、安全分數差異與 CI fail gate。
- 2026-05-31 已將公開入口收斂為單一 `README.md`；`README.en.md` 與 `README.hackathon.md` 不再作為 GitHub 入口，hackathon reproduction 與 proof 說明保留在 `docs/archive/hackathon/`。
- 2026-05-06 已新增 HTTP API 邊界加固：bearer token、`input_root`、request body limit、固定 CORS origin 與 CLI 啟動參數。
- 2026-06-01 已收斂 native build policy 安全預設：`disabled` 是 CLI/API 預設，`trusted` 只保留給使用者明確指定的本機可信 Foundry/Hardhat 專案。
- 2026-05-06 前端已新增 native build policy 與 API token 控制；token 存在時改用 polling，避免 EventSource 無法帶 Authorization header。
- 2026-06-01 已新增 API fail-closed：非本機 host 未提供 `--api-token` 時拒絕啟動，token 模式拒絕 wildcard CORS，並加入 max concurrent jobs、event buffer 與 report read size 上限。
- 2026-05-17 已新增前端新分析 transient state reset、trace request race guard、SSE terminal status 補抓 job/report；避免舊 findings、舊 trace 或較慢 trace response 覆寫新狀態。
- 2026-05-17 已新增前端 live workflow 修正：pending report 狀態會同步 job queued/running/error，完成 report commit 會清空串流 explanation buffer，polling 改為單飛 `setTimeout`，submit/review API 失敗會顯示 HTTP 狀態對應的安全錯誤訊息；pending 或尚無正式 trace id 階段禁用整份 report review 儲存，`/reports/{contract_id}?finding={finding_id}` 可載入 report 並聚焦目標 finding，無效 finding query 會在 report 載入後清除；短狀態訊息已改用 `role=status`，選取 finding 會標記 `aria-current`，手機版 trace panel 會顯示目前 finding 摘要。
- 2026-05-17 已依 Slither、Aderyn、Echidna、SmartBugs、SolidityScan、SolidityGuard、Eagle Audit 與 audit.new 競品缺口補強三項：GitHub/Etherscan/ZIP 匯入、Echidna/External tools API 與前端開關、公開 benchmark Markdown leaderboard。
- 2026-05-17 已新增 `src/smart_contract_audit/source_import.py`、`POST /api/imports` 與 `scsa import-source`；匯入來源固定為 untrusted，分析時強制 `native_build_policy=disabled`，ZIP 會拒絕 path traversal、symlink、特殊檔、nested archive、重複正規化路徑與超量檔案，遠端來源只允許 GitHub 與 Etherscan API allowlist host，redirect target 需留在 allowlist，遠端讀取禁用環境 proxy 並有 response size cap。
- 2026-05-17 已新增 0G proof artifact hash 驗證與 chain id gate：`upload-storage.mjs`、`register-proof.mjs` 會檢查 `ZERO_G_RPC_URL` chain id，`verify-submission-proof.mjs` 會重新計算 `artifact.source_file` sha256，dry-run proof 會驗證 `storage_root_hash` 等於 artifact hash。
- 2026-05-17 public benchmark 已新增 `--leaderboard-output` 與 `--leaderboard-date`，可產生 `docs/reference/002-public-benchmark-leaderboard.md`；2026-05-06 已新增 confusion matrix、precision、recall 與 F1 指標。
- 2026-05-07 已新增 0G hackathon proof flow：`scsa 0g-package` 產生 `audit-proof.json`，`integrations/0g` 提供 Storage upload、registry deploy/register 與 proof verify scripts，`scsa 0g-attach-proof` 可把 `submission-proof.json` 回寫到 report metadata，前端右欄可顯示 0G Proof panel；live deployment 欄位仍為 pending。
- OSS readiness 基礎文件已存在：`LICENSE`、`CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`.github/ISSUE_TEMPLATE/*`、`.github/pull_request_template.md`。
- README 已整理成 SCSA 專屬 evidence workbench 敘事，包含 analyzer/AI 邊界、trace/CI/review workflow、Quick Start、Web Workbench、CLI cookbook、輸出契約、安全邊界與驗證。
- v0.1.0 release 已存在：`CHANGELOG.md` 與 `docs/archive/release/001-v0.1.0-checklist.md` 記錄 v0.1.0 scope、deferred issues、驗證命令與 GitHub release 步驟。
- Release 後外部使用證據收集文件已建立：`docs/archive/community/001-v0.1.0-tester-feedback.md`。
- Tester outreach 與 feedback tracker 已建立：`docs/archive/community/002-v0.1.0-outreach-kit.md`、`docs/archive/community/003-v0.1.0-feedback-tracker.md`。
- 2026-06-01 Phase 1 合規入口已開始落地：新增 `THIRD_PARTY_NOTICES.md`、`NOTICE`、`tool_matrix.yml`、`standards_mapping.yml`、`docs/reference/tool-attribution.md`、`docs/reference/license-boundary.md`、`docs/reference/related-work.md`、`docs/reference/standards-mapping.md`，並讓 report finding 輸出 `standard_refs`。
- 2026-06-01 Phase 2 evidence layer 已開始落地：新增 Evidence Graph SQLite tables、finding `evidence_graph`、5 個 SCSA-native post-analysis rules、paired-variant benchmark、RAG groundedness eval、UI evidence provenance 顯示與 CI gate。
- 2026-06-01 Phase 3 advanced evidence 已開始落地：新增 `exploit_validation`、sandbox-only Foundry reentrancy PoC fixture、fuzz seed suggestions、formal property drafts、DeFi profit signal、EVMbench adapter、SQLite `exploit_validations` 與 UI advanced evidence 顯示。
- 2026-06-01 PR #15 與 PR #16 已 merge 到 `main`；`main` smoke 通過 `uv run pytest` 116 passed、frontend 35 passed、frontend build completed。v0.2.0 已發布為 evidence platform release；不是正式 audit certification release。

## 技術核心

Slither——Solidity 靜態分析工具，負責 deterministic vulnerability finding；LLM 不負責判定漏洞，只負責把 finding 轉成可讀解釋、攻擊路徑與修復建議。

RAG——Retrieval-Augmented Generation，先從審計語料與技術文件 chunk 檢索證據，再把證據放入 prompt，降低生成內容脫離資料來源的風險。

MLX——Apple Silicon 本地推理 runtime，本專案以 4-bit 權重量化估算記憶體需求，`8B` 參數模型在 4-bit 權重下約需 `4.0GB` 權重記憶體；`uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json` 會輸出模型路徑、量化位元、預估權重記憶體、fallback 原因、load_succeeded 與 peak_rss_bytes。

Trace——SQLite 分析追蹤表，保存 finding、raw Slither output、RAG chunks、prompt、LLM output、報告品質 judge score、token usage、partial 狀態、review status 與 review note，用於除錯與報告回溯；`scsa trace-dashboard` 可列出 trace id、dataset version、model version、review status。

HTTP API——本機 stdlib `ThreadingHTTPServer`，加固入口命令為 `uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --max-concurrent-jobs 4 --max-events-per-job 256 --max-report-bytes 5000000 --native-build-policy disabled`；支援 analysis job、SSE stream、JSON report、Markdown report download、SQLite trace lookup、整份 report review status 與逐條 finding review 寫回。外部 host 必須提供 bearer token，token 模式必須使用固定 CORS origin。

Source import——`POST /api/imports` 與 `scsa import-source` 支援 GitHub archive、Etherscan mainnet/sepolia API allowlist 與 ZIP；匯入後回傳 `input_path`、`import_id`、`source_kind`、`extracted_files`、`total_bytes`、`trust_level=untrusted`，前端可直接把 `input_path` 接到 `POST /api/analyses`。匯入目錄預設為 `reports-api/imports` 或 API `output_dir/imports`，可用 `--imports-dir` 與 import size limits 調整；過期 staging 目錄可用 `uv run scsa clean-imports --imports-dir reports-api/imports --ttl-seconds 86400` 清理。遠端匯入會禁用環境 proxy、在 redirect 前檢查 target host、讀取後驗證 final response URL，並在超過 `max_total_bytes + 65,536` bytes 時拒絕回應。

Report——Markdown/JSON 會輸出 security score、逐條 finding review status/note、vulnerable code snippet、自然語言 explanation、attack path、fix suggestion、AI remediation code、local/external 報告品質 judge score 與 prompt/completion/total tokens；前端可複製 `/reports/{contract_id}?finding={finding_id}` deep link 並下載 JSON/Markdown report，下載使用 `Authorization` header，不把 API token 放入 URL；security score 是合約風險量化分數，judge score 評估報告完整度。

External tools——Mythril 是 EVM bytecode 符號執行工具，Echidna/Medusa 是智能合約 fuzz 工具，Aderyn 是 Rust 靜態分析器，Halmos 是 Foundry symbolic testing runner；Mythril JSON issues、Echidna/Medusa failed/falsified properties、Aderyn JSON issues 與 Halmos proof failures 會轉成正式 finding 與 trace row，Aderyn SARIF 只以 `artifact_paths.sarif` 記錄 artifact path。CLI 用 `--external-tool`，HTTP API 用 `external_tools` 與 `external_timeout_seconds`，server 會去重、套用 allowlist 並把 timeout 限制在 5–120 秒；report 會記錄 execution mode、binary path、command、timeout、duration、status 與 output/artifact paths；`halmos` 需要 trusted Foundry project，未安裝時結果為 `skipped`。

Standards mapping——`standards_mapping.yml` 是 internal finding type 到 OWASP Smart Contract Top 10、SCWE、SCSVS 與 SWC 的 deterministic mapping；JSON report 每個 finding 會輸出 `standard_refs`，Markdown report 會顯示 Standards 行。找不到 mapping 時輸出空陣列，不由 LLM 補值。

Evidence Graph——`analysis_trace.sqlite` 目前含 `evidence_nodes`、`evidence_edges`、`evidence_claims`，每個 finding 會連到 tool signal、source range、trace row、RAG chunk、LLM claim、review action、standard ref 與 SCSA-native rule result。JSON report 的 `evidence_graph` 提供 UI 顯示用摘要，`eval/run_rag_groundedness.py` 要求 unsupported security claim 為 `0`。

SCSA-native rules——Phase 2 已新增 reentrancy evidence confirmer、auth-sensitive state write checker、unchecked low-level call canonicalizer、upgradeable proxy risk mapper、multi-tool consensus scorer。這些 rules 只在 analyzer evidence 之上做 confirmation / confidence decomposition，不取代 Slither 或 external tools。

Paired variants——`eval/paired_variants/` 目前涵蓋 `reentrancy`、`unchecked_external_call`、`access_control`、`upgrade_risk`、`dangerous_delegatecall` 五類，每類 3 組 positive/negative pair；`uv run python eval/run_paired_variants.py --min-paired-pass-rate 0.70` 會輸出 `reports/eval/paired_variant_results.json`、`benchmark_summary.md` 與 `benchmark_matrix.json`。

Phase 3 advanced evidence——`exploit_validation` 預設為 `not_attempted` 且 `mode=sandbox_only`；正常分析不自動執行 PoC。`uv run python eval/run_exploit_validation.py` 只跑 `tests/poc/reentrancy/` 本地 Foundry fixture，輸出 `reports/poc/f_001/validation.json` 與 `execution.log`。`fuzz_seed_suggestions` 與 `formal_property_suggestions` 都是 reviewer starting point；property 未 compile/verify 前固定 `status=draft`、`verification_status=not_proven`。`defi_profit_signal` 只能承接 local execution 或 trusted external-tool output。

UI design system——2026-05-31 已新增 `docs/design/005-ui-design-system.md`；前端定位為 evidence-first security console，使用 CSS variables/Tailwind tokens、shared `Button`/`Field`/`PanelSection`/`MetricGroup`、四工具 `ToolSelector` 與 `min-h-dvh` layout。Legacy `echidnaEnabled` persisted setting 會 migration 成 `externalTools=["echidna"]`，API token 仍不持久化。

Native build preflight——Foundry/Hardhat 專案在 `trusted` 模式先跑 `forge build` 或 Hardhat compile；成功後 Slither 不帶 `--compile-force-framework solc`，失敗或工具缺失時保留 solc fallback；`disabled` 模式略過 build scripts，適合未信任 public repo。

Public project build validation——`eval/run_public_project_builds.py` 預設讀取 `eval/public_benchmark/public-project-builds-10-manifest.json`；`--preflight-only` 不 clone 即回報 framework 分布與缺失工具，完整模式會 clone、初始化 submodules、安裝 npm dependencies、處理 Hardhat 自訂 artifacts/cache 路徑並產出 `public_project_builds_summary.json`，可用 `--min-analyzer-success-rate` 與 `--min-native-build-success-rate` 設門檻。

Report comparison——兩份 JSON 報告的差異比較，用 finding type、detector、檔名與 line_start 作穩定 key；`--fail-on-high-added` 與 `--fail-on-score-drop` 可讓 CI 在安全回退時失敗。

0G proof package——`uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --native-build-policy disabled > reports/latest-analysis.json` 後用 `REPORT_ID=$(uv run python -c 'import json; print(json.load(open("reports/latest-analysis.json"))["contract_id"])')` 取得實際報告 id；`uv run scsa 0g-package reports/latest-analysis.json --out-dir reports-0g --project-name "SCSA 0G Audit Proof" --track "Track 1: Agentic Infrastructure & OpenClaw Lab"` 產生 hash-stable `audit-proof.json`；本地驗證用 `cd integrations/0g && npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json" --dry-run && npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"`。Dry-run `proof_mode` 為 `dry_run` 且 `explorer_links` 為空；Live proof 仍需 funded `ZERO_G_PRIVATE_KEY`、`ZERO_G_RPC_URL=https://evmrpc.0g.ai`、`ZERO_G_STORAGE_INDEXER_RPC=https://indexer-storage-turbo.0g.ai`，先 `npm run deploy`，再設定 `ZERO_G_REGISTRY_ADDRESS` 後執行 live upload/register/verify；live registered `explorer_links` 欄位為 `storage_tx`、`registry`、`registration_tx`，預設指向 ChainScan。

## 驗證結果

2026-06-01 Phase 1-3 roadmap 驗證結果：

```text
uv sync --extra audit --dev           resolved 198 packages, checked 83 packages
uv run ruff check .                   all checks passed
uv run pytest                         116 passed
uv run python eval/run_eval.py        recall_at_k = 1.0
uv run python eval/run_judge.py       local_average_judge_score = 5.0, external_average_judge_score = 5.0
uv run python eval/run_paired_variants.py --min-paired-pass-rate 0.70  paired_pass_rate = 1.0, precision = 1.0, recall = 1.0, f1 = 1.0
uv run python eval/run_rag_groundedness.py --max-unsupported-security-claims 0  unsupported_security_claims = 0
uv run python eval/run_exploit_validation.py  status = executed_triggered, mode = local_foundry_test
uv run python eval/run_fuzz_seed_suggestions.py --min-seed-count 1  seed_count = 1
uv run python eval/run_formal_property_suggestions.py --min-property-count 1  property_count = 1
uv run python eval/run_evmbench_adapter.py  exploit_adapter = sandbox_only, unauthorized_targets_blocked = true
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5  supported_hit_rate = 1.0, precision = 0.8621, recall = 1.0, f1 = 0.9259
uv run python eval/run_public_project_builds.py --preflight-only  missing_required_tools = []
uv run python scripts/check_tool_matrix.py  passed
uv run python scripts/generate_sbom.py      generated tool-matrix SBOM and license inventory
uv run cyclonedx-py environment --output-file reports/sbom/python.cdx.json  passed
uv run pip-licenses --format=plain-vertical --output-file reports/licenses/python-licenses.txt  passed
cd frontend && npx @cyclonedx/cyclonedx-npm --output-file ../reports/sbom/frontend.cdx.json  passed
cd frontend && npm ls --json > ../reports/licenses/npm-tree.json  passed
cd frontend && npm run test -- --run  35 passed
cd frontend && npm run build          completed
git diff --check                     passed
```

2026-05-24 剩餘 9% 補強驗證結果：

```text
uv run ruff check .        all checks passed
uv run pytest              102 passed
uv run python eval/run_eval.py  recall_at_k = 1.0
uv run python eval/run_judge.py  local_average_judge_score = 5.0, external_average_judge_score = 5.0
uv run python eval/run_paired_variants.py --min-paired-pass-rate 0.70  paired_pass_rate = 1.0, precision = 1.0, recall = 1.0, f1 = 1.0
uv run python eval/run_rag_groundedness.py --max-unsupported-security-claims 0  unsupported_security_claims = 0
uv run python eval/run_exploit_validation.py  status = executed_triggered, mode = local_foundry_test
uv run python eval/run_fuzz_seed_suggestions.py --min-seed-count 1  seed_count = 1
uv run python eval/run_formal_property_suggestions.py --min-property-count 1  property_count = 1
uv run python eval/run_evmbench_adapter.py  exploit_adapter = sandbox_only, unauthorized_targets_blocked = true
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5  supported_hit_rate = 1.0, precision = 0.8621, recall = 1.0, f1 = 0.9259
uv run python eval/run_public_project_builds.py --preflight-only  missing_required_tools = []
cd frontend && npm run test -- --run  33 passed
cd frontend && npm run build          completed
git diff --check                    passed
Chrome headless CDP                 report deep-link, JSON download, Markdown download controls rendered; 390px mobile width has no button overflow
```

2026-05-17 前端驗證結果：

```text
uv run ruff check .        all checks passed
uv run pytest              102 passed
uv run python eval/run_eval.py  recall_at_k = 1.0
uv run python eval/run_judge.py  local_average_judge_score = 5.0, external_average_judge_score = 5.0
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5 --leaderboard-output docs/reference/002-public-benchmark-leaderboard.md --leaderboard-date 2026-05-17  completed, leaderboard generated
uv run python eval/run_public_project_builds.py --preflight-only  missing_required_tools = []
cd frontend && npm run test -- --run  32 passed
cd frontend && npm run build          completed
git diff --check                    passed
Chrome headless CDP + local API/Vite  live analysis, pending/failed-placeholder review disable, report/trace load, route failure empty state, invalid finding query cleanup, deep link focus, review PATCH, mobile trace summary verified
```

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
uv run python scripts/build_knowledge_graph.py  knowledge-graph-out artifacts generated
uv run pytest tests/test_e2e.py       2 passed, max RSS 54,231,040 bytes
```

2026-05-31 README / OSS readiness 更新驗證結果：

```text
uv sync --extra audit --dev           installed audit dependencies
uv run ruff check .                   all checks passed
uv run pytest                         15 passed
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports-demo
                                      overall_status = finding, f_001 = reentrancy, severity = 3
```

端到端測試的記憶體使用低於 16GB 硬體上限；目前測試路徑使用 deterministic fallback。本機 `/Users/william/models/Qwen3.5-9B-MLX-4bit` 已完成 `mlx-lm` 載入 probe，峰值 RSS 661,520,384 bytes。

## 已知限制

- 目前支援單檔、Foundry、Hardhat、generic nested import 專案、GitHub archive、Etherscan API 與 ZIP 匯入；匯入來源一律視為未信任，原生 build scripts 會被停用。
- 完整 business-logic symbolic analysis 尚未納入。
- 真實外部高階模型 API judge 需透過 `EXTERNAL_JUDGE_COMMAND` 接入；預設 external adapter 是 deterministic rule adapter；兩者分數語義皆為報告品質，不是合約安全分數。

## 接手順序

1. 先跑 `uv sync --extra audit --dev` 與 `uv run pytest`。
2. 再跑 `uv run pytest tests/test_slither.py tests/test_project_input.py` 確認 Slither/solc 串接與專案級 import 解析。
3. 最後跑 `uv run python eval/run_eval.py`、`uv run python eval/run_judge.py`、`uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5 --leaderboard-output docs/reference/002-public-benchmark-leaderboard.md --leaderboard-date 2026-05-17`、`/usr/bin/time -l uv run pytest tests/test_e2e.py`。

前端驗證：`cd frontend && npm install && npm run build && npm run test`。API 啟動：`uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --max-concurrent-jobs 4 --max-events-per-job 256 --max-report-bytes 5000000 --native-build-policy disabled`。開發預覽：`cd frontend && npm run dev`，預設 URL 為 `http://127.0.0.1:5173`，API proxy 目標為 `http://127.0.0.1:8787`。

Knowledge graph：`docs/knowledge-graph.md` 記錄 source import、Slither、external tools、RAG、report、trace、review 與 CI 的能力/證據關係。
圖譜產物：`uv run python scripts/build_knowledge_graph.py` 產生本機 `knowledge-graph-out/`，該目錄不追蹤到 GitHub。

## 文件入口

- 文件索引：`docs/DOCS_INDEX.md`
- Third-party notices：`THIRD_PARTY_NOTICES.md`
- Tool attribution：`docs/reference/tool-attribution.md`
- License boundary：`docs/reference/license-boundary.md`
- Related work：`docs/reference/related-work.md`
- Standards mapping：`docs/reference/standards-mapping.md`
- Public benchmark leaderboard：`docs/reference/002-public-benchmark-leaderboard.md`
- Changelog：`CHANGELOG.md`
- v0.1.0 release checklist：`docs/archive/release/001-v0.1.0-checklist.md`
- v0.2.0 release checklist：`docs/archive/release/002-v0.2.0-checklist.md`
- v0.1.0 tester feedback guide：`docs/archive/community/001-v0.1.0-tester-feedback.md`
- v0.1.0 tester outreach kit：`docs/archive/community/002-v0.1.0-outreach-kit.md`
- v0.1.0 feedback tracker：`docs/archive/community/003-v0.1.0-feedback-tracker.md`
- 使用說明書：`docs/guides/001-usage-manual.md`
- 專案架構書：`docs/design/001-project-architecture.md`
- Knowledge graph：`docs/knowledge-graph.md`
- 競品導向優化計畫：`docs/archive/design/004-competitor-optimization-plan.md`
- 驗證程序日誌：`docs/reference/001-validation-procedure-log.md`
- 公開 benchmark leaderboard：`docs/reference/002-public-benchmark-leaderboard.md`
