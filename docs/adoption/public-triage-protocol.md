# Public Triage Protocol

Status: current
Updated: 2026-06-01

This protocol defines when SCSA triage results may be documented as public
adoption evidence. Public triage cases must be authorized, sanitized, and
reviewable.

## Required authorization

Every public triage case must include an authorization link. The link must point
to one of:

- A public GitHub issue or discussion where the maintainer asks for SCSA triage.
- A pull request comment from a repository maintainer authorizing the scan.
- A public security policy or contribution guide that explicitly permits this
  kind of automated security tooling.
- A maintainer feedback issue in this repository confirming permission to test
  and summarize the target.

Do not publish a case when authorization exists only in private chat, email,
direct message, or local memory. Private authorization can be used for private
testing, but it is not enough for a public evidence case.

## Allowed targets

Allowed public case targets:

- Repositories you own or maintain.
- Public repositories where a maintainer explicitly authorized SCSA triage.
- Pull requests where the contributor or maintainer asked for review and the
  repository policy permits automated analysis.
- Local fixtures in this repository when they are clearly labeled as fixtures,
  not external adoption.

For public adoption evidence, prefer maintainer-authorized public repositories
over generic fixture runs.

## Disallowed targets

Do not create public triage cases for:

- Deployed contracts without maintainer authorization.
- Third-party repositories that did not authorize the scan.
- Customer contracts, private repositories, private forks, or proprietary audit
  material.
- Downloaded source bundles whose owner did not authorize public discussion.
- Mainnet exploit reproduction, attack planning, funded-wallet testing, or live
  system exploitation.
- Vulnerability details that the maintainer has not approved for disclosure.

## Sensitive material handling

Before opening or updating a public case:

- Remove private keys, tokens, API keys, wallet addresses tied to private
  testing, and secret names.
- Remove customer names, internal issue links, private repository paths, and
  proprietary contract identifiers.
- Replace private local paths with repository-relative paths.
- Do not paste full generated reports if they include private code or local
  system paths.
- Do not publish exploit instructions for a live third-party system.

If disclosure risk is unclear, keep the case private and do not count it as
public adoption evidence.

## Report sanitization

Public artifacts may include:

- Repository-relative command.
- SCSA version or commit.
- Report status: `finding`, `no_finding`, `error`, or `blocked`.
- Finding count, finding type, severity, detector, and standards mapping.
- Human review outcome.
- Link to a maintainer-approved public issue, pull request, gist, or sanitized
  Markdown artifact.

Public artifacts must not include:

- Raw SQLite traces from private or customer scans.
- Private absolute paths.
- Private source code snippets unless the source is already public and
  disclosure is authorized.
- Secrets, credentials, customer identifiers, or exploit runbooks.
- Claims that SCSA certified the target as safe to deploy.

## Case format

Use this format in
[`docs/adoption/public-triage-cases.md`](public-triage-cases.md):

```markdown
## Case ID
- Target repo:
- Authorization link:
- Date:
- Command:
- SCSA version:
- Findings:
- Human review outcome:
- Public artifact:
- Maintainer feedback:
```

Required field rules:

- `Case ID` must be stable, for example `PTC-0001`.
- `Authorization link` is required and must be public.
- `Command` must keep `--native-build-policy disabled` unless the target owner
  explicitly authorized trusted local native build execution.
- `Human review outcome` must distinguish automated evidence from reviewer
  decision.
- `Public artifact` must point to a sanitized, maintainer-approved artifact.

## Review and publication checklist

Before counting a case as public adoption evidence:

- Authorization link is public and reviewer-visible.
- Target repository is public or the public summary is maintainer-approved.
- Command and SCSA version are recorded.
- Sensitive material was removed.
- Native build policy is documented.
- Findings are summarized without overclaiming audit certification.
- Human review outcome is recorded.
- Maintainer feedback is linked or explicitly marked `pending`.
- Case was added to `docs/adoption/public-triage-cases.md`.
