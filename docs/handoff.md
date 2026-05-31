# 智能合約安全分析助理交接

更新日期：2026-05-31。

## 已完成內容

- Python package `smart_contract_audit` 已建立，入口命令為 `scsa`。
- 核心流程為 `.sol` 輸入 → Slither → finding normalization → JSON schema validation → RAG retrieval → LLM explanation fallback 或 MLX runtime → JSON/Markdown report → SQLite trace。
- 測試覆蓋 adapter、analyzer、RAG、Slither 串接、本地 import 解析、MLX 記憶體估算、MLX 模型自動探索、MLX probe fallback、skill graph artifact、schema validation、端到端流程。
- Eval 腳本已存在：`eval/run_eval.py` 測 RAG recall，`eval/run_judge.py` 測生成品質。
- CI 設定在 `.github/workflows/ci.yml`，目前執行 ruff、pytest、RAG eval 與 judge eval。
- OSS readiness 基礎文件已存在：`LICENSE`、`CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`.github/ISSUE_TEMPLATE/*`、`.github/pull_request_template.md`。
- README 已整理成外部讀者版本，包含 authorized-use boundary、quickstart、demo output、limitations 與 maintainer automation use cases。
- Release readiness 已開始：`CHANGELOG.md` 與 `docs/release/001-v0.1.0-checklist.md` 記錄 v0.1.0 scope、deferred issues、驗證命令與 GitHub release 步驟。
- Release 後外部使用證據收集文件已建立：`docs/community/001-v0.1.0-tester-feedback.md`。

## 技術核心

Slither——Solidity 靜態分析工具，負責 deterministic vulnerability finding；LLM 不負責判定漏洞，只負責把 finding 轉成可讀解釋、攻擊路徑與修復建議。

RAG——Retrieval-Augmented Generation，先從審計語料與技術文件 chunk 檢索證據，再把證據放入 prompt，降低生成內容脫離資料來源的風險。

MLX——Apple Silicon 本地推理 runtime，本專案以 4-bit 權重量化估算記憶體需求，`8B` 參數模型在 4-bit 權重下約需 `4.0GB` 權重記憶體；`uv run scsa mlx-probe --auto-discover-model --output reports-mlx/mlx_probe.json` 會輸出模型路徑、量化位元、預估權重記憶體、fallback 原因、load_succeeded 與 peak_rss_bytes。

Trace——SQLite 分析追蹤表，保存 finding、raw Slither output、RAG chunks、prompt、LLM output 與 partial 狀態，用於除錯與報告回溯。

## 驗證結果

2026-04-30 本地驗證結果：

```text
uv run pytest                         15 passed
uv run ruff check .                   all checks passed
uv run python eval/run_eval.py        recall_at_k = 1.0
uv run python eval/run_judge.py       average_judge_score = 5.0
uv run scsa mlx-probe --auto-discover-model --max-tokens 4 --output reports-mlx/mlx_probe.json  load_succeeded = true, peak_rss_bytes = 661,520,384
uv run python scripts/build_skill_graph.py  graphify-out artifacts generated
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

- 目前只支援單一入口 Solidity 檔，入口檔最多 500 行；同目錄本地 import 已有測試覆蓋。
- Mythril、Foundry、Hardhat plugin、多檔 import resolution、oracle manipulation 分析尚未納入 v1.0。
- 真實外部高階模型 API judge 需另外設定 API key；目前 `eval/run_judge.py` 走 local-rule-judge。
- `gstack/review` 無法完整跑，因為專案目錄沒有 `.git` repository 邊界與 `.claude/skills/review/checklist.md`。

## 接手順序

1. 先跑 `uv sync --extra audit --dev` 與 `uv run pytest`。
2. 再跑 `uv run pytest tests/test_slither.py` 確認 Slither/solc 串接與本地 import 解析。
3. 最後跑 `uv run python eval/run_eval.py`、`uv run python eval/run_judge.py`、`/usr/bin/time -l uv run pytest tests/test_e2e.py`。

自主迭代架構：`docs/skill-graph.md` 記錄 skill graph、多 agent 分工、缺口排序、驗證命令與文件更新規則。
圖譜產物：`uv run python scripts/build_skill_graph.py` 產生 `graphify-out/graph.json`、`graphify-out/GRAPH_REPORT.md`、`graphify-out/graph.html`。

## 文件入口

- 文件索引：`docs/DOCS_INDEX.md`
- Changelog：`CHANGELOG.md`
- v0.1.0 release checklist：`docs/release/001-v0.1.0-checklist.md`
- v0.1.0 tester feedback guide：`docs/community/001-v0.1.0-tester-feedback.md`
- 使用說明書：`docs/guides/001-usage-manual.md`
- 專案架構書：`docs/design/001-project-architecture.md`
- 驗證程序日誌：`docs/reference/001-validation-procedure-log.md`
