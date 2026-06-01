# 競品導向優化計畫

更新日期：2026-05-17。

## 競品定位

| 競品 | 主要優勢 | SCSA 對應策略 |
|---|---|---|
| Slither | Solidity/Vyper 靜態分析 detector 與 Python API 成熟 | 保持 Slither 作 deterministic finding 來源，SCSA 專注 report、trace、review workflow |
| Cyfrin Aderyn | Rust scanner、Foundry/Hardhat zero-config、SARIF/Markdown/JSON | 補 GitHub/ZIP 匯入與 benchmark page，降低首次使用摩擦 |
| Echidna | property-based fuzzing，可驗證 invariant/assertion | 把 Echidna/Foundry invariant workflow 暴露到 API 與前端，不只停留在 CLI |
| SmartBugs | 多工具 benchmark framework，研究可重現性強 | 用 public benchmark leaderboard 補可重現說服力 |
| SolidityScan / Eagle Audit / audit.new | SaaS 入口完整，支援 GitHub/Etherscan/ZIP 與報告分享 | 補遠端來源匯入，但保留 local-first 與 trace evidence 優勢 |

## 本輪優先補齊

1. 遠端與封裝來源匯入
   - 支援 GitHub archive URL、Etherscan-style explorer source-code API、ZIP source bundle。
   - 所有匯入先落到本機 staging path，再交給既有 analyzer。
   - 驗收：拒絕 unsafe URL scheme、zip-slip、超量檔案/bytes、非 Solidity 主體、非 allowlist redirect target 與 oversized remote response。

2. Echidna / Foundry invariant 工作流
   - HTTP API 與前端可選 `echidna` external tool。
   - 保留 `native_build_policy` server-side 上限，API request 不能把 disabled 升級為 trusted。
   - 驗收：API payload 會傳入 `external_tools` 與 timeout，report 顯示 external tool result。

3. 公開 benchmark leaderboard
   - `eval/run_public_benchmark.py` 可輸出 Markdown leaderboard。
   - 文件可直接發布命中率、precision、recall、F1、score gap、逐 label coverage。
   - 驗收：leaderboard 由 summary 產生，不手寫關鍵數字。

## 成功指標

| 指標 | 目標 |
|---|---:|
| 首次輸入方式 | local path + GitHub + Etherscan-style API + ZIP |
| Frontend live workflow tests | 至少 30 passed |
| Public benchmark | 可產出 Markdown leaderboard |
| External tool workflow | API/前端可啟用 Echidna |
| 安全邊界 | URL/redirect/ZIP/path/native build 有單元測試 |

## 非目標

- 不在本輪實作完整 SaaS 分享、登入、雲端儲存。
- 不把外部來源匯入預設為 trusted build；未信任專案仍建議使用 `native_build_policy=disabled`。
- 不聲稱 benchmark 等同人工審計或 formal verification。
