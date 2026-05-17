---
title: "Demo Video Production Checklist"
description: "Recording checklist for the required 3-minute product demo and 0G proof walkthrough."
category: "hackathon"
number: "006"
status: draft
services: ["frontend", "integrations/0g", "docs/hackathon"]
related: ["hackathon/001", "hackathon/002", "hackathon/003", "hackathon/005", "hackathon/007"]
last_modified: "2026-05-07"
---

# 006 — Demo Video Production Checklist

## Status

draft；public demo video URL 已公開，正式影片必須在 live 0G upload/register 後補錄 Scene 4 到 Scene 5。

## Summary

影片長度上限是 3 分鐘。內容必須展示產品核心功能、使用者流程，以及 0G component 實際使用方式。

## Recording Setup

| Item | Value |
|---|---|
| Target duration | 2 minutes 45 seconds |
| Browser URL | public frontend demo URL; local fallback is `http://127.0.0.1:5173` |
| API URL | `http://127.0.0.1:8787` |
| Demo input | `tests/contracts/VulnerableVault.sol` |
| Output video link | https://eskasia.github.io/smart-contract-security-assistant/scsa-usage-tutorial.mp4?v=7aa1ab4 |
| Public frontend demo link | https://eskasia.github.io/smart-contract-security-assistant/ |

## Scene Checklist

| Scene | Time | Must show |
|---|---:|---|
| Product problem | 20s | Browser app and one-sentence value proposition |
| Audit run | 50s | Finding list, score, vulnerable code, remediation diff, trace evidence |
| Proof package | 35s | `audit-proof.json`, `report.sha256`, `report.security_score`, `report.findings_count` |
| 0G usage | 45s | Live upload/register commands and `submission-proof.json` with `proof_mode=live_registered` |
| Verification close | 15s | Frontend 0G Proof panel and public Explorer links |

## Rejection Risks

- Slide-only or concept-only video.
- Video exceeds 3 minutes.
- 0G usage shown only as dry-run.
- Explorer links are not visible or not publicly accessible.

## References

- `docs/hackathon/0g-demo-script.md`
- `docs/hackathon/004-live-0g-proof-record.md`
