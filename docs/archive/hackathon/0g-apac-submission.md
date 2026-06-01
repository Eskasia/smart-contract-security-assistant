---
title: "0G APAC Submission Draft"
description: "HackQuest form text, 0G proof fields, public X post copy, and final checklist."
category: "hackathon"
number: "001"
status: draft
services: ["README.md", "integrations/0g", "frontend"]
related: ["hackathon/002", "hackathon/003", "hackathon/004", "hackathon/005", "hackathon/006", "hackathon/007"]
last_modified: "2026-05-07"
---

# 001 — 0G APAC Hackathon Submission Draft

## Status

draft；HackQuest 表單文字已準備，live 0G mainnet contract address、Explorer links 與 X post link 尚待完成；GitHub repo、frontend demo URL 與 public demo video URL 已公開。

## Summary

本文件可直接複製到 HackQuest 提交表單。提交前必須先完成 live 0G upload/register，並讓 `submission-proof.json.proof_mode` 等於 `live_registered`。

## Basic Project Information

Project name: SCSA 0G Audit Proof

One-sentence description: AI-assisted Solidity audit reports with verifiable 0G Storage persistence and 0G Chain proof registration.

Short summary:
SCSA 0G Audit Proof analyzes Solidity contracts with Slither, RAG, deterministic scoring, and traceable report generation. The final live flow packages each audit result as a hash-stable proof artifact, uploads the artifact to 0G Storage, and registers the report hash, storage root, score, and contract id on 0G Chain.

Track: Track 1 - Agentic Infrastructure & OpenClaw Lab

Repository: https://github.com/Eskasia/smart-contract-security-assistant

Repository visibility: public as of the 2026-05-15 GitHub CLI check.

Frontend demo link: https://eskasia.github.io/smart-contract-security-assistant/

Demo video link: https://eskasia.github.io/smart-contract-security-assistant/scsa-usage-tutorial.mp4?v=7aa1ab4

0G components:
- 0G Storage: stores the audit proof package and report artifacts in the live submission flow.
- 0G Chain: stores immutable proof events for report hash, storage root, score, and timestamp in the live submission flow.
- Official chain explorer: https://chainscan.0g.ai/
- Official storage explorer: https://storagescan.0g.ai/

## Required 0G Proof Fields

Registry contract address:

Registry explorer link:

Storage root hash:

Storage upload transaction:

Storage explorer link:

Proof registration transaction:

Proof registration explorer link:

`submission-proof.json` shape:

```json
{
  "proof_mode": "live_registered",
  "storage_root_hash": "",
  "storage_tx_hash": "",
  "registry_address": "",
  "registry_tx_hash": "",
  "explorer_links": {
    "storage_tx": "",
    "registry": "",
    "registration_tx": ""
  }
}
```

Dry-run proof uses `proof_mode: "dry_run"` and an empty `explorer_links` object.
Dry-run proof is local reproduction only and must not be submitted as actual 0G integration proof.

## Public X Post

SCSA 0G Audit Proof turns Solidity security scans into audit artifacts with verifiable 0G Storage and 0G Chain registration.

Demo:

#0GHackathon #BuildOn0G
@0G_labs @0g_CN @0g_Eco @HackQuest_

Public X post link:

## Final Submission Checklist

- [x] GitHub repository is public.
- [ ] `README.md` explains the public project overview and `docs/archive/hackathon/007-judge-reproduction-guide.md` explains local reproduction.
- [ ] 0G mainnet registry contract address is filled in.
- [ ] 0G Explorer links open without authentication.
- [ ] Demo video is 3 minutes or less and shows product flow plus 0G proof.
- [ ] X post link is submitted through HackQuest.
