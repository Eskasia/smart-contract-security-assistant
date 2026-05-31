from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.evaluation.groundedness import evaluate_groundedness
from smart_contract_audit.evidence_graph import build_evidence_graph
from smart_contract_audit.models import Finding, Location


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", default="reports/eval/rag_groundedness.json")
    parser.add_argument("--max-unsupported-security-claims", type=int, default=0)
    args = parser.parse_args()

    finding = Finding(
        finding_id="grounded_001",
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(
            file="GroundedVault.sol",
            function="withdraw",
            line_start=10,
            line_end=14,
        ),
        evidence="External call occurs before balance reset.",
        reference=["SWC-107"],
        finding_confidence=0.85,
        explanation_confidence=0.8,
        explanation="The external call occurs before the balance reset.",
        attack_path="The caller can re-enter before the balance is reset.",
        fix_suggestion="Reset balance before the external call.",
        remediation_code="",
        vulnerable_code="msg.sender.call(\"\"); balances[msg.sender] = 0;",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
    )
    graph = build_evidence_graph(
        finding=finding,
        trace_id="trace_groundedness",
        rag_chunk_ids=["groundedness_fixture:001"],
        rule_results=[],
    )
    finding.evidence_graph = graph.summary
    result = evaluate_groundedness([finding])
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["unsupported_security_claims"] > args.max_unsupported_security_claims:
        raise SystemExit(
            "unsupported_security_claims "
            f"{result['unsupported_security_claims']} exceeds "
            f"{args.max_unsupported_security_claims}"
        )


if __name__ == "__main__":
    main()
