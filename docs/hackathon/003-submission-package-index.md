---
title: "0G Submission Package Index"
description: "Maps every 0G APAC Hackathon requirement to the local file that satisfies it."
category: "hackathon"
number: "003"
status: draft
services: ["README.md", "docs/hackathon", "integrations/0g"]
related: ["hackathon/001", "hackathon/002", "hackathon/004", "hackathon/005", "hackathon/006", "hackathon/007"]
last_modified: "2026-05-07"
---

# 003 — 0G Submission Package Index

## Status

draft；文件包已齊備，提交有效性仍取決於 live 0G mainnet contract address、Explorer links 與 public X post link。Public demo video URL 已公開，但正式影片的 live 0G proof 段落仍受 live 0G blocker 影響。

## Summary

本文件是 HackQuest 提交前的總索引。任何標記為 `pending` 的項目都不能留空提交。

## Required Materials

| Rule item | Required output | Local file | Status |
|---|---|---|---|
| Basic project information | Project name, one-sentence description, short summary, selected track | `docs/hackathon/0g-apac-submission.md` | ready |
| Code repository | Public GitHub repository link and visibility evidence | `docs/hackathon/0g-apac-submission.md` | ready; GitHub CLI check on 2026-05-15 returned PUBLIC |
| 0G integration proof | Mainnet registry address, Explorer links, storage root, tx hashes | `docs/hackathon/004-live-0g-proof-record.md` | blocked until live deployment |
| Demo video | Public video link, 3 minutes or less | `docs/hackathon/006-demo-video-production-checklist.md` | public URL ready; live 0G proof scene still blocked |
| README / documentation | Overview, architecture, 0G modules, reproduction steps, reviewer notes | `README.md` and `docs/hackathon/007-judge-reproduction-guide.md` | ready except live fields |
| Public X post | Post text with screenshot or demo clip, hashtags, tags | `docs/hackathon/005-public-x-post-template.md` | pending posting |
| Frontend demo URL | Public non-localhost product demo URL | `docs/hackathon/0g-apac-submission.md` and JSON form | ready; https://eskasia.github.io/smart-contract-security-assistant/ returned HTTP 200 |
| Bonus materials | API notes, validation notes, tutorial path | `docs/reference/001-validation-procedure-log.md` and `docs/hackathon/007-judge-reproduction-guide.md` | ready |

## Invalid Submission Conditions

- `docs/hackathon/004-live-0g-proof-record.md` still has blank live 0G fields.
- Demo video only shows slides or local dry-run proof.
- X post lacks `#0GHackathon`, `#BuildOn0G`, `@0G_labs`, `@0g_CN`, `@0g_Eco`, or `@HackQuest_`.
- Repository becomes private again or judges cannot access it.
- Frontend demo URL is empty, returns non-200, or points to localhost.

## Final Fill-In Fields

| Field | Source after live work |
|---|---|
| Registry contract address | `npm run deploy` output |
| Registry explorer link | `npm run deploy` output or ChainScan address page |
| Storage root hash | `submission-proof.json.storage_root_hash` |
| Storage tx | `submission-proof.json.storage_tx_hash` |
| Storage explorer link | `submission-proof.json.explorer_links.storage_tx` |
| Registration tx | `submission-proof.json.registry_tx_hash` |
| Registration explorer link | `submission-proof.json.explorer_links.registration_tx` |
| Frontend demo link | `https://eskasia.github.io/smart-contract-security-assistant/` |
| Demo video link | `https://eskasia.github.io/smart-contract-security-assistant/scsa-usage-tutorial.mp4?v=7aa1ab4` |
| X post link | Published X URL |

## Single Source Sync Rule

`docs/hackathon/004-live-0g-proof-record.md` is the source of truth for all 0G proof fields. After it is filled, copy values to HackQuest Markdown, HackQuest JSON, and this submission folder in one edit; update `README.md` only if the public overview needs live proof links.

## References

- `README.md`
- `docs/hackathon/0g-apac-submission.md`
- `docs/hackathon/0g-demo-script.md`
- `docs/reference/001-validation-procedure-log.md`
