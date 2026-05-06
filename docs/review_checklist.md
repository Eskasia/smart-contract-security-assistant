# Review Checklist

日期：2026-05-07。

本 checklist 用於本專案安全閘門審查。

| Gate | Acceptance |
|---|---|
| Git baseline | repo 在 `main`，可讀取 baseline diff |
| CI | `.github/workflows/ci.yml` 執行 ruff、pytest、RAG eval、judge eval |
| Project input | Foundry、Hardhat、nested imports 三個 fixture 均可 Slither 分析；Foundry/Hardhat native build preflight 與 Hardhat 自訂 artifacts/cache path 有單元測試覆蓋 |
| API boundary | Token auth、`input_root`、body limit 與 non-wildcard CORS 測試通過 |
| Native build safety | Untrusted API mode 使用 `--native-build-policy disabled`；trusted CLI mode 保留 native build support |
| 0G proof package | `scsa 0g-package` 產生 stable `audit-proof.json`，含 report hash、score、finding count、trace id；contract id 不能逃出 output directory |
| 0G Storage dry-run | `integrations/0g` 可用 `npm run upload -- <audit-proof.json> --dry-run` 產生 `submission-proof.json` 並通過 `npm run verify-proof` |
| 0G Chain registry | `AuditProofRegistry` owner-only；`register-proof.mjs` 嚴格驗證 report hash、storage root、registry address、score bps 與 explorer link key |
| Hackathon submission | `README.hackathon.md`、demo script、X post copy、pending live proof fields 與 reproduction steps 完整 |
| Public project build validation | local manifest summary、native build threshold、commit ref checkout、10 repo manifest pinning、preflight missing tools、dependency install fallback 有單元測試覆蓋；10 pinned public repos 達 `10/10` analyzer 與 `10/10` native build |
| RAG corpus | `eval/run_eval.py` 的 `recall_at_k` 維持 `1.0` |
| Detector mapping | oracle、price manipulation、privilege escalation、upgrade risk 各 2 個測試合約 |
| Security score | JSON/Markdown 含 `security_score`、`score_formula_version`、`score_factors`，`security_score_v2` 支援 finding review multiplier |
| External tools | `--external-tool mythril` 可轉正式 finding 與 trace row；`--external-tool echidna` 可寫入 `external_tool_results`，工具未安裝時狀態為 `skipped` |
| Report comparison | `scsa compare-reports` 可輸出新增、修復、持續存在 findings 與 score delta |
| Public benchmark | `eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5` 通過 |
| Benchmark metrics | Public benchmark summary 含 confusion matrix、precision、recall 與 F1 |
| Report | JSON/Markdown 含 vulnerable code、AI remediation code、trace id、dataset version、model version、report/finding review status、finding review note、security score、報告品質 judge score、token usage |
| Judge | `eval/run_judge.py` 同時輸出 local 與 external 報告品質分數 |
| GitHub Actions | `.github/workflows/smart-contract-audit.yml` 可手動產生 `scsa-reports` artifact 與 `comparison.md` |
