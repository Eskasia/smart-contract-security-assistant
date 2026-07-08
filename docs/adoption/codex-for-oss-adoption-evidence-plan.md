# Codex for OSS Adoption Evidence Plan

Status: active collection plan
Updated: 2026-07-09

This plan defines the 2-4 week evidence collection phase before submitting the
Codex for OSS application. It is an execution checklist, not an adoption claim:
planned outreach, local fixtures, private messages, and incomplete feedback do
not count as adoption evidence.

## Current baseline

| Signal | Current | Target before application | Counting rule |
|---|---:|---:|---|
| GitHub stars | 1 | 100 | GitHub repo API snapshot |
| GitHub forks | 0 | 30 | GitHub repo API snapshot |
| External tester feedback issues | 0 | 10 | Completed public feedback issue |
| Authorized public triage cases | 0 | 3 | Public authorization link and sanitized case log entry |
| Permissioned testimonials | 0 | 1 | Explicit permission to quote |
| External OSS adoption links | 0 | 2 | Public external repository usage link |
| Monthly downloads | 0 | 1000 | Package or release download counter |

## Weekly plan

| Week | Goal | Required output |
|---|---|---|
| 1 | Contact 15-20 Solidity OSS maintainers, audit learners, or Web3 developers | Outreach log outside the public repo; no metrics update unless feedback is completed |
| 2 | Convert completed runs into public evidence | Public feedback issues and first authorized public triage case entries |
| 3 | Seek external repository adoption links | Public PR, workflow, README, issue, or maintainer comment showing SCSA usage |
| 4 | Prepare final application evidence package | Evidence consistency audit, metrics update, application text review |

## Weekly adoption operating loop

Cadence: every Wednesday while the Codex for OSS application package is active.

1. Refresh source-backed metrics in [`docs/adoption/metrics.md`](metrics.md).
2. Review open tester/outreach issues for completed feedback links.
3. Move only authorized public results into [`public-triage-cases.md`](public-triage-cases.md), [`testimonials.md`](testimonials.md), or [`external-adoptions.md`](external-adoptions.md).
4. Leave counts unchanged when evidence is private, pending, unauthorised, or only repository-owned.
5. Record the next outreach target list separately from evidence counts.

Success threshold for the next four weeks:

| Signal | Minimum target | Counting rule |
|---|---:|---|
| Completed tester feedback issue | 3 | Public GitHub issue or explicit permission to summarize |
| Authorized public triage case | 1 | Public repo link plus maintainer authorization |
| Quote-approved testimonial | 1 | Explicit permission to quote |
| External OSS adoption | 1 | Public repo workflow, issue, PR, or docs link showing SCSA use |

## Daily maintenance

Do this daily during the collection phase:

1. Check new GitHub issues, pull requests, tester replies, and security reports.
2. Triage only completed, source-backed feedback into public evidence docs.
3. Do not open a maintenance PR when there are no new source-backed facts.

## Weekly maintenance PR

Open at most one weekly evidence PR. Include only source-backed changes:

- `docs/adoption/metrics.md`
- `docs/adoption/codex-for-oss-evidence.md`
- `docs/adoption/public-triage-cases.md`
- `docs/adoption/external-adoptions.md`
- `docs/adoption/testimonials.md`
- `docs/adoption/codex-for-oss-application.md`

The PR body must list the public source links. Do not describe the project as
widely adopted, production deployed, or audit-certified unless those claims are
publicly sourced.

## Evidence intake rules

- Tester feedback counts only after a completed public issue records tester
  handle, repository tested, authorization basis, command run, install method,
  OS/Python/Node/solc versions, pass/fail result, report artifact summary,
  usability feedback, quote permission, and no secrets/private code/customer
  data.
- Public triage cases count only with a public authorization link, allowed
  target, sensitive-material handling, sanitized report summary, and explicit
  human-review boundary.
- External OSS adoption counts only when an external public repository links to
  SCSA usage, such as a workflow, README entry, issue, PR, or maintainer comment.
- Testimonials count only when permission to quote is explicit.
- Local fixtures, planned outreach, private DMs, stars, forks, package
  publication, and incomplete tester runs do not count as external adoption.

## Application narrative

Use this positioning until stronger adoption evidence exists:

```text
SCSA is an early tool for a security-critical OSS workflow. It has reproducible
CI, a human-review boundary, an authorized-use policy, public package/release
evidence, and structured adoption logs. External adoption evidence is being
collected and is not claimed until public sources are logged.
```

Avoid claims of broad adoption, production adoption, audit certification,
download traction, or third-party audit outcomes unless the evidence tracker
links to public sources.

## Validation

Run these checks before merging any weekly evidence PR:

```bash
uv run ruff check .
uv run pytest
uv run python scripts/sync_report_schema.py --check
uv run python scripts/check_application_text.py
git diff --check
```
