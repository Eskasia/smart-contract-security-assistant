from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.properties import suggest_properties_for_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="reports/poc/f_001/fixture_report.json")
    parser.add_argument("--output-dir", default="reports/properties")
    parser.add_argument("--format", default="foundry_invariant")
    parser.add_argument("--min-property-count", type=int, default=1)
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        _write_fixture_report(report_path)
    result = suggest_properties_for_report(
        report_path=report_path,
        output_dir=Path(args.output_dir),
        output_format=args.format,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["property_count"] < args.min_property_count:
        raise SystemExit(
            f"property_count {result['property_count']} below {args.min_property_count}"
        )


def _write_fixture_report(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "findings": [
                    {
                        "finding_id": "f_001",
                        "vulnerability_type": "reentrancy",
                        "location": {
                            "file": "tests/poc/reentrancy/src/VulnerableVault.sol",
                            "function": "withdraw",
                            "line_start": 11,
                            "line_end": 19,
                        },
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
