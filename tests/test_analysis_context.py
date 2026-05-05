from pathlib import Path

from smart_contract_audit.analysis_context import (
    create_analysis_context,
    validate_analysis_target,
)
from smart_contract_audit.config import (
    MAX_PROJECT_SOLIDITY_FILES,
    MAX_PROJECT_SOLIDITY_LINES,
    MAX_SOLIDITY_LINES,
)
from smart_contract_audit.solidity_target import resolve_solidity_target


def test_create_analysis_context_handles_unresolved_input(tmp_path: Path) -> None:
    context = create_analysis_context(
        tmp_path / "Missing.sol",
        output_dir=tmp_path / "reports",
        trace_db=None,
        dataset_chunks=None,
    )

    assert context.target is None
    assert context.source == ""
    assert context.target_error is not None
    assert context.contract_id == "e3b0c44298fc"
    assert context.trace_db == tmp_path / "reports" / "analysis_trace.sqlite"
    assert context.dataset_chunks == Path("data/dataset_v1.0/chunks/chunks.jsonl")
    assert context.output_dir.exists()


def test_validate_analysis_target_rejects_oversized_single_file(tmp_path: Path) -> None:
    contract = tmp_path / "Large.sol"
    contract.write_text(
        "\n".join(["pragma solidity ^0.8.19;"] * (MAX_SOLIDITY_LINES + 1)),
        encoding="utf-8",
    )
    target = resolve_solidity_target(contract)

    assert validate_analysis_target(target) == f"Input exceeds {MAX_SOLIDITY_LINES} lines."


def test_project_limits_cover_public_repository_scale(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    for index in range(3):
        (project / f"Contract{index}.sol").write_text(
            "pragma solidity ^0.8.19;\ncontract Contract{}\n",
            encoding="utf-8",
        )
    target = resolve_solidity_target(project)

    assert MAX_PROJECT_SOLIDITY_FILES == 500
    assert MAX_PROJECT_SOLIDITY_LINES == 100_000
    assert validate_analysis_target(target) is None
