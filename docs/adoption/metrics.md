# Adoption Metrics

Status: current manual tracker
Updated: 2026-07-13

This tracker records only source-backed adoption signals for the current Codex
for OSS application phase. Repository-owned fixtures, local validation runs,
and planned outreach do not count as external adoption.

## Current metrics

| Metric | Current | Target | Evidence |
|---|---:|---:|---|
| GitHub stars | 1 | 100 | GitHub repo API snapshot on 2026-07-13: `stargazers_count=1` |
| GitHub forks | 0 | 30 | GitHub repo API snapshot on 2026-07-13: `forks_count=0` |
| External testers | 0 | 10 | No external tester entries logged in [`docs/adoption/codex-for-oss-evidence.md`](codex-for-oss-evidence.md#external-tester-evidence) |
| Public triage cases | 0 | 3 | [`docs/adoption/public-triage-cases.md`](public-triage-cases.md) has no authorized public cases |
| Feedback issues | 0 | 5 | No completed current adoption-phase feedback issue links are logged; [issue #12](https://github.com/Eskasia/smart-contract-security-assistant/issues/12) is tester outreach, not feedback received |
| Testimonials | 0 | 10 | No quoted testimonials are logged in [`docs/adoption/codex-for-oss-evidence.md`](codex-for-oss-evidence.md#testimonials) |
| Monthly downloads | 0 | 1000 | PyPI package `smart-contract-security-assistant` is published at version `0.2.1`, but PyPI JSON does not provide a package-hosted monthly download counter; GitHub `v0.2.1` release asset download total was `0` on 2026-07-13 |
| External OSS adoptions | 0 | 2 | No public repo adoption links are logged |

## Weekly update log

### 2026-06-02

| Checklist item | Status | Evidence |
|---|---|---|
| Update package publication | PyPI package published at `0.2.1` | <https://pypi.org/project/smart-contract-security-assistant/> |
| Update download evidence | No counted downloads yet | PyPI JSON confirms package/version but does not provide a monthly download counter; GitHub `v0.2.1` release assets had `downloadCount=0` on 2026-06-02 |
| Add new feedback issues | No completed tester feedback issues logged | Public outreach and templates do not count as completed feedback |
| Add real testimonials | None logged | [`docs/adoption/testimonials.md`](testimonials.md) remains empty |
| Add public triage cases | None logged | [`docs/adoption/public-triage-cases.md`](public-triage-cases.md) remains empty |
| Add external adoption links | None logged | [`docs/adoption/external-adoptions.md`](external-adoptions.md) remains empty |

### 2026-06-01

| Checklist item | Status | Evidence |
|---|---|---|
| Update stars/forks | No change: stars `0`, forks `0` | GitHub repo API on 2026-06-01 |
| Add new feedback issues | No completed tester feedback issues logged | Public [issue #12](https://github.com/Eskasia/smart-contract-security-assistant/issues/12) is tester outreach only |
| Add real testimonials | None logged | [`docs/adoption/testimonials.md`](testimonials.md) remains empty |
| Add public triage cases | None logged | [`docs/adoption/public-triage-cases.md`](public-triage-cases.md) remains empty |
| Add release notes | No new release for this weekly update | Latest public releases are `v0.2.0` and `v0.1.0`; both have 0 release assets |
| Add external adoption links | None logged | [`docs/adoption/external-adoptions.md`](external-adoptions.md) remains empty |

## Update rules

1. Record only metrics with a source, collection date, and evidence link.
2. GitHub stars and forks may be updated from the GitHub repo API.
3. Download counts must come from PyPI, GitHub release assets, or another
   explicit package/download counter; source archive URLs are not counted.
4. External testers, public triage cases, testimonials, feedback issues, and OSS
   adoptions require public links or explicit permission to quote.
5. Repository fixtures under `docs/case-studies/` do not count as external
   adoption, public triage cases, or testimonials.

## Evidence sources

- GitHub repo: <https://github.com/Eskasia/smart-contract-security-assistant>
- GitHub repo API:
  <https://api.github.com/repos/Eskasia/smart-contract-security-assistant>
- GitHub releases:
  <https://github.com/Eskasia/smart-contract-security-assistant/releases>
- PyPI project JSON:
  <https://pypi.org/pypi/smart-contract-security-assistant/json>
