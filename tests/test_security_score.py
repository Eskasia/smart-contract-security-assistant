from smart_contract_audit.models import Finding, Location
from smart_contract_audit.scoring.security_score import compute_security_score


def test_security_score_starts_at_one_hundred_for_clean_contract() -> None:
    result = compute_security_score(
        findings=[],
        review_status="pending_human_review",
        partial_analysis=False,
        business_logic_review_required=False,
    )

    assert result.score == 100.0
    assert result.formula_version == "security_score_v1"
    assert result.factors["total_finding_penalty"] == 0.0


def test_security_score_penalizes_unreviewed_high_confidence_findings() -> None:
    result = compute_security_score(
        findings=[
            _finding("f_001", severity=3, confidence=1.0),
            _finding("f_002", severity=2, confidence=0.5),
        ],
        review_status="pending_human_review",
        partial_analysis=True,
        business_logic_review_required=True,
    )

    assert result.score == 49.0
    assert result.factors["severity_counts"] == {"1": 0, "2": 1, "3": 1}
    assert result.factors["partial_analysis_penalty"] == 10.0
    assert result.factors["business_logic_review_penalty"] == 5.0


def _finding(finding_id: str, severity: int, confidence: float) -> Finding:
    return Finding(
        finding_id=finding_id,
        vulnerability_type="reentrancy",
        severity=severity,
        location=Location(file="Vault.sol", function="withdraw", line_start=1, line_end=1),
        evidence="evidence",
        reference=["SWC-107"],
        finding_confidence=confidence,
        explanation_confidence=1.0,
        explanation="explanation",
        attack_path="attack path",
        fix_suggestion="fix",
        remediation_code="code",
        vulnerable_code="code",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
    )
