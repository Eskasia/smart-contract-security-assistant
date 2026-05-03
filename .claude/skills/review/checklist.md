# Review Checklist

日期：2026-04-30。

審查定位：CI 前置初篩、開發者自查、審計 triage；不承擔最終審計簽核。

## Required Gates

1. `uv run ruff check .`
2. `uv run pytest`
3. `uv run python eval/run_eval.py`
4. `uv run python eval/run_judge.py`

## Security Review Fields

| Field | Required Check |
|---|---|
| Git baseline | diff 必須可從 `main` 或工作樹讀取 |
| Solidity input | 單檔、Foundry、Hardhat、nested import fixture 必須通過 |
| RAG corpus | Web50 `unknown_rate < 0.4` 且 `eligible_chunks >= 400` |
| Detector scope | oracle、price manipulation、privilege escalation、upgrade risk 各至少 2 個合約 fixture |
| Report governance | report 必須含 vulnerable code、AI remediation code、`trace_id`、`dataset_version`、`model_version`、`review_status`、judge score、token usage |
| Judge output | local 與 external judge 分數必須同時輸出 |
