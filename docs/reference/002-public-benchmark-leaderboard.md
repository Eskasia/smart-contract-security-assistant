# SCSA Public Benchmark Leaderboard

Generated: 2026-05-17.

## Phase 2 Gate Summary

更新日期：2026-06-01

SCSA Phase 2 的公開評測入口包含 Hugging Face Slither50、public project
build preflight 與本機 paired variants detect mode。

| Benchmark | Mode | CI required | Gate |
|---|---|---:|---|
| Paired variants | detect | yes | `paired_pass_rate >= 0.70` |
| HF Slither50 v2 | detect | yes | `supported_hit_rate >= 0.95`, `score_gap >= 30`, `recall >= 0.5`, `f1 >= 0.5` |
| Public project build preflight | detect preflight | yes | no missing required tools |

Phase 2 不宣稱 Patch 或 Exploit mode 成績；EVM-style patch/exploit
evaluation 留到 Phase 3 sandbox-only scope。

## Headline

| Metric | Value |
|---|---:|
| Cases | 50 |
| Analyzer successful runs | 50 |
| Supported label hit rate | 100.00% |
| Matched label occurrences | 36 / 36 |
| Safe minus vulnerable score gap | 45.05 |
| Precision | 86.21% |
| Recall | 100.00% |
| F1 | 92.59% |

## Confusion Matrix

| Class | Count |
|---|---:|
| True positive | 25 |
| True negative | 21 |
| False positive | 4 |
| False negative | 0 |

## Label Coverage

| Label | Matched | Expected | Hit Rate |
|---|---:|---:|---:|
| access-control | 1 | 1 | 100.00% |
| bad-randomness | 10 | 10 | 100.00% |
| reentrancy | 16 | 16 | 100.00% |
| unchecked-calls | 9 | 9 | 100.00% |

## Case Results

| Case | Class | Expected | Detected | Missed | Score |
|---|---|---|---|---|---:|
| hf50_01 | safe | - | - | - | 100.00 |
| hf50_02 | safe | - | - | - | 100.00 |
| hf50_03 | safe | - | - | - | 100.00 |
| hf50_04 | safe | - | - | - | 100.00 |
| hf50_05 | safe | - | - | - | 100.00 |
| hf50_06 | safe | - | - | - | 100.00 |
| hf50_07 | safe | - | unchecked-calls | - | 74.60 |
| hf50_08 | safe | - | - | - | 83.20 |
| hf50_09 | safe | - | - | - | 100.00 |
| hf50_10 | safe | - | - | - | 95.00 |
| hf50_11 | safe | - | - | - | 83.20 |
| hf50_12 | safe | - | - | - | 83.20 |
| hf50_13 | safe | - | - | - | 100.00 |
| hf50_14 | safe | - | - | - | 100.00 |
| hf50_15 | safe | - | - | - | 100.00 |
| hf50_16 | safe | - | - | - | 83.20 |
| hf50_17 | safe | - | - | - | 100.00 |
| hf50_18 | safe | - | reentrancy | - | 92.70 |
| hf50_19 | safe | - | - | - | 100.00 |
| hf50_20 | safe | - | - | - | 100.00 |
| hf50_21 | safe | - | reentrancy | - | 97.70 |
| hf50_22 | safe | - | - | - | 95.00 |
| hf50_23 | safe | - | access-control | - | 69.50 |
| hf50_24 | safe | - | - | - | 100.00 |
| hf50_25 | safe | - | - | - | 61.40 |
| hf50_26 | vulnerable | reentrancy | reentrancy | - | 68.90 |
| hf50_27 | vulnerable | bad-randomness | bad-randomness | - | 0.00 |
| hf50_28 | vulnerable | reentrancy | reentrancy | - | 85.70 |
| hf50_29 | vulnerable | reentrancy, unchecked-calls | reentrancy, unchecked-calls | - | 2.90 |
| hf50_30 | vulnerable | bad-randomness, reentrancy, unchecked-calls | bad-randomness, reentrancy, unchecked-calls | - | 0.00 |
| hf50_31 | vulnerable | bad-randomness | bad-randomness | - | 81.40 |
| hf50_32 | vulnerable | bad-randomness | bad-randomness | - | 89.80 |
| hf50_33 | vulnerable | access-control, bad-randomness | access-control, bad-randomness | - | 33.80 |
| hf50_34 | vulnerable | reentrancy | reentrancy | - | 68.90 |
| hf50_35 | vulnerable | bad-randomness | bad-randomness | - | 89.80 |
| hf50_36 | vulnerable | unchecked-calls | access-control, unchecked-calls | - | 8.60 |
| hf50_37 | vulnerable | bad-randomness, unchecked-calls | bad-randomness, unchecked-calls | - | 64.40 |
| hf50_38 | vulnerable | bad-randomness, reentrancy | bad-randomness, reentrancy | - | 0.00 |
| hf50_39 | vulnerable | unchecked-calls | unchecked-calls | - | 57.80 |
| hf50_40 | vulnerable | reentrancy, unchecked-calls | reentrancy, unchecked-calls | - | 0.00 |
| hf50_41 | vulnerable | reentrancy, unchecked-calls | reentrancy, unchecked-calls | - | 31.70 |
| hf50_42 | vulnerable | reentrancy | reentrancy | - | 68.90 |
| hf50_43 | vulnerable | unchecked-calls | reentrancy, unchecked-calls | - | 56.00 |
| hf50_44 | vulnerable | bad-randomness, reentrancy | bad-randomness, reentrancy | - | 67.10 |
| hf50_45 | vulnerable | reentrancy | reentrancy | - | 81.10 |
| hf50_46 | vulnerable | reentrancy | reentrancy | - | 28.90 |
| hf50_47 | vulnerable | reentrancy | reentrancy | - | 68.90 |
| hf50_48 | vulnerable | reentrancy | reentrancy | - | 68.90 |
| hf50_49 | vulnerable | bad-randomness, reentrancy, unchecked-calls | bad-randomness, reentrancy, unchecked-calls | - | 0.00 |
| hf50_50 | vulnerable | reentrancy | reentrancy | - | 68.90 |

## Scope

This leaderboard reports deterministic benchmark results for the local SCSA pipeline. It is not a replacement for manual smart-contract review, invariant fuzzing, or formal verification.
