# 0G APAC Hackathon Submission Draft

## Basic Project Information

Project name: SCSA 0G Audit Proof

One-sentence description: AI-assisted Solidity audit reports prepared for verifiable 0G Storage persistence and 0G Chain proof.

Short summary:
SCSA 0G Audit Proof analyzes Solidity contracts with Slither, RAG, deterministic scoring, and traceable report generation. It prepares each audit result as a hash-stable proof artifact for pending 0G Storage upload and pending 0G Chain registration. Judges can inspect the product flow locally now, then verify on-chain activity after live registry, storage, and transaction fields are filled.

Track: Track 1 - Agentic Infrastructure & OpenClaw Lab

0G components:
- 0G Storage: will store the audit proof package and report artifacts after live deployment.
- 0G Chain: will store immutable proof events for report hash, storage root, score, and timestamp after live deployment.

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

## Public X Post

SCSA 0G Audit Proof turns Solidity security scans into audit artifacts prepared for pending verifiable 0G Storage and 0G Chain registration.

Demo:

#0GHackathon #BuildOn0G
@0G_labs @0g_CN @0g_Eco @HackQuest_

## Final Submission Checklist

- [ ] GitHub repository is public.
- [ ] `README.hackathon.md` explains architecture, 0G modules, and local reproduction.
- [ ] 0G mainnet registry contract address is filled in.
- [ ] 0G Explorer links open without authentication.
- [ ] Demo video is 3 minutes or less and shows product flow plus 0G proof.
- [ ] X post link is submitted through HackQuest.
