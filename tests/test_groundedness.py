from smart_contract_audit.evaluation.groundedness import evaluate_groundedness
from smart_contract_audit.models import Finding, Location


def test_groundedness_counts_only_unsupported_security_claims() -> None:
    supported = _finding("f_001", "supported")
    unsupported = _finding("f_002", "unsupported")

    result = evaluate_groundedness([supported, unsupported])

    assert result["claims_total"] == 2
    assert result["unsupported_security_claims"] == 1
    assert result["findings"][0]["groundedness_status"] == "supported"


def test_groundedness_accepts_phase_two_supported_report() -> None:
    supported = _finding("f_001", "supported")

    result = evaluate_groundedness([supported])

    assert result["unsupported_security_claims"] == 0
    assert result["groundedness_pass"] is True


def _finding(finding_id: str, status: str) -> Finding:
    finding = Finding(
        finding_id=finding_id,
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(file="Vault.sol", function="withdraw", line_start=1, line_end=3),
        evidence="External call before state update.",
        reference=["SWC-107"],
        finding_confidence=0.8,
        explanation_confidence=0.8,
        explanation="The external call occurs before state update.",
        attack_path="The caller can re-enter before state is updated.",
        fix_suggestion="Use checks-effects-interactions.",
        remediation_code="",
        vulnerable_code="msg.sender.call(\"\"); balances[msg.sender] = 0;",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
    )
    finding.evidence_graph = {
        "claim_nodes": [f"claim:{finding_id}:001"],
        "claims": [
            {
                "claim_id": f"claim:{finding_id}:001",
                "text": finding.explanation,
                "groundedness_status": status,
                "support_node_ids": ["source:Vault.sol:1-3"],
            }
        ],
    }
    return finding
