---
title: "90% 使用率優化建構書"
description: "規劃把試用率、持續使用率與答案滿意度推到 90% 的工程路線。"
category: "design"
number: "003"
status: draft
services: ["src/smart_contract_audit", "eval", ".github/workflows", "frontend", "docs"]
related: ["design/001", "design/002", "guides/001", "reference/001"]
last_modified: "2026-05-04"
---

# 003 — 90% 使用率優化建構書

## Status

draft；依據 2026-05-04 公開 Hugging Face Slither 標註資料測試、目前產品功能與使用率推估建立。Phase 1 已完成 `security_score_v2`、finding-level review multiplier、public benchmark harness、50 份樣本 manifest、safe/vulnerable 分數差 gate 與前端 security score 顯示；100 份 benchmark 仍待擴充。

## Summary

決策：把專案從「本地安全初篩工具」升級為「可被智能合約開發者反覆使用的審計工作流」。核心路線是信任層先補量化分數與 benchmark，能力層補工具覆蓋與專案級編譯，工作流層接入 GitHub/CI、歷史比較與可交付報告。

## Terms

試用率——智能合約相關人士第一次看到專案後，願意拿自己的合約或公開合約跑一次的比例。

持續使用率——使用者第一次試用後，仍在每週開發或審計流程中重複使用的比例。

答案滿意度——使用者對報告可讀性、準確度、可追溯性、修復建議可用性的 0–100 主觀評分。

命中率——公開標註資料中的漏洞類型，在本專案輸出 finding 中出現同類型結果的比例。

安全分數——依 severity、confidence、未修復 finding、人工 review 狀態與 benchmark 權重計算的 0–100 合約風險分數。

CI——Continuous Integration，每次 push 或 pull request 自動跑測試、分析與品質門檻。

## Target Metrics

| 指標 | 目前估算 | 目標 | 必要條件 |
|---|---:|---:|---|
| 試用率 | 65% | 90% | 安全分數、公開 benchmark、5 分鐘內可看懂 demo |
| 持續使用率 | 38% | 90% | GitHub/CI、歷史差異、誤報回寫、專案級分析 |
| 答案滿意度 | 72/100 | 90/100 | 工具覆蓋、修復建議可信、trace 可追溯、報告模板 |
| 支援類型 benchmark 命中率 | 20/20 | 95/100 | 100 份公開樣本與固定 eval gate |
| 單一 500 行合約分析時間 | ≤120 秒 | ≤120 秒 | 新增工具後仍保留 timeout 與 fallback |

## Boundaries

本階段負責：安全分數、benchmark harness、Slither/Mythril 類型覆蓋、Forge/Hardhat 專案級分析、GitHub/CI 回饋、前端報告可用性。

本階段不負責：替代人工審計、保證合約無漏洞、鏈上部署、私鑰管理、交易簽名、資金操作。

AI 責任邊界：Slither/Mythril/規則引擎產生漏洞事實；LLM 只負責解釋、修復建議與報告文字；安全分數必須由可重現公式計算。

## Architecture Decisions

1. 安全分數放在 `src/smart_contract_audit/scoring/`，輸入只接受 normalized findings、confidence、report review status、finding review status 與 benchmark 權重，輸出固定 0–100。
2. benchmark 放在 `eval/public_benchmark/`，保存 manifest、預期 labels、分析結果與回歸門檻；公開樣本不混入 RAG 訓練語料。
3. 工具擴充先走 adapter 層，Slither、Mythril 與 Echidna 都轉成同一個 `Finding` schema，避免前端與報告格式分裂。
4. CI gate 只阻擋新增高危 finding 或 benchmark 命中率下降，避免因既有歷史風險造成團隊無法合併修復 PR。

## Phase 1：信任層

Task 01：建立 100 份公開 benchmark。

Acceptance criteria：`eval/public_benchmark/manifest.json` 含 100 份公開樣本；每份有來源 URL、license/source、pragma、expected labels、是否在支援範圍內；`uv run python eval/run_public_benchmark.py` 輸出 category hit rate。

Verification：`uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95`。

Task 02：新增合約安全分數。

Acceptance criteria：JSON/Markdown report 增加 `security_score`、`score_factors`、`score_formula_version`；README 明確區分安全分數與報告品質 judge score。

Verification：`uv run pytest tests/test_security_score.py`、`uv run pytest`。

Task 03：前端顯示 benchmark 與分數解釋。

Acceptance criteria：前端報告首頁顯示安全分數、支援類型命中率、未支援類型提示；不得把 report-quality judge score 顯示成安全分數。

Verification：`cd frontend && npm run test && npm run build`。

## Phase 2：能力層

Task 04：補齊 Slither detector coverage。

Acceptance criteria：`DETECTOR_MAPPING` 覆蓋 benchmark 中所有支援類型 detector；未映射 detector 在 summary 中按 detector name 聚合。

Verification：`uv run pytest tests/test_detector_expansion.py`、benchmark supported hit rate ≥95/100。

Task 05：接入 Mythril/Echidna 作外部工具層。

Acceptance criteria：2026-05-04 已完成 v2，`--external-tool mythril --external-tool echidna` 會把外部工具摘要寫入 `external_tool_results`；Mythril issue 與 Echidna failed/falsified property 會轉成正式 `Finding`、寫入 SQLite trace，並與 Slither 同類型同檔案重疊行號 finding 去重。

Verification：`uv run pytest tests/test_external_tools.py tests/test_analyzer.py`。

Task 06：支援 Forge/Hardhat 真實 build。

Acceptance criteria：2026-05-04 已完成 v3，偵測 `foundry.toml`、`hardhat.config.*` 後優先使用專案原生 build；成功時 Slither 使用專案框架，失敗或工具缺失時保留 solc fallback 並把原因寫入 `analysis_metadata.errors`。`eval/run_public_project_builds.py` 會 clone pinned repo、初始化 submodules、安裝 npm dependencies、處理 Hardhat 自訂 artifacts/cache 路徑；10 repo pinned manifest 實測 `10/10` analyzer 與 `10/10` native build。

Verification：`uv run pytest tests/test_project_input.py tests/test_slither.py tests/test_public_project_builds.py` 已通過；`uv run python eval/run_public_project_builds.py --min-analyzer-success-rate 1.0 --min-native-build-success-rate 1.0` 已通過。

## Phase 3：工作流層

Task 07：GitHub Actions 掃描入口、report comparison 與 CI fail gate。

Acceptance criteria：2026-05-04 已完成手動掃描入口 `.github/workflows/smart-contract-audit.yml` 與 `scsa compare-reports`；提供 baseline report 時會輸出新增 finding、修復 finding、安全分數差異，高危新增 finding 或分數下降超門檻會使 CI fail。

Verification：`uv run pytest tests/test_report_compare.py`；`.github/workflows/smart-contract-audit.yml` 可產生 `scsa-reports` artifact 與 `comparison.md`。

Task 08：誤報/漏報 review 回寫。

Acceptance criteria：前端可把 finding 標記為 true_positive、false_positive、accepted_risk、fixed；狀態寫入 JSON report 與 SQLite trace。

Verification：`uv run pytest tests/test_http_api.py`、`cd frontend && npm run test`。

Task 09：歷史比較與審計報告模板。

Acceptance criteria：同一專案兩次分析可輸出 diff；Markdown/PDF 模板包含摘要、分數、finding、修復狀態、trace id、工具版本。

Verification：`uv run scsa compare-reports <old-report.json> <new-report.json> --output reports/comparison.md`；Markdown/JSON report schema validation 通過。

## Skill Mapping

| 開發項目 | 對應 skill | 使用時機 |
|---|---|---|
| 建構書與任務拆分 | `planning-and-task-breakdown`、`write-docs` | 每次新增/調整 roadmap |
| 智能合約漏洞規則 | `solidity-security`、`security-and-hardening` | detector 映射、Mythril、修復建議、安全邊界 |
| 評估與 benchmark | `llm-evaluation`、`source-driven-development` | 100 份公開樣本、命中率、滿意度評測 |
| CI 與 PR 自動化 | `ci-cd-and-automation`、`github-actions-templates`、`github` | GitHub Actions、PR comment、fail gate |
| 前端工作台 | `frontend-ui-engineering`、`frontend-design`、`e2e` | 安全分數、diff、review 回寫、報告體驗 |
| API 與 schema | `api-and-interface-design`、`test-driven-development` | report schema、score API、compare command |
| 除錯與驗證 | `debugging-and-error-recovery`、`code-review-and-quality` | benchmark 失敗、工具鏈錯誤、回歸審查 |

## Development Order

1. 先做 Task 01–02，建立可量化信任基準；完成後更新 README、docs/handoff.md、docs/review_checklist.md。
2. 再做 Task 04–06，補工具能力；每新增一類 detector 必須補 fixture 與 benchmark 樣本。
3. 最後做 Task 07–09，接日常工作流；每個工作流功能都要有本地命令與 CI 驗證。

## Checkpoints

Checkpoint A：Task 01–03 完成後，`uv run pytest`、`uv run ruff check .`、`uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30`、`cd frontend && npm run test && npm run build` 全通過。

Checkpoint B：Task 04–06 完成後，10 個公開專案中 9 個分析成功，支援類型 benchmark 命中率 ≥95/100，單案 500 行分析時間 ≤120 秒。

Checkpoint C：Task 07–09 完成後，測試 PR 可看到安全分數差異、finding diff、CI gate 結果與可交付 Markdown/PDF 報告。

## Risks

| 風險 | 影響 | 控制方式 |
|---|---|---|
| 安全分數被誤認為審計保證 | 高 | 報告固定顯示公式版本、支援範圍、人工審計聲明 |
| Mythril 使分析時間超過 120 秒 | 中 | 工具 timeout、快慢模式、部分結果標記 partial |
| 公開 benchmark 與真實專案分布不一致 | 中 | 樣本分層：token、DeFi、proxy、NFT、simple contract |
| CI gate 阻塞正常開發 | 中 | 只阻擋新增高危或分數下降超過設定門檻 |

## References

- `eval/public_benchmark/hf-slither50-v2-manifest.json`
- `eval/public_benchmark/public-project-builds-10-manifest.json`
- `src/smart_contract_audit/config.py`
- `docs/design/001-project-architecture.md`
- `docs/design/002-frontend-architecture.md`
- Hugging Face：`mwritescode/slither-audited-smart-contracts`
