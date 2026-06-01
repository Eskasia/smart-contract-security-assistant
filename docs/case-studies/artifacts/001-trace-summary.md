# Case Study 001 Trace Summary

Status: sanitized excerpt
Generated from: `reports-case-study-001/analysis_trace.sqlite`
Generated at: 2026-06-01

Raw SQLite is intentionally not committed. This excerpt records only the fields
needed to reproduce the case study evidence path.

## Trace Dashboard

| Field | Value |
|---|---|
| Final status | `finding` |
| Contract ID | `3fca00c06c2f` |
| Dataset version | `dataset_v1.0` |
| Model version | `mlx-8b-4bit` |
| solc version | `0.8.35` |
| Slither version | `0.11.5` |
| Review status | `pending_human_review` |
| Finding rows | `1` |

## Finding Trace Row

| Field | Value |
|---|---|
| Finding ID | `f_001` |
| Detector | `reentrancy-eth` |
| RAG mode | `balanced` |
| Chunks used | `3` |
| RAG chunk IDs | `report_001_0000`, `report_003_0000`, `report_002_0000` |
| Schema valid | `true` |
| Partial | `false` |
| Review status | `unreviewed` |

## Evidence Graph

- Root finding node: `finding:f_001`
- Source node: `source:tests/contracts/VulnerableVault.sol:11-16`
- Tool signal node: `tool_signal:slither:reentrancy-eth:f_001`
- Supported claims: `3`
- Unsupported security claims: `0`
- Native rule result count: `5`
- Exploit validation status: `not_attempted`
- Exploit validation mode: `sandbox_only`
- Fuzz seed suggestions: `1`
- Formal property suggestions: `1`

## Sanitization Notes

- Local absolute paths are omitted.
- Raw Slither JSON is not copied.
- Packed prompt and LLM raw output are not copied.
- SQLite database is not committed.
