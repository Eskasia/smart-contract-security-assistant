from pathlib import Path

from smart_contract_audit.analyzer import analyze_contract
from smart_contract_audit.finding_adapter import normalize_slither_json
from smart_contract_audit.slither_runner import SlitherRunError, SlitherRunResult, run_slither
from smart_contract_audit.solidity_target import (
    resolve_solidity_target,
    slither_command_args_for_target,
)


def test_resolve_foundry_project_with_remappings() -> None:
    target = resolve_solidity_target(Path("tests/fixtures/solidity_projects/foundry"))

    assert target.input_kind == "project_directory"
    assert target.project_type == "foundry"
    assert target.entry_path.name == "FoundryVault.sol"
    assert target.remappings == ("@local/=src/lib/",)
    assert len(target.source_files) == 2


def test_foundry_slither_args_disable_solc_fallback_after_native_build() -> None:
    target = resolve_solidity_target(Path("tests/fixtures/solidity_projects/foundry"))

    native_args = slither_command_args_for_target(target, force_framework_solc=False)
    fallback_args = slither_command_args_for_target(target, force_framework_solc=True)

    assert "--compile-force-framework" not in native_args
    assert fallback_args[-2:] == ["--compile-force-framework", "solc"]


def test_resolve_hardhat_project() -> None:
    target = resolve_solidity_target(Path("tests/fixtures/solidity_projects/hardhat"))

    assert target.project_type == "hardhat"
    assert target.entry_path.name == "HardhatVault.sol"
    assert len(target.source_files) == 2


def test_hardhat_slither_args_include_custom_artifact_paths(tmp_path: Path) -> None:
    project = tmp_path / "hardhat"
    contracts = project / "contracts"
    contracts.mkdir(parents=True)
    (project / "hardhat.config.ts").write_text(
        """
        export default {
          paths: {
            artifacts: "build/artifacts",
            cache: "build/cache",
            sources: "contracts"
          }
        };
        """,
        encoding="utf-8",
    )
    (project / "package.json").write_text(
        '{"devDependencies": {"hardhat": "^2.0.0"}}',
        encoding="utf-8",
    )
    (contracts / "Vault.sol").write_text(
        "pragma solidity ^0.8.19;\ncontract Vault {}\n",
        encoding="utf-8",
    )

    target = resolve_solidity_target(project)
    args = slither_command_args_for_target(target, force_framework_solc=False)

    assert "--hardhat-artifacts-directory" in args
    assert args[args.index("--hardhat-artifacts-directory") + 1] == "build/artifacts"
    assert "--hardhat-cache-directory" in args
    assert args[args.index("--hardhat-cache-directory") + 1] == "build/cache"


def test_hardhat_slither_args_ignore_external_artifact_paths(tmp_path: Path) -> None:
    project = tmp_path / "hardhat"
    contracts = project / "contracts"
    contracts.mkdir(parents=True)
    (project / "hardhat.config.ts").write_text(
        """
        export default {
          external: {
            contracts: [{ artifacts: "./temp-artifacts" }]
          }
        };
        """,
        encoding="utf-8",
    )
    (project / "package.json").write_text(
        '{"devDependencies": {"hardhat": "^2.0.0"}}',
        encoding="utf-8",
    )
    (contracts / "Vault.sol").write_text(
        "pragma solidity ^0.8.19;\ncontract Vault {}\n",
        encoding="utf-8",
    )

    target = resolve_solidity_target(project)
    args = slither_command_args_for_target(target, force_framework_solc=False)

    assert "--hardhat-artifacts-directory" not in args


def test_resolve_nested_import_project() -> None:
    target = resolve_solidity_target(Path("tests/fixtures/solidity_projects/nested"))

    assert target.project_type == "generic_project"
    assert target.entry_path.name == "NestedVault.sol"
    assert len(target.source_files) == 3


def test_single_file_input_does_not_include_sibling_contracts(tmp_path: Path) -> None:
    contract = tmp_path / "A.sol"
    sibling = tmp_path / "B.sol"
    contract.write_text("pragma solidity ^0.8.19;\ncontract A {}\n", encoding="utf-8")
    sibling.write_text(
        "pragma solidity ^0.8.19;\n" + "\n".join("contract B {}" for _ in range(600)),
        encoding="utf-8",
    )

    target = resolve_solidity_target(contract)

    assert target.input_kind == "single_file"
    assert target.source_files == (contract.resolve(),)
    report = analyze_contract(
        contract,
        output_dir=tmp_path / "reports",
        slither_runner=lambda _: SlitherRunResult(
            raw_json={"results": {"detectors": []}},
            solc_version="0.8.19",
            slither_version="0.11.5",
            warnings=[],
        ),
    )
    assert report.overall_status == "no_finding"


def test_analyze_project_directory_records_input_metadata(tmp_path: Path) -> None:
    project = Path("tests/fixtures/solidity_projects/foundry")
    runner_inputs = []

    def fake_slither(path: Path) -> SlitherRunResult:
        runner_inputs.append(path)
        return SlitherRunResult(
            raw_json={
                "results": {
                    "detectors": [
                        {
                            "check": "reentrancy-eth",
                            "description": "External call before state update",
                            "elements": [
                                {
                                    "type": "function",
                                    "name": "withdraw",
                                    "source_mapping": {
                                        "lines": [7, 8, 9, 10],
                                        "filename_relative": "src/FoundryVault.sol",
                                    },
                                }
                            ],
                        }
                    ]
                }
            },
            solc_version="0.8.34",
            slither_version="0.11.5",
            warnings=[],
        )

    report = analyze_contract(
        project,
        output_dir=tmp_path / "reports",
        dataset_chunks=Path("data/dataset_v1.0/chunks/chunks.jsonl"),
        slither_runner=fake_slither,
    )

    assert report.overall_status == "finding"
    assert report.review_status == "pending_human_review"
    assert report.analysis_metadata.input_kind == "project_directory"
    assert report.analysis_metadata.project_type == "foundry"
    assert report.analysis_metadata.source_files_count == 2
    assert runner_inputs == [project.resolve()]


def test_slither_project_fixtures_compile_and_detect_reentrancy() -> None:
    for fixture in ("foundry", "hardhat", "nested"):
        project = Path("tests/fixtures/solidity_projects") / fixture
        try:
            result = run_slither(project)
        except SlitherRunError as exc:
            raise AssertionError(f"{fixture} Slither run failed: {exc}") from exc

        normalized = normalize_slither_json(result.raw_json, project)
        assert result.raw_json.get("success") is True
        assert any(finding.detector_name == "reentrancy-eth" for finding in normalized.findings)
