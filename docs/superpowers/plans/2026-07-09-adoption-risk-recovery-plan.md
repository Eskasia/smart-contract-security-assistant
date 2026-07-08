# Adoption Risk Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current adoption uncertainty into source-backed metrics, a repeatable external-evidence funnel, and one defensible industry-leading feature plan.

**Architecture:** Treat adoption evidence and product differentiation as separate tracks. Track 1 updates public evidence from live sources without inflating adoption; Track 2 converts outreach into public, permissioned evidence; Track 3 designs Finding-to-Repro Harness as a later product PR after evidence docs are current.

**Tech Stack:** Markdown docs, GitHub REST API snapshots, PyPI JSON, GitHub issues/PRs, existing SCSA CLI/report pipeline, future Foundry test skeleton generation.

## Global Constraints

- Work from latest `main`, not `codex/finding-falsification-pack`, `codex/frontend-dependency-security-refresh`, or stale `adoption/g2-3-adoption-metrics-tracker`.
- Do not claim unverified external adoption, stars, forks, downloads, testers, testimonials, case studies, or public triage cases.
- Use exact dates in `YYYY-MM-DD` format.
- Keep `docs/adoption/metrics.md` as the canonical source for adoption counts.
- Keep repository-owned fixtures separate from external adoption evidence.
- Do not implement Finding-to-Repro Harness until the evidence tracker and adoption funnel are current.

---

## Current Situation Summary

- `main` is synced with `origin/main` as of 2026-07-09.
- Open PRs remain separate: PR #32 frontend dependency refresh and PR #33 finding falsification packs.
- `docs/adoption/metrics.md` exists, but its latest recorded update is 2026-06-17.
- Live checks on 2026-07-09 showed GitHub stars `1`, forks `0`, release asset downloads `0`, and PyPI package version `0.2.1`.
- The biggest strategic gap is not documentation volume; it is lack of external, verifiable adoption evidence.
- The most likely three-month failure mode is internal feature/documentation progress without tester feedback, public triage cases, testimonials, or external OSS adoption links.
- The strongest product differentiator to plan next is Finding-to-Repro Harness: static finding to executable Foundry PoC or invariant-test skeleton plus reviewer replay instructions.

## File Structure

- Modify: `docs/adoption/metrics.md`
  Responsibility: canonical adoption metrics, source dates, weekly update log.
- Modify: `docs/adoption/codex-for-oss-evidence.md`
  Responsibility: evidence index that points to the current metrics and adoption status.
- Modify: `docs/adoption/codex-for-oss-adoption-evidence-plan.md`
  Responsibility: 2-4 week conversion plan from outreach to public evidence.
- Modify: `docs/adoption/tester-onboarding.md`
  Responsibility: make tester feedback submission path concrete and measurable.
- Modify: `docs/adoption/external-adoptions.md`
  Responsibility: keep external adoption entries source-backed and empty unless public evidence exists.
- Create: `docs/design/finding-to-repro-harness.md`
  Responsibility: design the later industry-leading feature before implementation.
- Optional future modify: `docs/DOCS_INDEX.md`
  Responsibility: index any changed or newly created docs.

### Task 1: Refresh Adoption Facts

**Files:**
- Modify: `docs/adoption/metrics.md`
- Modify: `docs/adoption/codex-for-oss-evidence.md`
- Modify: `docs/DOCS_INDEX.md`

**Interfaces:**
- Consumes: GitHub repo API, GitHub releases API, PyPI JSON, existing metrics table.
- Produces: source-backed adoption snapshot dated 2026-07-09.

- [ ] **Step 1: Capture live source snapshots**

Run:

```bash
curl -fsSL "https://api.github.com/repos/Eskasia/smart-contract-security-assistant" \
  | jq '{stargazers_count, forks_count, open_issues_count, pushed_at, default_branch}'

curl -fsSL "https://api.github.com/repos/Eskasia/smart-contract-security-assistant/releases" \
  | jq 'map({tag_name, published_at, assets: [.assets[] | {name, download_count}]})[:3]'

curl -fsSL "https://pypi.org/pypi/smart-contract-security-assistant/json" \
  | jq '{version: .info.version, releases: (.releases | keys | sort | .[-5:])}'
```

Expected on 2026-07-09:

```text
GitHub stars: 1
GitHub forks: 0
GitHub v0.2.1 release asset downloads: 0 total
PyPI version: 0.2.1
```

- [ ] **Step 2: Update metrics without inflating adoption**

In `docs/adoption/metrics.md`:

```markdown
Updated: 2026-07-09

| GitHub stars | 1 | 100 | GitHub repo API snapshot on 2026-07-09: `stargazers_count=1` |
| GitHub forks | 0 | 30 | GitHub repo API snapshot on 2026-07-09: `forks_count=0` |
| Monthly downloads | 0 | 1000 | PyPI package `smart-contract-security-assistant` is published at version `0.2.1`, but PyPI JSON does not provide a package-hosted monthly download counter; GitHub `v0.2.1` release asset download total was `0` on 2026-07-09 |
```

Add a weekly update entry:

```markdown
### 2026-07-09

| Checklist item | Status | Evidence |
|---|---|---|
| Update stars/forks | No change: stars `1`, forks `0` | GitHub repo API on 2026-07-09 |
| Update package publication | PyPI package remains published at `0.2.1` | <https://pypi.org/project/smart-contract-security-assistant/> |
| Update download evidence | No counted downloads yet | PyPI JSON confirms package/version but does not provide a monthly download counter; GitHub `v0.2.1` release assets had `download_count=0` on 2026-07-09 |
| Add new feedback issues | No completed tester feedback issues logged | Public outreach and templates do not count as completed feedback |
| Add real testimonials | None logged | [`docs/adoption/testimonials.md`](testimonials.md) remains empty |
| Add public triage cases | None logged | [`docs/adoption/public-triage-cases.md`](public-triage-cases.md) remains empty |
| Add external adoption links | None logged | [`docs/adoption/external-adoptions.md`](external-adoptions.md) remains empty |
```

- [ ] **Step 3: Update evidence index summary**

In `docs/adoption/codex-for-oss-evidence.md`, update the adoption section to:

```markdown
Latest weekly adoption update: 2026-07-09. The PyPI package is published at
`0.2.1`, GitHub stars are `1`, GitHub forks are `0`, and the GitHub `v0.2.1`
release asset download total is `0`. No package-hosted monthly download
counter, completed tester feedback issue, testimonial, public triage case, or
external OSS adoption link is logged.
```

- [ ] **Step 4: Verify**

Run:

```bash
rg -n "2026-07-09|stargazers_count=1|forks_count=0|download_count=0" docs/adoption/metrics.md docs/adoption/codex-for-oss-evidence.md
rg -n "External testers \\| 0|Public triage cases \\| 0|Testimonials \\| 0|External OSS adoptions \\| 0" docs/adoption/metrics.md
git diff --check
```

Expected: all commands exit `0`; no adoption count is increased.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/adoption/metrics.md docs/adoption/codex-for-oss-evidence.md docs/DOCS_INDEX.md
git commit -m "docs: refresh adoption metrics snapshot"
```

### Task 2: Convert Adoption Risk Into Weekly Operating Loop

**Files:**
- Modify: `docs/adoption/codex-for-oss-adoption-evidence-plan.md`
- Modify: `docs/adoption/tester-onboarding.md`
- Modify: `docs/adoption/external-adoptions.md`
- Modify: `docs/DOCS_INDEX.md`

**Interfaces:**
- Consumes: current zero-count metrics, public triage protocol, tester onboarding flow.
- Produces: weekly adoption operating loop with explicit evidence gates.

- [ ] **Step 1: Add weekly loop to evidence plan**

Add this section to `docs/adoption/codex-for-oss-adoption-evidence-plan.md`:

```markdown
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
```

- [ ] **Step 2: Make tester feedback path measurable**

In `docs/adoption/tester-onboarding.md`, ensure the feedback instructions require:

```markdown
- Public feedback issue link or explicit permission to summarize privately shared feedback.
- Repository tested, authorization basis, command run, and report artifact summary.
- Permission field for whether the feedback can count as testimonial evidence.
- Confirmation that private code, secrets, addresses, and proprietary audit material were removed.
```

- [ ] **Step 3: Keep external adoption log conservative**

In `docs/adoption/external-adoptions.md`, ensure the counting rule says:

```markdown
An entry counts only when a public repository, issue, pull request, workflow,
release note, or maintainer-approved document shows SCSA being used outside
this repository. Private conversations, planned outreach, local fixtures, and
unmerged templates do not count.
```

- [ ] **Step 4: Verify**

Run:

```bash
rg -n "Weekly adoption operating loop|Completed tester feedback issue|External OSS adoption" docs/adoption/codex-for-oss-adoption-evidence-plan.md
rg -n "permission to summarize|Permission field|private code" docs/adoption/tester-onboarding.md
rg -n "Private conversations, planned outreach, local fixtures" docs/adoption/external-adoptions.md
git diff --check
```

Expected: all commands exit `0`.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/adoption/codex-for-oss-adoption-evidence-plan.md docs/adoption/tester-onboarding.md docs/adoption/external-adoptions.md docs/DOCS_INDEX.md
git commit -m "docs: add adoption evidence operating loop"
```

### Task 3: Design Finding-to-Repro Harness

**Files:**
- Create: `docs/design/finding-to-repro-harness.md`
- Modify: `docs/DOCS_INDEX.md`

**Interfaces:**
- Consumes: existing report JSON, finding metadata, formal property suggestions, fuzz seed notes, Foundry project detection.
- Produces: implementation-ready design for a later feature PR.

- [ ] **Step 1: Write the design document**

Create `docs/design/finding-to-repro-harness.md`:

```markdown
# Finding-to-Repro Harness

Status: proposed
Updated: 2026-07-09

## Goal

Generate reviewer-owned reproducibility tasks from SCSA findings without
claiming proof, exploitability, or audit certification.

## Non-goals

- Do not execute untrusted project build tooling by default.
- Do not claim that generated tests prove a vulnerability.
- Do not overwrite maintainer test suites.
- Do not generate private exploit payloads for unauthorized targets.

## User workflow

1. Run `scsa analyze` and produce a JSON report.
2. Run a future `scsa repro plan <report.json> --format foundry`.
3. Review generated Foundry test skeletons and invariant drafts.
4. Maintainer fills project-specific setup and assertions.
5. CI runs the harness only in explicitly trusted project mode.

## Artifact shape

Each generated repro task should include:

- finding id
- vulnerability type
- target contract and source span when available
- suspected preconditions
- counterevidence checks
- Foundry test skeleton path
- replay command
- reviewer warnings

## Safety boundary

Generated harnesses are reviewer work items. They are not confirmed exploits,
formal proofs, or deployment safety claims until a human reviewer adapts and
executes them in an authorized environment.

## First implementation slice

Support only deterministic skeleton generation from existing report JSON:

- no network access
- no project dependency installation
- no native build execution
- no automatic exploit calldata synthesis
- output to a new directory chosen by the reviewer

## Verification

- Unit tests cover report-to-task mapping.
- Snapshot tests cover generated Foundry skeleton text.
- CLI tests verify output path safety.
- Docs verify that generated harnesses remain reviewer-only drafts.
```

- [ ] **Step 2: Index the design**

Add one row to `docs/DOCS_INDEX.md`:

```markdown
| design | 007 | proposed | Finding-to-Repro Harness | 設計 finding 轉成 reviewer-owned Foundry repro skeleton / invariant draft 的後續功能，保留 human-review 與 authorized-use 邊界。 | 2026-07-09 | `docs/design/finding-to-repro-harness.md` |
```

- [ ] **Step 3: Verify**

Run:

```bash
test -f docs/design/finding-to-repro-harness.md
rg -n "reviewer-owned|Do not claim|trusted project mode|First implementation slice" docs/design/finding-to-repro-harness.md
rg -n "Finding-to-Repro Harness" docs/DOCS_INDEX.md
git diff --check
```

Expected: all commands exit `0`.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/design/finding-to-repro-harness.md docs/DOCS_INDEX.md
git commit -m "docs: design finding-to-repro harness"
```

### Task 4: Conversation Efficiency Protocol

**Files:**
- Create: `docs/superpowers/plans/2026-07-09-adoption-risk-recovery-plan.md`
- Optional modify: project-local `AGENTS.md` only if the user explicitly asks to make this protocol permanent.

**Interfaces:**
- Consumes: current thread confusion around stale summaries, branch drift, and live metrics.
- Produces: repeatable conversation entry snapshot.

- [ ] **Step 1: Use this snapshot before future adoption work**

At the start of each adoption-related task, capture:

```text
Branch:
Main sync:
Open PRs:
Current goal:
Metrics date:
Live stars/forks/downloads:
Files in scope:
Files out of scope:
```

- [ ] **Step 2: Verify the snapshot with commands**

Run:

```bash
git status --short --branch
gh pr list --state open --json number,title,headRefName,baseRefName,url
rg -n "Updated:|GitHub stars|GitHub forks|Monthly downloads" docs/adoption/metrics.md
```

Expected: the assistant can answer the snapshot before editing files.

- [ ] **Step 3: Keep it out of permanent instructions unless repeated**

Do not edit `AGENTS.md` for this protocol unless it proves useful across at least three adoption tasks or the user explicitly asks for permanent workflow rules.

## Execution Order

1. Task 1 in one PR: refresh adoption facts.
2. Task 2 in one PR: add evidence operating loop.
3. Task 3 in one PR: design the industry-leading product feature.
4. Task 4 remains an operating habit unless the user asks to codify it.

## Acceptance Criteria

- Metrics are updated to 2026-07-09 without increasing unverified counts.
- Evidence index and metrics page agree.
- Weekly adoption loop defines concrete conversion targets and counting rules.
- Finding-to-Repro Harness is designed, not implemented.
- No branch work is based on stale PR #32, PR #33, or old G2.3 branches.
- `git diff --check` passes for each PR.

## Remaining Risks

- External adoption remains `0` until real testers or maintainers produce public, permissioned evidence.
- The Finding-to-Repro Harness may be less compelling if it stays a design doc and does not ship as a working CLI artifact.
- Live metrics can become stale again unless Task 2's weekly loop is followed.
