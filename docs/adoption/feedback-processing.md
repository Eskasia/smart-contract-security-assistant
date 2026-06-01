# Feedback Processing

Status: current workflow
Updated: 2026-06-01

This workflow converts tester feedback into issues, pull requests, release
notes, and adoption metrics without treating unverified feedback as adoption.

## Intake

Record each feedback item from an authorized tester, public issue, or public
triage case with:

- Feedback source link
- Reporter identity or approved public placeholder
- Authorization basis for any tested repository
- SCSA version or commit
- Command or workflow tested
- Report artifact summary, with private data redacted
- Permission status for quotes, repo names, and public summaries

Reject or redact feedback that includes private keys, secrets, customer
identifiers, proprietary contract code, unpublished third-party findings, or
reports from repositories without explicit authorization.

## Classification

Classify each accepted item into one primary category:

- install blocker
- false positive
- false negative
- UX issue
- docs gap
- security boundary issue

Use secondary labels only when they change the owner or required verification.
Security boundary issues override other categories for priority and review.

## Response SLA

SLA means the target response time for maintainer triage, not a guaranteed fix
time.

| Category | First response | Target next action |
|---|---:|---|
| security boundary issue | 1 business day | Open issue or security advisory path before public detail expansion |
| install blocker | 2 business days | Reproduce locally or request missing environment details |
| false negative | 3 business days | Create a minimal fixture or document why it is out of scope |
| false positive | 3 business days | Compare analyzer output, mapping, and human-review boundary |
| UX issue | 5 business days | Convert to frontend/API/docs task when actionable |
| docs gap | 5 business days | Patch docs or link an existing canonical doc |

## PR creation rule

Create a pull request when feedback produces a concrete code, test, benchmark,
or documentation change. Each PR should keep one primary feedback category,
link the source issue or authorized case, and include verification commands.

For false positives and false negatives, add or update a fixture, benchmark
case, or regression test before claiming the behavior changed. For security
boundary feedback, confirm the authorized-use and local-first impact in the PR
summary.

## Release note rule

Add release notes when a feedback-driven change affects installation,
reporting behavior, finding classification, API safety, source import, native
build policy, benchmark gates, or public documentation commitments.

Do not list private tester names, private repository names, proprietary code, or
unpublished findings in release notes unless the reporter has explicitly
approved public attribution.

## Metrics update rule

Update [`docs/adoption/metrics.md`](metrics.md) only after the feedback has a
source link and permission status. Count a feedback issue only when it is part
of the current adoption phase and has a public issue, public discussion, or
approved public placeholder entry.

Testimonials require an explicit permission-to-quote link and belong in
[`docs/adoption/testimonials.md`](testimonials.md). Public triage cases require
authorization and belong in
[`docs/adoption/public-triage-cases.md`](public-triage-cases.md).
