from smart_contract_audit.falsification import build_falsification_pack
from smart_contract_audit.models import Finding, Location


def test_reentrancy_falsification_pack_names_refuting_checks() -> None:
    finding = _finding()

    pack = build_falsification_pack(finding)

    check_ids = {
        check["check_id"] for check in pack["counterevidence_checks"]
    }
    assert pack["status"] == "needs_human_review"
    assert pack["human_review_required"] is True
    assert "reentrancy_guard_effective" in check_ids
    assert "No positive or negative reentrancy guard evidence is recorded." in pack[
        "missing_evidence"
    ]
    assert pack["supported_by"] == [
        "detector:reentrancy-eth",
        "static_tool:slither",
        "location:Vault.sol:11",
    ]


def test_finding_to_dict_includes_generated_falsification_pack() -> None:
    data = _finding().to_dict()

    assert data["falsification_pack"]["counterevidence_checks"]
    assert data["falsification_pack"]["confirmation_requirements"]
    assert data["falsification_pack"]["limitations"]


def _finding() -> Finding:
    return Finding(
        finding_id="f_001",
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(file="Vault.sol", function="withdraw", line_start=11, line_end=13),
        evidence="External call before balance update.",
        reference=["SWC-107"],
        finding_confidence=0.9,
        explanation_confidence=0.8,
        explanation="External call occurs before state update.",
        attack_path="Caller can re-enter before state is updated.",
        fix_suggestion="Use checks-effects-interactions.",
        remediation_code="",
        vulnerable_code='msg.sender.call(""); balances[msg.sender] = 0;',
        static_tool_source="slither",
        detector_name="reentrancy-eth",
    )
