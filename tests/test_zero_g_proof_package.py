from __future__ import annotations

import json
from pathlib import Path

from smart_contract_audit.zero_g.proof_package import (
    attach_zero_g_proof,
    build_proof_package,
    sha256_file,
)


def _write_report(path: Path) -> None:
    payload = {
        "contract_id": "vulnerablevault",
        "overall_status": "finding",
        "findings": [{"id": "f_001", "severity": 3}],
        "analysis_metadata": {
            "security_score": {
                "score": 68.9,
                "score_formula_version": "security_score_v2",
            },
            "analysis_trace_id": "trace-123",
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_proof_package_writes_stable_manifest(tmp_path: Path) -> None:
    report = tmp_path / "vulnerablevault.json"
    _write_report(report)

    result = build_proof_package(
        report_path=report,
        output_dir=tmp_path / "reports-0g",
        project_name="SCSA 0G Audit Proof",
        track="Track 1: Agentic Infrastructure & OpenClaw Lab",
    )

    assert result.contract_id == "vulnerablevault"
    assert result.output_dir == tmp_path / "reports-0g" / "vulnerablevault"
    assert result.proof_json == result.output_dir / "audit-proof.json"
    assert result.proof_json.read_text(encoding="utf-8").endswith("\n")

    proof = json.loads(result.proof_json.read_text(encoding="utf-8"))
    assert proof["schema_version"] == "scsa_0g_proof_v1"
    assert proof["project_name"] == "SCSA 0G Audit Proof"
    assert proof["track"] == "Track 1: Agentic Infrastructure & OpenClaw Lab"
    assert proof["report"]["contract_id"] == "vulnerablevault"
    assert proof["report"]["sha256"] == sha256_file(report)
    assert proof["report"]["security_score"] == 68.9
    assert proof["report"]["findings_count"] == 1
    assert proof["zero_g"]["storage_root_hash"] is None
    assert proof["zero_g"]["storage_tx_hash"] is None
    assert proof["zero_g"]["registry_address"] is None
    assert proof["zero_g"]["registry_tx_hash"] is None
    assert proof["zero_g"]["explorer_links"] == {}


def test_build_proof_package_rejects_path_like_contract_id(tmp_path: Path) -> None:
    report = tmp_path / "escape.json"
    payload = {
        "contract_id": "../escape",
        "overall_status": "finding",
        "findings": [],
        "analysis_metadata": {"security_score": {"score": 100.0}},
    }
    report.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    try:
        build_proof_package(
            report_path=report,
            output_dir=tmp_path / "reports-0g",
            project_name="SCSA 0G Audit Proof",
            track="Track 1: Agentic Infrastructure & OpenClaw Lab",
        )
    except ValueError as exc:
        assert "contract_id" in str(exc)
    else:
        raise AssertionError("path-like contract_id should be rejected")


def test_attach_zero_g_proof_adds_metadata(tmp_path: Path) -> None:
    report = tmp_path / "vulnerablevault.json"
    _write_report(report)
    proof = {
        "storage_root_hash": "0x" + "11" * 32,
        "storage_tx_hash": "0x" + "22" * 32,
        "registry_address": "0x" + "33" * 20,
        "registry_tx_hash": "0x" + "44" * 32,
        "explorer_links": {
            "registry": "https://www.0gscan.com/address/0x3333333333333333333333333333333333333333",
            "registration_tx": "https://www.0gscan.com/tx/0x4444444444444444444444444444444444444444444444444444444444444444",
        },
    }

    output = attach_zero_g_proof(report, proof)

    assert output == report
    assert output.read_text(encoding="utf-8").endswith("\n")
    updated = json.loads(output.read_text(encoding="utf-8"))
    assert updated["analysis_metadata"]["zero_g_proof"] == proof
