# Benchmark Reproducibility

Status: current reproducibility guide
Updated: 2026-06-01

This page explains how to reproduce the benchmark gates used for SCSA public
evidence. These checks measure mapped detector behavior, score separation,
paired fixture detection, and groundedness. They do not measure complete
Solidity vulnerability coverage and do not replace human review, fuzzing, or
formal verification.

## Dataset

The public benchmark gate uses:

- Manifest:
  `eval/public_benchmark/hf-slither50-v2-manifest.json`
- Source files:
  `public-contracts/hf-slither50-v2/`
- Upstream dataset:
  <https://huggingface.co/datasets/mwritescode/slither-audited-smart-contracts>
- Case count: 50
- Supported public labels in the current manifest: `access-control`,
  `bad-randomness`, `reentrancy`, and `unchecked-calls`

The paired-variant gate uses local positive/negative Solidity fixture pairs
under `eval/paired_variants/`. It currently covers 15 pairs across these
internal vulnerability types: `access_control`, `dangerous_delegatecall`,
`reentrancy`, `unchecked_external_call`, and `upgrade_risk`.

The groundedness gate uses a deterministic in-repo finding fixture in
`eval/run_rag_groundedness.py` and checks that generated security claims are
supported by evidence graph fields.

## Supported detector scope

SCSA promotes only mapped Slither detector output into formal report findings.
Unmapped Slither output remains trace evidence until mapped.

The authoritative mapped detector list is
`src/smart_contract_audit/config.py::DETECTOR_MAPPING`. The public HF Slither50
benchmark maps current report findings into these benchmark labels:

| Internal type | Public benchmark label |
|---|---|
| `reentrancy` | `reentrancy` |
| `unchecked_external_call` | `unchecked-calls` |
| `oracle` | `bad-randomness` |
| `access_control` | `access-control` |
| `privilege_escalation` | `access-control` |

Other mapped internal types can still appear in reports, paired variants, or
trace evidence, but they are not all measured by the HF Slither50 public-label
hit-rate gate.

## Commands

Run from the repository root:

```bash
uv run python eval/run_public_benchmark.py \
  --min-supported-hit-rate 0.95 \
  --min-score-gap 30 \
  --min-recall 0.5 \
  --min-f1 0.5

uv run python eval/run_paired_variants.py --min-paired-pass-rate 0.70
uv run python eval/run_rag_groundedness.py --max-unsupported-security-claims 0
```

The public benchmark writes reports under `reports-public/benchmark/`. The
paired-variant and groundedness checks write JSON and Markdown summaries under
`reports/eval/`.

## Metrics

Public benchmark metrics:

- `supported_hit_rate`: fraction of expected supported label occurrences that
  SCSA detected.
- `average_score_gap_safe_minus_vulnerable`: average score separation between
  safe and vulnerable cases.
- `precision`, `recall`, `f1`: binary classification metrics based on whether a
  case has expected vulnerable labels and whether SCSA detected supported
  labels.

Paired-variant metric:

- `paired_pass_rate`: fraction of local positive/negative pairs where SCSA
  flags the positive fixture and leaves the negative fixture clean for the
  expected behavior.

Groundedness metric:

- `unsupported_security_claims`: count of generated security claims that are
  not supported by evidence graph fields.

## Gates

CI currently enforces:

| Gate | Threshold |
|---|---:|
| Public supported-label hit rate | `>= 0.95` |
| Public safe-minus-vulnerable score gap | `>= 30` |
| Public recall | `>= 0.5` |
| Public F1 | `>= 0.5` |
| Paired variant pass rate | `>= 0.70` |
| Groundedness unsupported security claims | `<= 0` |

The CI workflow records these commands in `.github/workflows/ci.yml`.

## Known limitations

- The benchmark is scoped to supported labels and mapped detector output, not
  complete Solidity vulnerability coverage.
- Safe cases can still produce findings; those count against precision and
  should be reviewed as possible false positives.
- Unsupported vulnerability classes, business logic, governance, oracle
  economics, MEV, and cross-contract risks still require qualified human review.
- Native Foundry and Hardhat build execution is disabled by default for
  untrusted or imported sources.
- RAG groundedness checks claim support for evidence-linked wording only; they
  do not prove a vulnerability exists.

## Last verified run

Latest recorded benchmark summary:
[`docs/reference/002-public-benchmark-leaderboard.md`](002-public-benchmark-leaderboard.md)

As of 2026-06-01, the recorded public benchmark summary is:

- 50 cases
- 100.00% supported-label hit rate
- 86.21% precision
- 100.00% recall
- 92.59% F1
- 45.05 safe-minus-vulnerable score gap
- `paired_pass_rate = 1.0`
- `unsupported_security_claims = 0`
