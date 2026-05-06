import subprocess
from pathlib import Path

import pytest

from smart_contract_audit.finding_adapter import normalize_slither_json
from smart_contract_audit.slither_runner import (
    SlitherRunError,
    get_system_solc_version,
    prepare_native_build,
    run_slither,
)
from smart_contract_audit.solidity_target import resolve_solidity_target


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


def test_slither_project_directory_detects_independent_contract(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "A.sol").write_text(
        """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.19;
        contract A {
            function ok() external pure returns (uint256) {
                return 1;
            }
        }
        """,
        encoding="utf-8",
    )
    (project / "Z.sol").write_text(
        """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.19;
        contract Z {
            mapping(address => uint256) public balances;
            function deposit() external payable {
                balances[msg.sender] += msg.value;
            }
            function withdraw() external {
                uint256 amount = balances[msg.sender];
                (bool success,) = msg.sender.call{value: amount}("");
                require(success);
                balances[msg.sender] = 0;
            }
        }
        """,
        encoding="utf-8",
    )

    result = run_slither(project)
    normalized = normalize_slither_json(result.raw_json, project)

    assert any("Z.sol" in finding.location.file for finding in normalized.findings)


def test_slither_uses_successful_native_foundry_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "foundry"
    source_dir = project / "src"
    source_dir.mkdir(parents=True)
    (project / "foundry.toml").write_text('[profile.default]\nsrc = "src"\n', encoding="utf-8")
    (source_dir / "Vault.sol").write_text(
        "pragma solidity ^0.8.19;\ncontract Vault {}\n",
        encoding="utf-8",
    )
    commands: list[tuple[list[str], Path | None]] = []

    def fake_which(name: str) -> str | None:
        return {"forge": "forge", "slither": "slither", "solc": "solc"}.get(name)

    def fake_run(
        command: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: int = 15,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        commands.append((command, cwd))
        if command[0] == "solc":
            return subprocess.CompletedProcess(command, 0, stdout="Version: 0.8.34", stderr="")
        if command[:2] == ["slither", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="0.11.5", stderr="")
        if command[0] == "forge":
            return subprocess.CompletedProcess(command, 0, stdout="compiled", stderr="")
        if command[0] == "slither":
            output_path = Path(command[command.index("--json") + 1])
            output_path.write_text(
                '{"success": true, "results": {"detectors": []}}',
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("smart_contract_audit.slither_runner.shutil.which", fake_which)
    monkeypatch.setattr("smart_contract_audit.slither_runner.subprocess.run", fake_run)

    result = run_slither(project)

    assert result.raw_json["success"] is True
    assert any(command[:2] == ["forge", "build"] for command, _ in commands)
    slither_command = next(command for command, _ in commands if command[0] == "slither")
    assert str(project) in slither_command
    assert "--compile-force-framework" not in slither_command
    assert "foundry native build completed before Slither." in result.warnings


def test_slither_can_disable_native_build_for_untrusted_projects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "foundry"
    source_dir = project / "src"
    source_dir.mkdir(parents=True)
    (project / "foundry.toml").write_text('[profile.default]\nsrc = "src"\n', encoding="utf-8")
    (source_dir / "Vault.sol").write_text(
        "pragma solidity ^0.8.19;\ncontract Vault {}\n",
        encoding="utf-8",
    )
    commands: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        return {"forge": "forge", "slither": "slither", "solc": "solc"}.get(name)

    def fake_run(
        command: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: int = 15,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[0] == "solc":
            return subprocess.CompletedProcess(command, 0, stdout="Version: 0.8.34", stderr="")
        if command[:2] == ["slither", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="0.11.5", stderr="")
        if command[0] == "slither":
            output_path = Path(command[command.index("--json") + 1])
            output_path.write_text(
                '{"success": true, "results": {"detectors": []}}',
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("smart_contract_audit.slither_runner.shutil.which", fake_which)
    monkeypatch.setattr("smart_contract_audit.slither_runner.subprocess.run", fake_run)

    result = run_slither(project, native_build_policy="disabled")

    assert not any(command[0] == "forge" for command in commands)
    assert any(
        "--compile-force-framework" in command
        for command in commands
        if command[0] == "slither"
    )
    assert "Native build disabled by policy." in result.warnings


def test_hardhat_native_build_prefers_package_compile_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "hardhat"
    contracts = project / "contracts"
    contracts.mkdir(parents=True)
    (project / "hardhat.config.js").write_text("module.exports = {};\n", encoding="utf-8")
    (project / "package.json").write_text(
        '{"scripts": {"compile": "SKIP_LOAD=true hardhat compile"}}',
        encoding="utf-8",
    )
    (contracts / "Vault.sol").write_text(
        "pragma solidity ^0.8.19;\ncontract Vault {}\n",
        encoding="utf-8",
    )
    commands: list[tuple[list[str], Path | None]] = []

    def fake_run(
        command: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: int = 15,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        commands.append((command, cwd))
        return subprocess.CompletedProcess(command, 0, stdout="compiled", stderr="")

    monkeypatch.setattr(
        "smart_contract_audit.slither_runner.shutil.which",
        lambda name: "/bin/npm" if name == "npm" else None,
    )
    monkeypatch.setattr("smart_contract_audit.slither_runner.subprocess.run", fake_run)

    result = prepare_native_build(resolve_solidity_target(project))

    assert result.succeeded is True
    assert commands == [(["/bin/npm", "run", "compile"], project.resolve())]


def test_system_solc_version_is_detected() -> None:
    version = get_system_solc_version()
    assert version is None or version.count(".") == 2
