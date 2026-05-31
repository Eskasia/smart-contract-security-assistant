from smart_contract_audit.models import Finding, Location
from smart_contract_audit.rules import apply_native_rules


def test_apply_native_rules_returns_five_phase_two_rules() -> None:
    finding = _finding(
        vulnerability_type="reentrancy",
        vulnerable_code=(
            "function withdraw() external {\n"
            "  uint256 amount = balances[msg.sender];\n"
            "  (bool success, ) = msg.sender.call{value: amount}(\"\");\n"
            "  require(success);\n"
            "  balances[msg.sender] = 0;\n"
            "}"
        ),
    )
    results = apply_native_rules(finding, [finding])
    rule_ids = {result["rule_id"] for result in results}

    assert rule_ids == {
        "scsa.reentrancy.evidence_confirmer.v1",
        "scsa.auth_sensitive_state_write.v1",
        "scsa.unchecked_low_level_call.v1",
        "scsa.upgradeable_proxy_risk_mapper.v1",
        "scsa.multi_tool_consensus_scorer.v1",
    }
    assert results[0]["status"] == "confirmed_by_evidence"
    assert results[0]["confidence_delta"] > 0


def test_consensus_rule_detects_two_tools_on_same_location() -> None:
    slither = _finding("reentrancy", "msg.sender.call before balance reset", "slither")
    aderyn = _finding("reentrancy", "external call before state update", "aderyn")
    results = apply_native_rules(slither, [slither, aderyn])
    consensus = next(
        result
        for result in results
        if result["rule_id"] == "scsa.multi_tool_consensus_scorer.v1"
    )

    assert consensus["status"] == "confirmed_by_evidence"
    assert consensus["confidence_breakdown"]["multi_tool_agreement"] > 0


def _finding(
    vulnerability_type: str = "reentrancy",
    vulnerable_code: str = "msg.sender.call before balances[msg.sender] = 0",
    source: str = "slither",
) -> Finding:
    return Finding(
        finding_id=f"f_{source}",
        vulnerability_type=vulnerability_type,
        severity=3,
        location=Location(file="Vault.sol", function="withdraw", line_start=4, line_end=8),
        evidence=vulnerable_code,
        reference=["SWC-107"],
        finding_confidence=0.8,
        explanation_confidence=0.8,
        explanation="The finding is supported by source evidence.",
        attack_path="Review the source range.",
        fix_suggestion="Apply the recommended mitigation.",
        remediation_code="",
        vulnerable_code=vulnerable_code,
        static_tool_source=source,
        detector_name=f"{source}:reentrancy",
    )
