from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from smart_contract_audit.evaluation.public_benchmark import (
    run_benchmark,
    write_public_benchmark_leaderboard,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        type=Path,
        nargs="?",
        default=Path("eval/public_benchmark/hf-slither50-v2-manifest.json"),
    )
    parser.add_argument("--reports-dir", type=Path, default=Path("reports-public/benchmark"))
    parser.add_argument(
        "--rag-mode",
        choices=["quality", "balanced", "fast", "fallback"],
        default="fallback",
    )
    parser.add_argument("--min-supported-hit-rate", type=float, default=0.0)
    parser.add_argument("--min-score-gap", type=float)
    parser.add_argument("--min-precision", type=float, default=0.0)
    parser.add_argument("--min-recall", type=float, default=0.0)
    parser.add_argument("--min-f1", type=float, default=0.0)
    parser.add_argument("--leaderboard-output", type=Path)
    parser.add_argument("--leaderboard-date", default=date.today().isoformat())
    args = parser.parse_args()

    summary = run_benchmark(
        args.manifest,
        args.reports_dir,
        rag_mode=args.rag_mode,
        min_supported_hit_rate=args.min_supported_hit_rate,
        min_score_gap=args.min_score_gap,
        min_precision=args.min_precision,
        min_recall=args.min_recall,
        min_f1=args.min_f1,
    )
    if args.leaderboard_output:
        write_public_benchmark_leaderboard(
            summary,
            args.leaderboard_output,
            generated_date=args.leaderboard_date,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
