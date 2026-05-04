from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.evaluation.public_benchmark import run_benchmark


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
    args = parser.parse_args()

    summary = run_benchmark(
        args.manifest,
        args.reports_dir,
        rag_mode=args.rag_mode,
        min_supported_hit_rate=args.min_supported_hit_rate,
        min_score_gap=args.min_score_gap,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
