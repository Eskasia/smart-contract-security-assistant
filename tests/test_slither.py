from pathlib import Path

import pytest

from smart_contract_audit.finding_adapter import normalize_slither_json
from smart_contract_audit.slither_runner import (
    SlitherRunError,
    get_system_solc_version,
    run_slither,
)


def test_slither_detects_fixture_reentrancy() -> None:
    try:
        result = run_slither(Path("tests/contracts/VulnerableVault.sol"))
    except SlitherRunError as exc:
        pytest.fail(f"Slither integration failed: {exc}")

    normalized = normalize_slither_json(
        result.raw_json,
        Path("tests/contracts/VulnerableVault.sol"),
    )

    assert result.raw_json.get("success") is True
    assert result.slither_version
    assert result.solc_version
    assert any(finding.detector_name == "reentrancy-eth" for finding in normalized.findings)


def test_slither_resolves_local_imports_from_entry_contract() -> None:
    entry_path = Path("tests/contracts/ImportEntryVault.sol")

    try:
        result = run_slither(entry_path)
    except SlitherRunError as exc:
        pytest.fail(f"Slither local import resolution failed: {exc}")

    normalized = normalize_slither_json(result.raw_json, entry_path)
    reentrancy_findings = [
        finding
        for finding in normalized.findings
        if finding.detector_name == "reentrancy-eth"
    ]

    assert result.raw_json.get("success") is True
    assert reentrancy_findings
    assert any("ImportBaseVault.sol" in finding.location.file for finding in reentrancy_findings)


def test_system_solc_version_is_detected() -> None:
    version = get_system_solc_version()
    assert version is None or version.count(".") == 2
