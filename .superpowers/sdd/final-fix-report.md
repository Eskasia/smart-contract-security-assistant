# Final Fix Report: Whole-branch adoption evidence wording updates

Scope: `.github/ISSUE_TEMPLATE/tester-feedback.yml`, `docs/adoption/tester-onboarding.md`, `docs/adoption/metrics.md`, `docs/superpowers/plans/2026-07-09-adoption-risk-recovery-plan.md`  
Date: 2026-07-09

## Changes
- `tester-feedback.yml`: replaced self-referential `feedback_issue_or_permission` prompt with "current GitHub issue is the feedback record" and now collects external public evidence links (outside this issue) or explicit permission to summarize privately shared feedback.
- `docs/adoption/tester-onboarding.md`: aligned language to treat the opened issue as the current feedback record and collect only external evidence links or permission to summarize privately shared feedback.
- `docs/adoption/metrics.md`: split update rule so feedback issues require public links or permission to summarize, while testimonials require explicit permission to quote.
- `docs/superpowers/plans/2026-07-09-adoption-risk-recovery-plan.md`: added top scope note stating only Task 1/2/4 in this PR, deferred Task 3 to branch `codex/finding-to-repro-harness-design-wip`, and updated execution order and acceptance criteria accordingly.

## Command results
1. `rg -n "external evidence links|permission to summarize|current GitHub issue" .github/ISSUE_TEMPLATE/tester-feedback.yml docs/adoption/tester-onboarding.md`  
   - found required lines in both files.
2. `rg -n "permission to summarize|permission to quote" docs/adoption/metrics.md docs/adoption/tester-onboarding.md`  
   - found required lines in both files.
3. `rg -n "Task 3.*deferred|codex/finding-to-repro-harness-design-wip|Task 1/2/4" docs/superpowers/plans/2026-07-09-adoption-risk-recovery-plan.md`  
   - found scope and execution-order updates for deferred Task 3 and Task 1/2/4 scope.
4. `test ! -f docs/design/finding-to-repro-harness.md`  
   - exit `0`, as expected (file not present).
5. `git diff --check`  
   - exit `0`, no whitespace issues.
