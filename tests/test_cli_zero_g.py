from __future__ import annotations

import json
from pathlib import Path

from smart_contract_audit.cli import main


def _write_report(path: Path) -> None:
    payload = {
        "analysis_metadata": {
            "analysis_trace_id": "trace-123",
            "security_score": {"score": 68.9},
        },
        "contract_id": "vulnerablevault",
        "findings": [{"id": "f_001", "severity": 3}],
        "overall_status": "finding",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_zero_g_package_command_writes_proof_json(
    tmp_path: Path,
    capsys,
) -> None:
    report = tmp_path / "vulnerablevault.json"
    output_dir = tmp_path / "reports-0g"
    _write_report(report)

    main(
        [
            "0g-package",
            str(report),
            "--out-dir",
            str(output_dir),
            "--project-name",
            "SCSA 0G Audit Proof",
            "--track",
            "Track 1: Agentic Infrastructure & OpenClaw Lab",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    proof_json = Path(output["proof_json"])
    assert output == {
        "contract_id": "vulnerablevault",
        "output_dir": str(output_dir.resolve() / "vulnerablevault"),
        "proof_json": str(proof_json),
    }
    assert proof_json == output_dir.resolve() / "vulnerablevault" / "audit-proof.json"
    assert proof_json.exists()


def test_zero_g_attach_proof_command_updates_report(
    tmp_path: Path,
    capsys,
) -> None:
    report = tmp_path / "vulnerablevault.json"
    proof = tmp_path / "submission-proof.json"
    _write_report(report)
    proof_payload = {
        "explorer_links": {
            "registration_tx": "https://example.invalid/0g-registration-test",
        },
        "registry_address": "0x" + "33" * 20,
        "registry_tx_hash": "0x" + "44" * 32,
        "storage_root_hash": "0x" + "11" * 32,
        "storage_tx_hash": "0x" + "22" * 32,
    }
    proof.write_text(json.dumps(proof_payload, indent=2), encoding="utf-8")

    main(["0g-attach-proof", str(report), str(proof)])

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "proof": str(proof.resolve()),
        "report": str(report.resolve()),
    }
    updated = json.loads(report.read_text(encoding="utf-8"))
    assert updated["analysis_metadata"]["zero_g_proof"] == proof_payload
