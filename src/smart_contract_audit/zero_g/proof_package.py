from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SAFE_CONTRACT_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ProofPackageResult:
    contract_id: str
    output_dir: Path
    proof_json: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_proof_package(
    report_path: Path,
    output_dir: Path,
    project_name: str,
    track: str,
) -> ProofPackageResult:
    report_path = report_path.resolve()
    output_dir = output_dir.resolve()
    report = _read_json(report_path)
    contract_id = _contract_id(report, report_path)
    target_dir = output_dir / contract_id
    target_dir.mkdir(parents=True, exist_ok=True)
    proof_path = target_dir / "audit-proof.json"
    report_sha256 = sha256_file(report_path)

    proof = {
        "created_at": _stable_created_at(report_sha256),
        "project_name": project_name,
        "report": {
            "contract_id": contract_id,
            "file_name": report_path.name,
            "findings_count": _findings_count(report),
            "overall_status": report.get("overall_status"),
            "security_score": _security_score(report),
            "sha256": report_sha256,
            "trace_id": _analysis_metadata(report).get("analysis_trace_id"),
        },
        "schema_version": "scsa_0g_proof_v1",
        "track": track,
        "zero_g": {
            "explorer_links": {},
            "registry_address": None,
            "registry_tx_hash": None,
            "storage_root_hash": None,
            "storage_tx_hash": None,
        },
    }
    _write_json(proof_path, proof)
    return ProofPackageResult(contract_id=contract_id, output_dir=target_dir, proof_json=proof_path)


def attach_zero_g_proof(report_path: Path, proof: dict[str, Any]) -> Path:
    report = _read_json(report_path)
    metadata = report.setdefault("analysis_metadata", {})
    metadata["zero_g_proof"] = {
        "explorer_links": proof["explorer_links"],
        "registry_address": proof["registry_address"],
        "registry_tx_hash": proof["registry_tx_hash"],
        "storage_root_hash": proof["storage_root_hash"],
        "storage_tx_hash": proof["storage_tx_hash"],
    }
    _write_json(report_path, report)
    return report_path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _contract_id(report: dict[str, Any], report_path: Path) -> str:
    value = report.get("contract_id")
    contract_id = value if isinstance(value, str) and value else report_path.stem
    if not SAFE_CONTRACT_ID.fullmatch(contract_id) or contract_id in {".", ".."}:
        raise ValueError("contract_id must be a safe relative path segment.")
    return contract_id


def _stable_created_at(report_sha256: str) -> str:
    seconds = int(report_sha256[:8], 16) % 86_400
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"1970-01-01T{hours:02d}:{minutes:02d}:{secs:02d}+00:00"


def _analysis_metadata(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("analysis_metadata")
    return value if isinstance(value, dict) else {}


def _security_score(report: dict[str, Any]) -> float | None:
    direct_value = report.get("security_score")
    if isinstance(direct_value, (int, float)):
        return float(direct_value)

    metadata_score = _analysis_metadata(report).get("security_score")
    if isinstance(metadata_score, dict):
        value = metadata_score.get("score")
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _findings_count(report: dict[str, Any]) -> int:
    findings = report.get("findings")
    return len(findings) if isinstance(findings, list) else 0
