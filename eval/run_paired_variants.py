from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.evaluation.paired_variants import (
    evaluate_paired_variants,
    write_paired_variant_reports,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="eval/paired_variants")
    parser.add_argument("--output-dir", default="reports/eval")
    parser.add_argument("--min-paired-pass-rate", type=float, default=0.70)
    args = parser.parse_args()

    result = evaluate_paired_variants(Path(args.root))
    write_paired_variant_reports(result, Path(args.output_dir))
    matrix_path = Path("eval/benchmark_matrix.yml")
    if matrix_path.exists():
        (Path(args.output_dir) / "benchmark_matrix.json").write_text(
            json.dumps(json.loads(matrix_path.read_text(encoding="utf-8")), indent=2),
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["paired_pass_rate"] < args.min_paired_pass_rate:
        raise SystemExit(
            f"paired_pass_rate {result['paired_pass_rate']} below {args.min_paired_pass_rate}"
        )


if __name__ == "__main__":
    main()
