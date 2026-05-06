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
uv run scsa 0g-package reports-api/vulnerablevault.json --out-dir reports-0g --project-name "SCSA 0G Audit Proof" --track "Track 1: Agentic Infrastructure & OpenClaw Lab"
```

Open the generated `audit-proof.json` and show `report_sha256`, `security_score`, and `findings_count`.

## Scene 4 - Upload and register on 0G, 45 seconds

Show:

```bash
cd integrations/0g
npm install
npm run deploy
export ZERO_G_REGISTRY_ADDRESS=""
npm run upload -- ../../reports-0g/vulnerablevault/audit-proof.json --dry-run
npm run verify-proof -- ../../reports-0g/vulnerablevault/submission-proof.json
```

For the live recording, replace the dry-run commands with:

```bash
npm run upload -- ../../reports-0g/vulnerablevault/audit-proof.json
npm run register -- ../../reports-0g/vulnerablevault/submission-proof.json
cd ../..
uv run scsa 0g-attach-proof reports-api/vulnerablevault.json reports-0g/vulnerablevault/submission-proof.json
```

Paste the registry address printed by `npm run deploy` into `ZERO_G_REGISTRY_ADDRESS` before running the live `npm run register`.

Open `submission-proof.json` and show `storage_root_hash`, `storage_tx_hash`, `registry_address`, `registry_tx_hash`, and `explorer_links.storage_tx`, `explorer_links.registry`, `explorer_links.registration_tx`.

## Scene 5 - Verification close, 15 seconds

Return to the frontend and show the 0G Proof panel with storage root, registry address, and Explorer links.
Say: "The audit report is reproducible locally and verifiable on 0G."
