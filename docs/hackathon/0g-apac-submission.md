# 0G APAC Hackathon Submission Draft

## Basic Project Information

Project name: SCSA 0G Audit Proof

One-sentence description: AI-assisted Solidity audit reports with verifiable 0G Storage persistence and 0G Chain proof.

Short summary:
SCSA 0G Audit Proof analyzes Solidity contracts with Slither, RAG, deterministic scoring, and traceable report generation. It solves the reviewer trust problem by packaging each audit result into a hash-stable proof artifact, uploading it to 0G Storage, and registering the report hash plus storage root on 0G Chain. Judges can inspect the product flow locally and verify on-chain activity through the 0G Explorer links.

Track: Track 1 - Agentic Infrastructure & OpenClaw Lab

0G components:
- 0G Storage: stores the audit proof package and report artifacts.
- 0G Chain: stores immutable proof events for report hash, storage root, score, and timestamp.

## Required 0G Proof Fields

Registry contract address:

Registry explorer link:

Storage root hash:

Storage upload transaction:

Storage explorer link:

Proof registration transaction:

Proof registration explorer link:

## Public X Post

SCSA 0G Audit Proof turns Solidity security scans into verifiable audit artifacts stored on 0G Storage and registered on 0G Chain.

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
