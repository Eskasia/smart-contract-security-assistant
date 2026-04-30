# AGENTS.md

此專案根目錄路徑含尾端空格：`/Users/william/智能合約安全分析助理 `。所有 shell 指令必須使用精確路徑或在已設定的 working directory 內執行。

## 專案狀態

截至 2026-04-30，核心 Python MVP 已可跑：Slither 串接、finding adapter、JSON schema validation、本地 RAG fallback、MLX-ready generator、SQLite trace、Markdown/JSON report、CLI、Gradio 可選入口、eval 腳本與 pytest 測試。

## 常用驗證

```bash
uv sync --extra audit --dev
uv run pytest
uv run ruff check .
uv run pytest tests/test_slither.py
uv run python eval/run_eval.py
uv run python eval/run_judge.py
/usr/bin/time -l uv run pytest tests/test_e2e.py
```

已驗證工具版本：Slither `0.11.5`，solc `0.8.34`。`pytest tests/test_e2e.py` 在 2026-04-30 的最大 resident set size 為 54,231,040 bytes。

## 主要程式邊界

- CLI：`src/smart_contract_audit/cli.py`
- 分析主流程：`src/smart_contract_audit/analyzer.py`
- Slither 串接：`src/smart_contract_audit/slither_runner.py`
- Finding 映射：`src/smart_contract_audit/finding_adapter.py`
- RAG：`src/smart_contract_audit/rag/`
- MLX 介面：`src/smart_contract_audit/llm/mlx_runtime.py`
- Trace：`src/smart_contract_audit/trace/`
- 驗證 schema：`src/smart_contract_audit/validation/`

## 簡報產物

最終 PPT：`elite-product-report/final-output/智能合約安全分析助理_產品報告.pptx`。來源在 `elite-product-report/src/product-report.md`、`elite-product-report/src/generate.mjs`、`elite-product-report/slides/`，修改簡報時先改來源再重新 render/export。

歷史簡報資料夾：`deck-smart-contract-security-assistant/`、`huashu-redesign/`、`huashu-product-report/`、`elite-product-report/`。

## 審查限制

此目錄截至 2026-04-30 沒有 `.git` repository 邊界，`gstack/review` 的 base branch diff、commit log、PR review 與 checklist 流程無法完整執行；可用本地命令驗證測試、lint、eval 與 PPTX package integrity。

## 文件規則

新增功能後同步更新 `README.md` 與 `docs/handoff.md`。避免相對時間，使用 `YYYY-MM-DD`。輸出給使用者時使用繁體中文並保持精簡。
