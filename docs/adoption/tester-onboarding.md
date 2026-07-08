# Tester Onboarding

Status: current
Updated: 2026-07-09

This guide is for external testers who want to give SCSA feedback without
creating unsafe or unverifiable adoption evidence.

## Who should test

Good tester profiles:

- Solidity maintainers testing a repository they own or maintain.
- Security reviewers testing a repository they are explicitly authorized to
  review.
- Contributors running only the bundled repository fixtures.
- Tooling evaluators who can share command output without exposing private
  code, secrets, customer data, or proprietary audit material.

Do not test third-party contracts, customer repositories, private forks, copied
source bundles, or deployed contracts unless you have explicit authorization to
review and discuss that material.

## Authorization rule

Only run SCSA on one of these targets:

- A fixture already included in this repository.
- A repository you own.
- A repository you maintain.
- A repository where the owner gave you explicit permission to run security
  tooling and share feedback.

Unauthorized scanning is not useful feedback for this project. Do not submit
reports from code you are not allowed to review, quote, or summarize.

## Setup

Install dependencies:

```bash
uv sync --extra audit --dev
cd frontend && npm ci
```

Check the local environment:

```bash
uv run scsa --help
uv run scsa analyze --help
python --version
node --version
```

Optional validation before testing:

```bash
uv run ruff check .
uv run pytest
```

## Run a fixture test

Use this command when you only want to verify the default workflow without
bringing external code into scope:

```bash
uv run scsa analyze tests/contracts/VulnerableVault.sol \
  --out-dir reports-tester-fixture \
  --native-build-policy disabled
```

Expected high-level result:

- Overall status: `finding`
- Finding type: `reentrancy`
- Human review required: `true`
- Generated artifacts stay local under `reports-tester-fixture/`

You may share a short summary of this fixture result. Do not upload raw SQLite,
private paths, or unrelated local files.

## Run an authorized repo test

Use this only for a repository you own, maintain, or are explicitly authorized
to review.

```bash
uv run scsa analyze <authorized-local-repo-or-contract-path> \
  --out-dir reports-authorized-test \
  --native-build-policy disabled
```

Keep `--native-build-policy disabled` for pull requests, imported source,
downloaded archives, and any project where you have not reviewed scripts and
dependencies.

Trusted native build mode is allowed only for an explicitly trusted local
Foundry or Hardhat project:

```bash
uv run scsa analyze <trusted-local-foundry-or-hardhat-project> \
  --out-dir reports-authorized-trusted-test \
  --native-build-policy trusted
```

Do not use trusted native build mode on imported GitHub repositories, Etherscan
imports, downloaded archives, customer-provided code, or unreviewed pull request
content.

## Submit feedback

Open a tester feedback issue with:

- Your tester GitHub handle.
- Current GitHub issue as the feedback record plus public external evidence links (if any) or explicit permission to summarize privately shared feedback.
- The repository tested, authorization basis, command run, and report artifact
  summary.
- The install method you used.
- OS, Python, Node, and solc versions.
- The result: pass or fail.
- Confirmation that private code, secrets, addresses, and proprietary audit
  material were removed.
- A report artifact summary that does not include private code, private paths,
  customer data, secrets, addresses, or proprietary audit material.
- Usability feedback, including setup clarity, command clarity, report
  usefulness, false positives, false negatives, docs gaps, or installation
  blockers.
- Permission field for whether this feedback can count as testimonial evidence.
- Permission to quote: yes or no.

Use the GitHub issue template:

```text
.github/ISSUE_TEMPLATE/tester-feedback.yml
```

## What not to include

Do not include:

- Private keys, seed phrases, tokens, API keys, or wallet material.
- Proprietary contracts, customer code, private audit reports, or unpublished
  vulnerabilities.
- Raw customer identifiers, private repository URLs, or internal ticket links.
- Exploit instructions against live third-party systems.
- Mainnet transaction plans, funded wallet details, or instructions to attack a
  deployed contract.
- Full generated reports if they contain private paths or private source code.

Prefer short summaries, redacted snippets, and public fixture output.

## Feedback template

```text
- Tester GitHub:
- Repo tested:
- Authorization basis:
- Current GitHub issue as the feedback record:
- Public external evidence links (if available) or permission to summarize privately shared feedback:
- Command run:
- Install method:
- OS:
- Python version:
- Node version:
- solc version:
- Result: pass/fail
- Report artifact summary:
- Report usefulness 1-5:
- False positives:
- False negatives:
- Installation blockers:
- Can this feedback count as testimonial evidence: yes/no
- Private code/secrets/addresses/proprietary audit material removed: yes/no
- Permission to quote: yes/no
```

For testimonial text, include only words you are comfortable being quoted
publicly and only if you have permission to discuss the tested repository.
