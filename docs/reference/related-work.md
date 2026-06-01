# Related Work

Updated: 2026-06-01

## Static Analysis

SCSA uses Slither as the primary deterministic finding source. SCSA does not
claim to replace Slither detectors. Its contribution is evidence normalization,
traceability, review workflow, report generation, and standards-aligned output.

Aderyn is treated as an optional external static-analysis signal. SCSA records
its JSON findings and SARIF artifact path when the operator enables it.

## Fuzzing and Property Testing

SCSA treats Echidna and Medusa output as optional external signals. It
normalizes invariant failures, failed properties, counterexample metadata, and
reviewer status into the same report workflow as other findings.

SCSA does not claim to be a fuzzer. Phase 3 emits reviewer-facing fuzz seed
suggestions and sandbox validation artifacts, while Echidna and Medusa remain
external fuzzing engines.

## Symbolic Execution and Symbolic Testing

SCSA treats Mythril and Halmos output as optional symbolic signals. It records
symbolic issues, proof failures, and assertion failures as evidence rather than
merging them into opaque AI output.

Halmos is restricted to explicit trusted Foundry project mode because it depends on native build behavior.

## RAG and LLM Assistance

SCSA uses LLMs only to explain analyzer-backed evidence. LLM output cannot
create a vulnerability without a deterministic analyzer finding or an enabled
external-tool signal.

## Evidence-Oriented Security Review

SCSA's original focus is a local-first evidence layer: SQLite traces,
JSON/Markdown reports, reviewer workflow, CI gates, benchmark gates, and report
comparison.

## Explicit Non-Goals

- SCSA does not detect all Solidity vulnerabilities.
- SCSA does not replace Slither, Aderyn, Echidna, Medusa, Mythril, or Halmos.
- SCSA does not automatically complete a human audit.
- SCSA does not guarantee contract safety.
- SCSA does not use AI to create unsupported vulnerability facts.
