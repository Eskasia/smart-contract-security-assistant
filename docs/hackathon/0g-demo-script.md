---
title: "0G Demo Script"
description: "3-minute demo run-of-show for frontend audit flow, proof package, 0G Storage, and 0G Chain."
category: "hackathon"
number: "002"
status: draft
services: ["frontend", "integrations/0g", "src/smart_contract_audit"]
related: ["hackathon/001", "hackathon/004", "hackathon/006", "hackathon/007"]
last_modified: "2026-05-07"
---

# 002 — 0G APAC Hackathon Demo Script

## Status

draft；正式提交影片只使用 live 0G upload/register 畫面，dry-run 只保留在附錄供本地重現。

## Summary

本腳本控制在 2 分 45 秒，符合「demo video no more than 3 minutes」。正式提交影片必須展示 `proof_mode=live_registered`、公開 Explorer links 與前端 0G Proof panel。

Target duration: 2 minutes 45 seconds.

## Scene 1 - Problem and product, 20 seconds

Show the browser at `http://127.0.0.1:5173`.
Say: "Smart contract auditors need fast triage, but generated reports are hard to trust unless the artifact and score can be verified."

## Scene 2 - Run an audit, 50 seconds

Terminal A:

```bash
uv run scsa api --host 127.0.0.1 --port 8787 --out-dir reports-api --input-root "$PWD" --api-token dev-token --cors-origin http://127.0.0.1:5173 --max-request-bytes 1048576 --native-build-policy disabled
```

Terminal B:

```bash
cd frontend && npm run dev
```

Use the frontend to analyze `tests/contracts/VulnerableVault.sol`.
Point out the finding list, security score, vulnerable code, remediation diff, and trace evidence.

## Scene 3 - Create 0G proof package, 35 seconds

Show:

```bash
mkdir -p reports
uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --native-build-policy disabled > reports/latest-analysis.json
REPORT_ID=$(uv run python -c 'import json; print(json.load(open("reports/latest-analysis.json"))["contract_id"])')
uv run scsa 0g-package reports/latest-analysis.json --out-dir reports-0g --project-name "SCSA 0G Audit Proof" --track "Track 1: Agentic Infrastructure & OpenClaw Lab"
```

Open the generated `audit-proof.json` and show `report.sha256`, `report.security_score`, and `report.findings_count`.

## Scene 4 - Live 0G proof, 45 seconds

Show commands in this order:

```bash
cd integrations/0g
npm install
export ZERO_G_RPC_URL=https://evmrpc.0g.ai
export ZERO_G_PRIVATE_KEY="<redacted funded key>"
export ZERO_G_STORAGE_INDEXER_RPC=https://indexer-storage-turbo.0g.ai
npm run deploy
export ZERO_G_REGISTRY_ADDRESS="<paste registry_address from deploy output>"
npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json"
npm run register -- "../../reports-0g/$REPORT_ID/submission-proof.json"
cd ../..
uv run scsa 0g-attach-proof reports/latest-analysis.json "reports-0g/$REPORT_ID/submission-proof.json"
```

Proof field screen order:

1. `storage_tx_hash`
2. `storage_root_hash`
3. `registry_address`
4. `registry_tx_hash`
5. `proof_mode: live_registered`

## Scene 5 - Verification close, 15 seconds

Return to the frontend and show the 0G Proof panel with storage root, registry address, and Explorer links.

Explorer screen order:

1. Storage tx Explorer link
2. Registry contract Explorer link
3. Registration tx Explorer link

Say: "The audit report is reproducible locally and verifiable on 0G."

## Appendix - Local Dry-Run Only

Dry-run is not part of the formal submission video.

```bash
cd integrations/0g
npm install
npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json" --dry-run
npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"
```

Expected dry-run fields: `proof_mode=dry_run`, `storage_tx_hash=dry-run-only`, `registry_address=pending-live-registry`, and empty `explorer_links`.
