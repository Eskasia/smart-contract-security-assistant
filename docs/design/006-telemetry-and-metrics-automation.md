# Distribution Metrics Automation Design Spec

Status: current
Last updated: 2026-06-17

This design covers a source-backed adoption metrics updater for the Codex for
OSS application evidence set. It intentionally excludes client-side telemetry:
the CLI must not send contract paths, repository names, target identifiers, or
finding summaries to a public issue or external service.

## Goals

1. Update only metrics that have public, reproducible sources.
2. Keep external testers, public triage cases, testimonials, feedback issues,
   and external OSS adoption links manual until each entry has a public issue,
   PR, report artifact, or explicit quote permission.
3. Make source failures visible in CI instead of silently treating failed
   requests as no-op metric updates.
4. Submit automated changes through pull requests instead of pushing directly
   to `main`.

## Sources

| Source | Fields used | Metrics affected |
|---|---|---|
| GitHub repo API | `stargazers_count`, `forks_count` | GitHub stars, GitHub forks |
| GitHub release API | release asset `download_count` | download evidence text only |
| PyPI JSON | `info.version` | package publication evidence text only |

PyPI JSON does not expose a package-hosted monthly download counter, so the
automation does not fabricate monthly downloads. Until an accepted monthly
counter source is added, `Monthly downloads` remains `0` and the evidence cell
records the latest package version plus GitHub release asset download total.

## Workflow

The weekly GitHub Actions workflow runs `scripts/update_adoption_metrics.py
--write`, validates `git diff --check`, and opens a pull request only when
`docs/adoption/metrics.md` changes. The workflow has explicit `contents: write`
and `pull-requests: write` permissions and uses concurrency to prevent
overlapping metrics update runs.

## Non-goals

- No CLI telemetry.
- No external adoption, tester, public triage, feedback, or testimonial counts
  without source-backed manual entries.
- No direct commits to `main`.
