# Review Checklist

日期：2026-04-30。

本 checklist 對齊 `.claude/skills/review/checklist.md`，用於本專案安全閘門審查。

| Gate | Acceptance |
|---|---|
| Git baseline | repo 在 `main`，可讀取 baseline diff |
| CI | `.github/workflows/ci.yml` 執行 ruff、pytest、RAG eval、judge eval |
| Project input | Foundry、Hardhat、nested imports 三個 fixture 均可 Slither 分析 |
| Corpus | Web50 `unknown_rate < 0.4` 且 `eligible_chunks >= 400` |
| Detector mapping | oracle、price manipulation、privilege escalation、upgrade risk 各 2 個測試合約 |
| Report | JSON/Markdown 含 vulnerable code、AI remediation code、trace id、dataset version、model version、review status、judge score、token usage |
| Judge | `eval/run_judge.py` 同時輸出 local 與 external 分數 |
