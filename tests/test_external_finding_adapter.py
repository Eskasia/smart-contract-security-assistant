from pathlib import Path

from smart_contract_audit.external_finding_adapter import (
    merge_external_findings,
    normalize_echidna_output,
    normalize_mythril_output,
)
from smart_contract_audit.models import Finding, Location
from smart_contract_audit.solidity_target import resolve_solidity_target


def test_normalize_mythril_issue_to_formal_finding(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19;\ncontract Vault {}\n", encoding="utf-8")
    target = resolve_solidity_target(contract)

    findings = normalize_mythril_output(
        {
            "issues": [
                {
                    "title": "External Call To User-Supplied Address",
                    "description": "An external call can lead to reentrancy.",
                    "severity": "High",
                    "swc-id": "SWC-107",
                    "locations": [{"filename": str(contract), "line": 2}],
                }
            ]
        },
        target,
        start_index=3,
    )

    assert len(findings) == 1
    assert findings[0].finding_id == "f_003"
    assert findings[0].vulnerability_type == "reentrancy"
    assert findings[0].severity == 3
    assert findings[0].location.file == str(contract)
    assert findings[0].location.line_start == 2
    assert findings[0].static_tool_source == "mythril"
    assert findings[0].detector_name == "mythril:SWC-107"


def test_merge_external_findings_deduplicates_overlapping_supported_findings() -> None:
    existing = _finding("f_001", "reentrancy", line_start=10, line_end=12)
    external = _finding("f_002", "reentrancy", line_start=11, line_end=11)
    external.static_tool_source = "mythril"

    merged = merge_external_findings([existing], [external])

    assert merged == [existing]


def test_normalize_echidna_failure_to_formal_finding(tmp_path: Path) -> None:
    contract = tmp_path / "InvariantVault.sol"
    contract.write_text("pragma solidity ^0.8.19;\ncontract InvariantVault {}\n", encoding="utf-8")
    target = resolve_solidity_target(contract)
    payload = {
        "tests": [
            {
                "contract": "InvariantVault",
                "name": "echidna_total_assets_never_decrease",
                "status": "failed",
                "error": "property falsified after withdraw",
                "transactions": [{"contract": "InvariantVault", "function": "withdraw"}],
            },
            {"name": "echidna_owner", "status": "passed"},
        ]
    }

    findings = normalize_echidna_output(payload, target)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.static_tool_source == "echidna"
    assert finding.detector_name == "echidna:echidna_total_assets_never_decrease"
    assert finding.vulnerability_type == "invariant_violation"
    assert finding.severity == 2
    assert finding.location.file == str(target.entry_path)
    assert "property falsified" in finding.evidence


def _finding(
    finding_id: str,
    vulnerability_type: str,
    line_start: int,
    line_end: int,
) -> Finding:
    return Finding(
        finding_id=finding_id,
        vulnerability_type=vulnerability_type,
        severity=3,
        location=Location(
            file="Vault.sol",
            function="withdraw",
            line_start=line_start,
            line_end=line_end,
        ),
        evidence="evidence",
        reference=["SWC-107"],
        finding_confidence=1.0,
        explanation_confidence=1.0,
        explanation="explanation",
        attack_path="attack",
        fix_suggestion="fix",
        remediation_code="code",
        vulnerable_code="code",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
    )
