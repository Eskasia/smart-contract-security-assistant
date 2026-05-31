# Public Benchmark Leaderboard

更新日期：2026-06-01

SCSA Phase 2 的公開評測入口包含 Hugging Face Slither50、public project build preflight 與本機 paired variants detect mode。

| Benchmark | Mode | CI required | Gate |
|---|---|---:|---|
| Paired variants | detect | yes | `paired_pass_rate >= 0.70` |
| HF Slither50 v2 | detect | yes | `supported_hit_rate >= 0.95`, `score_gap >= 30`, `recall >= 0.5`, `f1 >= 0.5` |
| Public project build preflight | detect preflight | yes | no missing required tools |

Phase 2 不宣稱 Patch 或 Exploit mode 成績；EVM-style patch/exploit evaluation 留到 Phase 3 sandbox-only scope。
