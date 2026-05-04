# Review Checklist

日期：2026-05-04。

本 checklist 對齊 `.claude/skills/review/checklist.md`，用於本專案安全閘門審查。

| Gate | Acceptance |
|---|---|
| Git baseline | repo 在 `main`，可讀取 baseline diff |
| CI | `.github/workflows/ci.yml` 執行 ruff、pytest、RAG eval、judge eval |
| Project input | Foundry、Hardhat、nested imports 三個 fixture 均可 Slither 分析 |
| Corpus | Web50 `unknown_rate < 0.4` 且 `eligible_chunks >= 400` |
| Detector mapping | oracle、price manipulation、privilege escalation、upgrade risk 各 2 個測試合約 |
| Security score | JSON/Markdown 含 `security_score`、`score_formula_version`、`score_factors` |
| External tools | `--external-tool mythril` 與 `--external-tool echidna` 可寫入 `external_tool_results`，工具未安裝時狀態為 `skipped` |
| Report comparison | `scsa compare-reports` 可輸出新增、修復、持續存在 findings 與 score delta |
| Public benchmark | `eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30` 通過 |
| Report | JSON/Markdown 含 vulnerable code、AI remediation code、trace id、dataset version、model version、review status、security score、報告品質 judge score、token usage |
| Judge | `eval/run_judge.py` 同時輸出 local 與 external 報告品質分數 |
| GitHub Actions | `.github/workflows/smart-contract-audit.yml` 可手動產生 `scsa-reports` artifact 與 `comparison.md` |
