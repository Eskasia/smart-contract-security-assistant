import json
from pathlib import Path

from smart_contract_audit.report_compare import (
    compare_report_files,
    comparison_should_fail,
    render_comparison_markdown,
)


def test_compare_report_files_tracks_added_fixed_and_persistent_findings(tmp_path: Path) -> None:
    base = tmp_path / "base.json"
    head = tmp_path / "head.json"
    _write_report(
        base,
        security_score=80.0,
        findings=[
            _finding("f_001", "reentrancy", 3, "Vault.sol", 10, "reentrancy-eth"),
            _finding("f_002", "unchecked_external_call", 2, "Vault.sol", 20, "unchecked-send"),
        ],
    )
    _write_report(
        head,
        security_score=67.5,
        findings=[
            _finding("f_101", "unchecked_external_call", 2, "Vault.sol", 20, "unchecked-send"),
            _finding("f_102", "access_control", 3, "Vault.sol", 30, "arbitrary-send-eth"),
        ],
    )

    comparison = compare_report_files(base, head)

    assert comparison["security_score_delta"] == -12.5
    assert comparison["added_count"] == 1
    assert comparison["fixed_count"] == 1
    assert comparison["persistent_count"] == 1
    assert comparison["high_severity_added_count"] == 1
    assert comparison["added_findings"][0]["vulnerability_type"] == "access_control"
    assert comparison["fixed_findings"][0]["vulnerability_type"] == "reentrancy"


def test_comparison_fail_gate_and_markdown_summary(tmp_path: Path) -> None:
    base = tmp_path / "base.json"
    head = tmp_path / "head.json"
    _write_report(base, security_score=90.0, findings=[])
    _write_report(
        head,
        security_score=75.0,
        findings=[_finding("f_001", "access_control", 3, "Vault.sol", 12, "suicidal")],
    )

    comparison = compare_report_files(base, head)
    markdown = render_comparison_markdown(comparison)

    assert comparison_should_fail(
        comparison,
        fail_on_high_added=True,
        fail_on_score_drop=10.0,
    )
    assert "Security score delta: `-15.00`" in markdown
    assert "Added findings: `1`" in markdown
    assert "access_control" in markdown


def _finding(
    finding_id: str,
    vulnerability_type: str,
    severity: int,
    file: str,
    line_start: int,
    detector_name: str,
) -> dict:
    return {
        "finding_id": finding_id,
        "vulnerability_type": vulnerability_type,
        "severity": severity,
        "location": {
            "file": file,
            "function": "withdraw",
            "line_start": line_start,
            "line_end": line_start,
        },
        "detector_name": detector_name,
        "evidence": f"{vulnerability_type} evidence",
    }


def _write_report(path: Path, security_score: float, findings: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "contract_id": "vault",
                "security_score": security_score,
                "findings": findings,
            }
        ),
        encoding="utf-8",
    )
