from pathlib import Path
from subprocess import CompletedProcess

from smart_contract_audit.external_tools import run_external_tools


def test_mythril_result_counts_json_issues(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")

    def fake_runner(command: list[str], timeout_seconds: int) -> CompletedProcess[str]:
        assert command[:3] == ["myth", "analyze", str(contract)]
        assert timeout_seconds == 30
        return CompletedProcess(command, 0, stdout='{"issues":[{"title":"reentrancy"}]}', stderr="")

    results = run_external_tools(
        contract,
        tmp_path / "external",
        tools=("mythril",),
        timeout_seconds=30,
        command_runner=fake_runner,
        binary_resolver=lambda name: name,
    )

    assert results[0].tool_name == "mythril"
    assert results[0].status == "finding"
    assert results[0].findings_count == 1
    assert results[0].execution_mode == "symbolic"
    assert results[0].binary_path == "myth"
    assert results[0].timeout_seconds == 30
    assert Path(results[0].output_path).exists()


def test_echidna_result_counts_failed_tests(tmp_path: Path) -> None:
    contract = tmp_path / "Invariant.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Invariant {}", encoding="utf-8")

    def fake_runner(command: list[str], timeout_seconds: int) -> CompletedProcess[str]:
        assert command[:2] == ["echidna", str(contract)]
        return CompletedProcess(
            command,
            1,
            stdout='{"tests":[{"status":"failed"},{"status":"passed"}]}',
            stderr="",
        )

    results = run_external_tools(
        contract,
        tmp_path / "external",
        tools=("echidna",),
        command_runner=fake_runner,
        binary_resolver=lambda name: name,
    )

    assert results[0].tool_name == "echidna"
    assert results[0].status == "finding"
    assert results[0].findings_count == 1


def test_aderyn_result_counts_json_issues_and_sarif_artifact(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")

    def fake_runner(command: list[str], timeout_seconds: int) -> CompletedProcess[str]:
        assert timeout_seconds == 60
        output_index = command.index("--output") + 1
        output_path = Path(command[output_index])
        if output_path.suffix == ".sarif":
            return CompletedProcess(command, 0, stdout='{"version":"2.1.0"}', stderr="")
        return CompletedProcess(
            command,
            1,
            stdout='{"issues":[{"title":"Unchecked return value"}]}',
            stderr="",
        )

    results = run_external_tools(
        contract,
        tmp_path / "external",
        tools=("aderyn",),
        command_runner=fake_runner,
        binary_resolver=lambda name: name,
    )

    assert results[0].tool_name == "aderyn"
    assert results[0].status == "finding"
    assert results[0].findings_count == 1
    assert results[0].execution_mode == "read-only CLI"
    assert results[0].artifact_paths["sarif"].endswith("aderyn.sarif")


def test_medusa_and_halmos_count_failures(tmp_path: Path) -> None:
    contract = tmp_path / "Invariant.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Invariant {}", encoding="utf-8")

    def fake_runner(command: list[str], timeout_seconds: int) -> CompletedProcess[str]:
        if command[0] == "medusa":
            assert command[:2] == ["medusa", "fuzz"]
            return CompletedProcess(
                command,
                1,
                stdout='{"tests":[{"status":"falsified"},{"status":"passed"}]}',
                stderr="",
            )
        assert command[0] == "halmos"
        return CompletedProcess(command, 1, stdout="Counterexample: test invariant", stderr="")

    results = run_external_tools(
        contract,
        tmp_path / "external",
        tools=("medusa", "halmos"),
        command_runner=fake_runner,
        binary_resolver=lambda name: name,
    )

    assert [result.tool_name for result in results] == ["medusa", "halmos"]
    assert [result.status for result in results] == ["finding", "finding"]
    assert [result.findings_count for result in results] == [1, 1]


def test_missing_external_tool_is_skipped(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")

    results = run_external_tools(
        contract,
        tmp_path / "external",
        tools=("mythril",),
        binary_resolver=lambda _: None,
    )

    assert results[0].tool_name == "mythril"
    assert results[0].status == "skipped"
    assert results[0].findings_count == 0
    assert results[0].execution_mode == "symbolic"
    assert results[0].timeout_seconds == 60
    assert "not installed" in results[0].summary
