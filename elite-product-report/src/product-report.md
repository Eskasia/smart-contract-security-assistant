---
style: corporate-professional
accent-color: "#0078D4"
animations: minimal
---

# 智能合約安全分析助理
## 企業產品狀態報告

===

## Executive Summary

* MVP 已完成 CLI、Slither、RAG、MLX-ready、Trace 與 CI 驗收
* 測試結果：15 passed、RAG recall@k 1.0、Judge score 5.0
* 產品定位：正式審計前的工程化初篩
* 下一版重點：多檔專案支援、真實外部 Judge、公開審計報告 corpus

===

## Product Scope

* 目標用戶：Solidity 開發者、Web3 團隊、資安教學、履歷作品審查
* 核心任務：漏洞初篩、修復建議、報告輸出、finding 回放
* 當前邊界：單檔 Solidity 合約，500 行以內

===

## Architecture

* .sol input
* Slither detector
* FindingSchema adapter
* RAG retrieval
* MLX-ready generation
* JSON / Markdown / SQLite Trace

===

## Validation Metrics

| Metric | Result | Status |
|--------|--------|--------|
| pytest | 15 passed | Pass |
| ruff | All passed | Pass |
| RAG recall@k | 1.0 | Pass |
| Judge score | 5.0 | Pass |
| E2E | 2 passed | Pass |
| Max RSS | 54,231,040 bytes | Pass |

===

## Roadmap

* v0.8: CLI、Slither、RAG fixture、MLX-ready、Trace、CI
* v0.9: Foundry/Hardhat 支援、多檔 import resolution、外部 Judge API
* v1.0: 真實公開審計報告 corpus、Dense retrieval、報告審核 UI

===

# Questions
