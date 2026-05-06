# 0G APAC Hackathon Demo Script

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

## Scene 4 - Create local proof and show live path, 45 seconds

Local dry-run proof:

```bash
cd integrations/0g
npm install
npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json" --dry-run
npm run verify-proof -- "../../reports-0g/$REPORT_ID/submission-proof.json"
```

Live recording after funding the deployer key:

```bash
npm run deploy
export ZERO_G_REGISTRY_ADDRESS="0x..."
npm run upload -- "../../reports-0g/$REPORT_ID/audit-proof.json"
npm run register -- "../../reports-0g/$REPORT_ID/submission-proof.json"
cd ../..
uv run scsa 0g-attach-proof reports/latest-analysis.json "reports-0g/$REPORT_ID/submission-proof.json"
```

For dry-run recording, open `submission-proof.json` and show `proof_mode: dry_run`, `storage_root_hash`, `storage_tx_hash: dry-run-only`, `registry_address: pending-live-registry`, and empty `explorer_links`.
For live recording, open `submission-proof.json` after `npm run register` and show `proof_mode: live_registered`, `storage_root_hash`, `storage_tx_hash`, `registry_address`, `registry_tx_hash`, and `explorer_links.storage_tx`, `explorer_links.registry`, `explorer_links.registration_tx`.

## Scene 5 - Verification close, 15 seconds

For dry-run recording, return to the frontend and show the 0G Proof panel without Explorer links. Say: "The audit report is reproducible locally and prepared for 0G verification."
For live recording after upload/register, return to the frontend and show the 0G Proof panel with storage root, registry address, and Explorer links. Say: "The audit report is reproducible locally and verifiable on 0G."
