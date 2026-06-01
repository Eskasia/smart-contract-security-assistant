---
title: "0G Hackathon Issue Remediation Tracker"
description: "Tracks each issue from /Users/william/0g-apac-hackathon-issues.md and its remediation status."
category: "hackathon"
number: "008"
status: draft
services: ["README.md", "docs/archive/hackathon", "config", "integrations/0g", "submission"]
related: ["hackathon/001", "hackathon/003", "hackathon/004", "hackathon/006", "hackathon/007"]
last_modified: "2026-05-07"
---

# 008 — 0G Hackathon Issue Remediation Tracker

## Status

draft；可由 repo 修改完成的敘事、配置、表單草稿、提交包一致性、公開 frontend demo、public demo video URL 與 GitHub public visibility 已納入本輪修正；live 0G proof 與 X post 仍需外部操作。

## Summary

本文件以 `/Users/william/0g-apac-hackathon-issues.md` 為依據，避免把外部未完成事項用假值補齊。提交前必須把 P0 欄位更新為真實 live 資料。

## Remediation Matrix

| ID | Issue | Status | Evidence |
|---|---|---|---|
| 01 | live 0G proof 尚未執行 | blocked by funded 0G key and live deploy | `docs/archive/hackathon/004-live-0g-proof-record.md` is single source of truth |
| 02 | HackQuest 表單空欄位 | blocked by live proof and X URL | `frontend_demo_url` and `demo_video_url` are filled; 0G proof and X post fields stay empty until true values exist |
| 03 | Demo video 尚未產出 | partially remediated | public MP4 URL returned `video/mp4` HTTP 200 on 2026-05-16; final live 0G scene still depends on live_registered proof |
| 04 | Demo script 允許 dry-run 畫面 | remediated | `docs/archive/hackathon/0g-demo-script.md` formal scenes use live proof only; dry-run moved to appendix |
| 05 | Public X post 尚未發布 | blocked by media/posting | `docs/archive/hackathon/005-public-x-post-template.md` includes demo URL and media checklist |
| 06 | README 語氣偏 pending | remediated without false completion claims | `README.md` keeps general project positioning; live proof blockers remain in `docs/archive/hackathon/004-live-0g-proof-record.md` |
| 07 | 文件狀態仍是 draft | blocked by P0 external items | Status stays draft until live proof/video/X/demo are real |
| 08 | dry-run 與 live proof 敘事混合 | remediated | Main submission path is live_registered; dry-run is reviewer reproduction only |
| 09 | 0G proof 欄位未同步 | remediated structurally | `docs/archive/hackathon/004-live-0g-proof-record.md` declared as single source of truth |
| 10 | frontend demo URL 未確定 | remediated | GitHub Pages URL `https://eskasia.github.io/smart-contract-security-assistant/` returned HTTP 200 on 2026-05-15 |
| 11 | Explorer base URL 不統一 | remediated | ChainScan defaults added for tx/address; StorageScan documented separately |
| 12 | Storage indexer RPC 範例空白 | remediated | `ZERO_G_STORAGE_INDEXER_RPC=https://indexer-storage-turbo.0g.ai` |
| 13 | config 只有 env name | remediated | `config/0g-hackathon.example.json` includes default endpoint references |
| 14 | README live env 全空 | remediated | Public endpoint defaults added; private key remains blank |
| 15 | `submission-proof.json` path 空白 | blocked by live proof output | proof record includes explicit path field and expected report path |
| 16 | 描述偏準備上鏈 | remediated with honest blocker | form/README wording now describes live flow and readiness blocker |
| 17 | 影片 proof 欄位順序不足 | remediated | demo script defines proof field and Explorer screen order |
| 18 | X 貼文缺 demo URL | remediated structurally | X template includes `<public demo or video URL>` placeholder |
| 19 | final checklist 未關閉 | blocked by P0 external items | submission index keeps pending states visible |
| 20 | repository public 證據不足 | remediated | GitHub CLI check on 2026-05-15 returned PUBLIC |

## External Blockers

- Funded 0G Mainnet deployer key.
- Live 0G Storage upload and 0G Chain registry transaction.
- Public X post URL with screenshot or clip.

## References

- `/Users/william/0g-apac-hackathon-issues.md`
- `README.md`
- `docs/archive/hackathon/004-live-0g-proof-record.md`
- `config/0g-hackathon.example.json`
- `integrations/0g/.env.example`
