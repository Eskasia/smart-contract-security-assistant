---
title: "Live 0G Proof Record"
description: "Fill-in record for 0G mainnet registry, storage, transaction, and Explorer proof fields."
category: "hackathon"
number: "004"
status: draft
services: ["integrations/0g", "README.md", "docs/archive/hackathon"]
related: ["hackathon/001", "hackathon/002", "hackathon/003", "hackathon/007"]
last_modified: "2026-05-07"
---

# 004 — Live 0G Proof Record

## Status

draft；live 0G proof 尚未執行，以下欄位不得用假地址、dry-run sentinel 值或 localhost URL 填充。

## Summary

本文件是 HackQuest 「0G Integration Proof」的單一事實來源。完成 live upload/register 後，把相同欄位同步回 `docs/archive/hackathon/0g-apac-submission.md`、HackQuest 表單與 `submission/0g-apac-hackathon/`；只有公開 README 需要顯示 live proof links 時才同步 `README.md`。

## Live Proof Fields

| Field | Value |
|---|---|
| 0G network | 0G Mainnet |
| 0G chain RPC | `https://evmrpc.0g.ai` |
| 0G storage indexer | `https://indexer-storage-turbo.0g.ai` |
| Chain explorer | `https://chainscan.0g.ai/` |
| Storage explorer | `https://storagescan.0g.ai/` |
| Registry contract address |  |
| Registry explorer link |  |
| Storage root hash |  |
| Storage upload transaction |  |
| Storage explorer link |  |
| Proof registration transaction |  |
| Proof registration explorer link |  |
| `submission-proof.json` path |  |
| Demo report path |  |

## Live Commands

Preferred one-command finalization after X post is published and the 0G deployer wallet is funded:

```bash
export ZERO_G_PRIVATE_KEY="<funded 0G mainnet private key>"
export PUBLIC_X_POST_URL="<published X post URL>"
python3 scripts/finalize_0g_hackathon_submission.py
```

Manual command sequence:

```bash
cd integrations/0g
npm install
export ZERO_G_RPC_URL="https://evmrpc.0g.ai"
export ZERO_G_PRIVATE_KEY=""
export ZERO_G_STORAGE_INDEXER_RPC="https://indexer-storage-turbo.0g.ai"
export ZERO_G_CHAIN_EXPLORER_TX_BASE="https://chainscan.0g.ai/tx/"
export ZERO_G_CHAIN_EXPLORER_ADDRESS_BASE="https://chainscan.0g.ai/address/"
export ZERO_G_STORAGE_EXPLORER_BASE="https://storagescan.0g.ai/"
npm run deploy
export ZERO_G_REGISTRY_ADDRESS=""
npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json"
npm run register -- "../../reports-0g/$REPORT_ID/submission-proof.json"
npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"
cd ../..
uv run scsa 0g-attach-proof reports/latest-analysis.json "reports-0g/$REPORT_ID/submission-proof.json"
```

## Required JSON Shape

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

## Acceptance Check

```bash
cd integrations/0g
npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"
```

Expected result: `{"ok": true, ...}` and all three Explorer links open publicly.

## Sync Targets

After live registration, copy the same values to:

- `README.md` only when public proof links are added to the GitHub entry page
- `docs/archive/hackathon/0g-apac-submission.md`
- `docs/archive/hackathon/hackquest-submission.form.json`
- `docs/archive/hackathon/003-submission-package-index.md`
- `submission/0g-apac-hackathon/`

## References

- `integrations/0g/scripts/upload-storage.mjs`
- `integrations/0g/scripts/register-proof.mjs`
- `integrations/0g/scripts/verify-submission-proof.mjs`
