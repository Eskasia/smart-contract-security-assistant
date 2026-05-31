# Phase 3 Advanced Evidence

Last updated: 2026-06-01.

Phase 3 adds sandbox-only advanced evidence on top of Phase 1 attribution and Phase 2 Evidence Graph traceability. Normal `scsa analyze` does not execute PoC validation by default.

## Evidence Types

- `exploit_validation` records triggerability, execution mode, transaction sequence, asset delta, execution log path, safety notes, and `human_review_required`.
- `fuzz_seed_suggestions` gives reviewer-facing Echidna, Medusa, or Foundry starting directions. A seed is a suggestion, not a confirmed exploit.
- `formal_property_suggestions` gives draft invariants, annotations, or rules. `status` must stay `draft` and `verification_status` must stay `not_proven` until a verifier actually compiles and proves it.
- `defi_profit_signal` records asset flow only when it comes from local execution or trusted external-tool output.

## Safety Boundary

Allowed execution targets:

- local fixtures
- user-owned or authorized repositories
- Foundry or Hardhat sandbox projects
- local Ethereum nodes
- mock tokens, mock oracles, and mock pools

Blocked targets:

- mainnet exploit transactions
- funded wallet flows
- unauthorized third-party contracts
- bypass steps against third-party controls

## Local Validation Fixture

The first sandbox fixture lives at `tests/poc/reentrancy/`.

Run:

```bash
uv run python eval/run_exploit_validation.py
```

Expected output:

```text
status = executed_triggered
mode = local_foundry_test
triggered = true
human_review_required = true
```

Generated artifacts:

```text
reports/poc/f_001/validation.json
reports/poc/f_001/execution.log
```

## Evaluation Scripts

```bash
uv run python eval/run_fuzz_seed_suggestions.py --min-seed-count 1
uv run python eval/run_formal_property_suggestions.py --min-property-count 1
uv run python eval/run_evmbench_adapter.py
uv run scsa properties suggest reports/<contract_id>.json --format foundry-invariant --out reports/properties
```

The EVMbench adapter is scoped to detect result alignment, patch-suggestion-only metadata, and sandbox-only exploit validation. It does not generate executable exploits for unauthorized targets.
