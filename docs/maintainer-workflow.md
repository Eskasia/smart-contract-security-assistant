# Maintainer Workflow

Status: current
Updated: 2026-06-01

This guide gives maintainers copy-paste workflows for pull request triage,
issue triage, release regression checks, and human reviewer handoff.

Related references:

- [README](../README.md)
- [SECURITY.md](../SECURITY.md)
- [Public report schema](../schema/report.schema.json)
- [Reusable SCSA PR triage GitHub Action](templates/scsa-pr-triage.yml)

## Authorized-Use Boundary

Only analyze repositories, contracts, pull requests, or issue reproductions
that you own, maintain, or are explicitly authorized to review. Do not upload
private keys, secrets, customer contracts, proprietary audit reports, or
unauthorized third-party code into SCSA reports, traces, issues, or pull request
comments.

SCSA output is automated triage evidence for a human reviewer. It is not final
audit certification.

## Workflow A: Pull Request Security Triage

Use this workflow when a pull request changes Solidity source or security
critical project configuration.

```bash
uv sync --extra audit --dev
uv run scsa analyze <contract.sol|project-dir> \
  --out-dir reports-pr \
  --native-build-policy disabled
```

Attach or link these artifacts in the pull request:

- `reports-pr/<contract_id>.json`
- `reports-pr/<contract_id>.md`
- `reports-pr/analysis_trace.sqlite`

Review checklist:

- Confirm the repository is authorized for review.
- Confirm every report still says `requires_human_review=true`.
- Check whether findings come from mapped detector output.
- Check trace evidence before accepting or rejecting each finding.
- Keep `--native-build-policy disabled` unless the project is local and trusted.

For external maintainers who want a copy-paste GitHub Actions entrypoint, use
[`docs/templates/scsa-pr-triage.yml`](templates/scsa-pr-triage.yml). The
template is manual-only, requires an explicit target path, uploads
`scsa-reports`, and keeps native build execution disabled by default.

## Workflow B: Issue Triage From a User-Reported Solidity Bug

Use this workflow when a user reports a suspected vulnerability with a minimal
contract, public repository, or reproduction archive.

```bash
uv sync --extra audit --dev
uv run scsa analyze <reproduction.sol|project-dir> \
  --out-dir reports-issue \
  --native-build-policy disabled
```

Record in the issue:

- Whether the report produced `finding`, `no_finding`, `partial_analysis`, or
  `error`.
- The finding IDs and severity levels, if any.
- Whether the finding is reproducible from the submitted input.
- What evidence still needs a human reviewer.

Do not paste private report contents into a public issue unless the reporter
explicitly provided public-safe material.

## Workflow C: Release Regression Comparison

Use this workflow before release candidates when a baseline report exists.

```bash
uv run scsa compare-reports reports/base.json reports/head.json \
  --output reports/comparison.md \
  --fail-on-high-added \
  --fail-on-score-drop 10
```

Expected artifacts:

- `reports/comparison.md`
- Updated JSON and Markdown reports for the release candidate.
- CI logs showing whether the comparison gate passed.

Fail the release candidate if a high-severity finding is newly introduced or
the score drops past the configured threshold without a documented maintainer
decision.

## Workflow D: Evidence Handoff To Human Reviewer

Use this workflow when automated triage has produced evidence that needs a
qualified reviewer decision.

Handoff package:

- JSON report validated against `schema/report.schema.json`.
- Markdown report for reviewer reading.
- SQLite trace database for raw analyzer output and evidence graph lookup.
- Any external-tool artifacts listed in `external_tool_results`.
- Review notes explaining accepted risk, false positive, fixed, or blocked
  statuses.

Human reviewer must check:

- Source authorization.
- Raw analyzer evidence.
- Standards mapping context.
- Business-logic, governance, oracle, economic, and cross-contract risks that
  automated triage cannot certify.

## Commands

```bash
uv sync --extra audit --dev
uv run scsa analyze <contract.sol|project-dir> --out-dir reports-pr --native-build-policy disabled
uv run scsa compare-reports reports/base.json reports/head.json --output reports/comparison.md --fail-on-high-added --fail-on-score-drop 10
uv run python scripts/sync_report_schema.py --check
uv run ruff check .
uv run pytest
```

## Expected Artifacts

| Artifact | Purpose |
|---|---|
| `reports-pr/<contract_id>.json` | Machine-readable report for schema validation and automation |
| `reports-pr/<contract_id>.md` | Human-readable triage report |
| `reports-pr/analysis_trace.sqlite` | Raw evidence, trace rows, review state, and evidence graph data |
| `reports/comparison.md` | Release or PR regression comparison |
| CI logs | Reproducible validation evidence |

## Limitations

- SCSA is triage, not full audit certification.
- Only mapped detector output is promoted to formal report findings.
- Unmapped analyzer output is retained as trace evidence until mapped.
- LLM output explains evidence; it does not create vulnerability facts.
- Native build mode can execute project build scripts and should stay disabled
  for untrusted code.
- Human reviewer approval is required before treating findings as final.

## Copy-Paste GitHub Issue / PR Comment Templates

### Pull Request Triage Comment

```markdown
SCSA triage summary:

- Status:
- Finding count:
- High severity added:
- Review status:
- Report artifact:
- Trace evidence:
- Human reviewer required: yes

This is automated triage, not final audit certification.
```

### Issue Triage Comment

```markdown
SCSA issue triage summary:

- Authorized source confirmed:
- Reproduction analyzed:
- Report status:
- Finding IDs:
- Evidence artifact:
- Human reviewer required: yes

This result is an initial security triage signal. It does not certify the
contract as safe or unsafe to deploy.
```

### Release Regression Comment

```markdown
SCSA release regression summary:

- Baseline report:
- Candidate report:
- Comparison artifact:
- High severity added:
- Score delta:
- Gate result:
- Human reviewer required: yes

Release should remain blocked until new high-severity findings or score drops
are reviewed and documented.
```
