from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.fuzz import write_fuzz_seed_outputs
from smart_contract_audit.models import Finding, Location


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="reports/fuzz")
    parser.add_argument("--min-seed-count", type=int, default=1)
    args = parser.parse_args()

    finding = Finding(
        finding_id="f_001",
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(
            file="tests/poc/reentrancy/src/VulnerableVault.sol",
            function="withdraw",
            line_start=11,
            line_end=19,
        ),
        evidence="External call before balance reset.",
        reference=["SWC-107"],
        finding_confidence=0.9,
        explanation_confidence=0.8,
        explanation="withdraw sends ETH before clearing balances.",
        attack_path="Attacker re-enters from receive().",
        fix_suggestion="Apply checks-effects-interactions.",
        remediation_code="",
        vulnerable_code="",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
    )
    result = write_fuzz_seed_outputs([finding], Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["seed_count"] < args.min_seed_count:
        raise SystemExit(f"seed_count {result['seed_count']} below {args.min_seed_count}")


if __name__ == "__main__":
    main()
