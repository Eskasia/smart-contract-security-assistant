---
title: "HackQuest 成果提交說明書"
description: "繁體中文整理 0G APAC Hackathon 的 HackQuest 成果提交材料與本專案交付對應。"
category: "hackathon"
number: "009"
status: draft
services: ["docs/hackathon", "submission/0g-apac-hackathon", "integrations/0g"]
related: ["hackathon/001", "hackathon/003", "hackathon/004", "hackathon/006", "hackathon/007"]
last_modified: "2026-05-07"
---

# 009 — HackQuest 成果提交說明書

## Status

draft；本說明書依 2026-05-07 查詢到的官方 HackQuest 0G APAC Hackathon 頁面整理。正式提交前仍需填入 live 0G proof 與 public X post URL；GitHub repo、frontend demo URL 與 public demo video URL 已公開。

## Summary

成果必須在 2026-05-16 23:59 UTC+8 前透過 HackQuest 平台提交；換算 UTC 為 2026-05-16 15:59。有效提交的核心是 live 0G integration proof，必須有 0G mainnet contract address、公開 Explorer link 與至少一項 0G core component 的實際整合證明。

## Terms

HackQuest——本次比賽指定提交平台，所有最終成果材料都要從 0G APAC Hackathon 頁面進入提交流程。

0G mainnet contract address——部署在 0G 主網上的合約地址，本專案預期填入 `AuditProofRegistry` 的部署地址。

Explorer link——能讓評審公開查看鏈上活動的 0G 區塊瀏覽器連結；本專案使用 ChainScan 驗證 registry address 與 registration transaction，使用 StorageScan 驗證 storage artifact。

0G core component——官方接受的 0G 模組，包含 0G Storage、0G Compute、0G Chain、Agent ID、privacy 或 secure execution 功能。

live_registered——本專案 `submission-proof.json` 的正式提交狀態，代表 audit proof 已完成 0G Storage upload 與 0G Chain register。

## Submit Flow

1. 進入 HackQuest 的 0G APAC Hackathon 頁面，登入帳號並確認已完成報名。
2. 在 HackQuest 提交流程填入 basic project information：project name、30 字內 one-sentence description、short summary、使用的 0G component。
3. 填入 GitHub repository link；repo 必須 public，或已明確分享給評審可審查。
4. 填入 0G integration proof：0G mainnet contract address、Explorer link、使用的 0G component、可驗證的鏈上活動。
5. 貼上 demo video URL；影片長度上限 3 分鐘，需展示產品核心功能、使用流程、0G component 實際如何被使用。
6. 確認 README 或文件包含 project overview、architecture、0G modules、local deployment 或 reproduction steps、reviewer notes。
7. 發布 public X post，貼文需含 project name、demo screenshot 或 short clip、`#0GHackathon`、`#BuildOn0G`、`@0G_labs`、`@0g_CN`、`@0g_Eco`、`@HackQuest_`，並把 X post URL 填回 HackQuest。

## Project File Mapping

| HackQuest 欄位 | 本專案來源檔案 | 目前狀態 |
|---|---|---|
| Basic project information | `docs/hackathon/0g-apac-submission.md` | draft ready |
| GitHub repository link | `docs/hackathon/0g-apac-submission.md` | ready；2026-05-15 GitHub CLI 顯示 PUBLIC |
| 0G mainnet proof | `docs/hackathon/004-live-0g-proof-record.md` | blocked；待 live deploy/register |
| Structured form values | `docs/hackathon/hackquest-submission.form.json` | blocked；live proof 與 X post 仍空 |
| Demo video | `docs/hackathon/006-demo-video-production-checklist.md` | partially ready；public MP4 URL 已公開，正式 live 0G proof 段落仍待補 |
| README / documentation | `README.md` + `docs/hackathon/007-judge-reproduction-guide.md` | ready except live fields |
| Public X post | `docs/hackathon/005-public-x-post-template.md` | blocked；待 screenshot/clip 與公開發布 |
| Judge reproduction | `docs/hackathon/007-judge-reproduction-guide.md` | local ready；live verification blocked |

## Finalizer Command

登入 X 並發布貼文後，使用有 0G mainnet gas 的錢包執行：

```bash
export ZERO_G_PRIVATE_KEY="<funded 0G mainnet private key>"
export PUBLIC_X_POST_URL="<published X post URL>"
python3 scripts/finalize_0g_hackathon_submission.py
```

此命令會執行 live 0G deploy/upload/register、驗證 `submission-proof.json`，並回填 HackQuest JSON 與 `submission/0g-apac-hackathon`。

## Final Checks

提交前必須全部成立：

1. `submission-proof.json.proof_mode` 等於 `live_registered`。
2. `docs/hackathon/004-live-0g-proof-record.md` 已填入 registry address、storage root、storage transaction、registration transaction 與公開 Explorer links。
3. `hackquest-submission.form.json` 的 `public_x_post_url` 與 `zero_g_integration_proof` 全部為真實公開資料。
4. GitHub repo 不再顯示 Private badge，或已提供評審可審查的權限。
5. Demo video 是公開 YouTube 或 Loom 連結，長度不超過 3 分鐘，畫面包含產品流程與 0G proof。
6. X post 是公開狀態，且包含指定 hashtag 與官方帳號 tag。
7. README 中的本地重現指令可在乾淨環境照步驟執行。

## Invalid Conditions

- 只提交 dry-run proof。
- 影片只有投影片或概念說明。
- GitHub repo 空白、placeholder、缺少比賽期間的有效開發紀錄。
- 缺少 0G mainnet contract address 或公開 Explorer link。
- X post 缺少指定 hashtag 或官方 tag。
- HackQuest 表單留空 demo video URL、public X post URL 或 0G proof 欄位。

## References

- HackQuest 0G APAC Hackathon: https://www.hackquest.io/hackathons/0G-APAC-Hackathon
- 0G Documentation: https://docs.0g.ai/
- ChainScan mainnet explorer: https://chainscan.0g.ai/
- StorageScan storage explorer: https://storagescan.0g.ai/
- python-0g mainnet storage indexer reference: https://pypi.org/project/python-0g/
