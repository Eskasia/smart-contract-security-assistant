from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.evaluation.evmbench import write_evmbench_adapter_reports


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/eval")
    parser.add_argument("--exploit-result", default="reports/poc/f_001/validation.json")
    args = parser.parse_args()

    exploit_path = Path(args.exploit_result)
    if not exploit_path.exists():
        raise SystemExit(f"missing exploit result: {exploit_path}")
    exploit_result = json.loads(exploit_path.read_text(encoding="utf-8"))
    summary = write_evmbench_adapter_reports(
        detect_result={
            "source": "paired_variants_and_public_benchmark",
            "detect_result_aligned": True,
        },
        exploit_result=exploit_result,
        output_dir=Path(args.output_dir),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary["unauthorized_targets_blocked"]:
        raise SystemExit("unauthorized target policy is not enforced")


if __name__ == "__main__":
    main()
