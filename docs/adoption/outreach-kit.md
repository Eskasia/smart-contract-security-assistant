# Outreach Kit

Status: current safe outreach templates
Updated: 2026-06-01

Use these templates to invite public feedback without overstating SCSA's scope
or encouraging unauthorized scans. SCSA is automated triage evidence for human
review, not a full audit or deployment certification.

Core links:

- Tester onboarding: [`docs/adoption/tester-onboarding.md`](tester-onboarding.md)
- Maintainer workflow: [`docs/maintainer-workflow.md`](../maintainer-workflow.md)
- PR triage workflow template: [`docs/templates/scsa-pr-triage.yml`](../templates/scsa-pr-triage.yml)
- Feedback processing: [`docs/adoption/feedback-processing.md`](feedback-processing.md)
- Public feedback issue template: `.github/ISSUE_TEMPLATE/tester-feedback.yml`

## 1. Solidity OSS maintainer message

```text
Hi <name>, I maintain SCSA, a local-first Solidity security triage tool that
turns analyzer output into reviewable JSON, Markdown, and trace artifacts.

Authorized-use boundary: please only run it on a repository, pull request, or
contract that you own, maintain, or are explicitly authorized to review and
discuss publicly. Keep --native-build-policy disabled for untrusted PR input.

This is not a full audit or a safety certification. It is meant to help
maintainers collect first-pass evidence before human review.

Onboarding:
docs/adoption/tester-onboarding.md

Maintainer workflow:
docs/maintainer-workflow.md

If you try it, please open a public feedback issue with the command, target
authorization basis, result, and any blocker:
.github/ISSUE_TEMPLATE/tester-feedback.yml
```

## 2. Audit learner message

```text
Hi <name>, SCSA may be useful if you want to practice reading Solidity security
tool output with traceable reports and human-review notes.

Authorized-use boundary: run it only on the bundled fixtures, your own code, a
repository you maintain, or a target where you have explicit permission to run
security tooling and share feedback. Do not scan random third-party contracts.

This is not a full audit and should not be used to certify a contract as safe.
Use it as a learning workflow for analyzer evidence and review handoff.

Onboarding:
docs/adoption/tester-onboarding.md

Maintainer workflow:
docs/maintainer-workflow.md

After your run, please open a public feedback issue and note whether setup,
report readability, or false-positive handling was clear:
.github/ISSUE_TEMPLATE/tester-feedback.yml
```

## 3. Web3 Discord/Telegram short post

```text
I am looking for public feedback on SCSA, a local-first Solidity security
triage workflow that produces JSON/Markdown reports and trace artifacts.

Authorized-use boundary: only run it on code you own, maintain, or are
explicitly authorized to review and discuss. Do not submit private contracts,
secrets, customer data, or unauthorized third-party scan results.

It is not a full audit or deployment certification; every result requires human
review.

Onboarding:
docs/adoption/tester-onboarding.md

Maintainer workflow:
docs/maintainer-workflow.md

If you test it, please open a public feedback issue with the command, target
authorization basis, and result:
.github/ISSUE_TEMPLATE/tester-feedback.yml
```

## 4. GitHub issue invitation

```text
Thanks for maintaining <repo>. I am collecting public feedback for SCSA, a
local-first Solidity triage tool for reviewable analyzer evidence.

Authorized-use boundary: please only use SCSA on this repository if you own or
maintain it, or if the maintainer team explicitly authorizes the run and public
summary. Keep private code, secrets, customer data, and unpublished findings out
of public issues.

This is not a full audit and does not certify the repository as safe. It can
produce first-pass report artifacts for human review.

Onboarding:
docs/adoption/tester-onboarding.md

Maintainer workflow:
docs/maintainer-workflow.md

If you are open to trying it, please open a public feedback issue after the run:
.github/ISSUE_TEMPLATE/tester-feedback.yml
```

## 5. Follow-up after tester completes run

```text
Thanks for testing SCSA.

Authorized-use boundary check: before anything is quoted or linked publicly,
please confirm the tested target was a fixture, your own repository, a
repository you maintain, or a target you were explicitly authorized to review
and discuss.

This result is not a full audit or safety certification. I will treat it as
tester feedback and maintenance evidence only.

Please open or update a public feedback issue with:
- command run
- authorization basis
- SCSA version or commit
- result status
- install blockers, false positives, false negatives, UX issues, or docs gaps
- whether any short testimonial text may be quoted publicly

Onboarding:
docs/adoption/tester-onboarding.md

Maintainer workflow:
docs/maintainer-workflow.md

Feedback issue template:
.github/ISSUE_TEMPLATE/tester-feedback.yml
```
