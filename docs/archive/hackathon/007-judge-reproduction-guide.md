---
title: "Judge Reproduction Guide"
description: "Reviewer-facing setup, local demo, dry-run proof, and live 0G verification steps."
category: "hackathon"
number: "007"
status: draft
services: ["src/smart_contract_audit", "frontend", "integrations/0g", "tests"]
related: ["hackathon/001", "hackathon/003", "hackathon/004", "reference/001"]
last_modified: "2026-05-07"
---

# 007 — Judge Reproduction Guide

## Status

draft；本地重現流程已驗證，live 0G verification 需等 `docs/archive/hackathon/004-live-0g-proof-record.md` 填入主網資料後執行。

## Summary

本文件給評審快速重現產品流程。正式 0G 驗證以 `proof_mode=live_registered` 的 `submission-proof.json` 為準；dry-run 只證明本地 artifact 可重現。

## Prerequisites

| Tool | Expected |
|---|---|
| Python | `>=3.11` |
| uv | installed |
| Node.js | installed |
| Slither | installed through `uv sync --extra audit --dev` |
| solc | `0.8.34` verified locally |

## Local Product Flow

```bash
uv sync --extra audit --dev
uv run pytest tests/test_cli_zero_g.py tests/test_zero_g_proof_package.py -q
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --native-build-policy disabled
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` and analyze `tests/contracts/VulnerableVault.sol`.

## Local Proof Flow

```bash
mkdir -p reports
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --native-build-policy disabled > reports/latest-analysis.json
REPORT_ID=$(uv run python -c 'import json; print(json.load(open("reports/latest-analysis.json"))["contract_id"])')
uv run scsa 0g-package reports/latest-analysis.json --out-dir reports-0g --project-name "SCSA 0G Audit Proof" --track "Track 1: Agentic Infrastructure & OpenClaw Lab"
cd integrations/0g
npm install
npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json" --dry-run
npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"
cd ../..
uv run scsa 0g-attach-proof reports/latest-analysis.json "reports-0g/$REPORT_ID/submission-proof.json"
```

Expected dry-run fields:

```json
{
  "proof_mode": "dry_run",
  "storage_tx_hash": "dry-run-only",
  "registry_address": "pending-live-registry",
  "registry_tx_hash": "pending-live-registration",
  "explorer_links": {}
}
```

## Live 0G Verification

Use this only after `docs/archive/hackathon/004-live-0g-proof-record.md` has all live fields filled.

```bash
cd integrations/0g
export ZERO_G_CHAIN_EXPLORER_TX_BASE="https://chainscan.0g.ai/tx/"
export ZERO_G_CHAIN_EXPLORER_ADDRESS_BASE="https://chainscan.0g.ai/address/"
npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"
```

Expected live fields:

```json
{
  "proof_mode": "live_registered",
  "explorer_links": {
    "storage_tx": "",
    "registry": "",
    "registration_tx": ""
  }
}
```

## Reviewer Notes

- No test account is required for local analysis.
- No faucet is required for dry-run reproduction.
- A funded 0G key is required only for live deployment, upload, and registry registration.
- `.env` and private keys must not be committed.

## References

- `README.md`
- `docs/reference/001-validation-procedure-log.md`
- `integrations/0g/.env.example`
