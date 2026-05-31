import sqlite3
from pathlib import Path

from smart_contract_audit.analyzer import analyze_contract
from smart_contract_audit.models import ExternalToolResult, RagChunk
from smart_contract_audit.rag.indexer import write_chunks
from smart_contract_audit.slither_runner import SlitherRunResult


def test_analyze_contract_with_fake_slither(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text(
        """
        pragma solidity ^0.8.19;
        contract Vault {
            mapping(address => uint256) public balances;
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
    chunks_path = tmp_path / "chunks.jsonl"
    write_chunks(
        [
            RagChunk(
                chunk_id="report_001_0001",
                source_id="report_001",
                report_id="audit",
                severity=3,
                vuln_type="reentrancy",
                content="Reentrancy happens when ETH is sent before balance state is updated.",
                token_count=12,
                created_at="2026-04-29",
                sha256="abc",
            )
        ],
        chunks_path,
    )

    def fake_slither(_: Path, native_build_policy: str = "trusted") -> SlitherRunResult:
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
                                        "lines": [5, 6, 7, 8],
                                        "filename_relative": "Vault.sol",
                                    },
                                }
                            ],
                        }
                    ]
                }
            },
            solc_version="0.8.19",
            slither_version="0.10.0",
            warnings=[],
        )

    report = analyze_contract(
        contract,
        output_dir=tmp_path / "reports",
        dataset_chunks=chunks_path,
        slither_runner=fake_slither,
        external_tools=("mythril",),
        external_tool_runner=lambda *_: [
            ExternalToolResult(
                tool_name="mythril",
                command=["myth", "analyze", str(contract)],
                status="finding",
                findings_count=1,
                summary="Mythril reported 1 issue.",
            )
        ],
    )

    assert report.overall_status == "finding"
    assert report.findings[0].vulnerability_type == "reentrancy"
    assert report.findings[0].finding_confidence == 1.0
    assert "call{value: amount}" in report.findings[0].vulnerable_code
    assert "nonReentrant" in report.findings[0].remediation_code
    assert report.findings[0].local_judge_score == 5.0
    assert report.findings[0].external_judge_score == 5.0
    assert report.findings[0].total_tokens > 0
    assert report.analysis_metadata.total_tokens == report.findings[0].total_tokens
    assert report.external_tool_results[0].tool_name == "mythril"
    assert report.external_tool_results[0].findings_count == 1
    assert (tmp_path / "reports" / f"{report.contract_id}.json").exists()
    assert (tmp_path / "reports" / "analysis_trace.sqlite").exists()


def test_analyze_contract_adds_mythril_findings_to_formal_report(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text(
        "pragma solidity ^0.8.19;\ncontract Vault { function withdraw() external {} }\n",
        encoding="utf-8",
    )

    def fake_slither(_: Path, native_build_policy: str = "trusted") -> SlitherRunResult:
        return SlitherRunResult(
            raw_json={"results": {"detectors": []}},
            solc_version="0.8.19",
            slither_version="0.11.5",
            warnings=[],
        )

    def fake_external_tool_runner(
        _: Path,
        output_dir: Path,
        __: tuple[str, ...],
        ___: int,
    ) -> list[ExternalToolResult]:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "mythril.json"
        output_path.write_text(
            """
            {
              "issues": [
                {
                  "title": "External Call To User-Supplied Address",
                  "description": "An external call can lead to reentrancy.",
                  "severity": "High",
                  "swc-id": "SWC-107",
                  "locations": [{"filename": "Vault.sol", "line": 2}]
                }
              ]
            }
            """,
            encoding="utf-8",
        )
        return [
            ExternalToolResult(
                tool_name="mythril",
                command=["myth", "analyze", str(contract)],
                status="finding",
                findings_count=1,
                summary="Mythril reported 1 issue.",
                output_path=str(output_path),
            )
        ]

    report = analyze_contract(
        contract,
        output_dir=tmp_path / "reports",
        dataset_chunks=tmp_path / "missing-chunks.jsonl",
        slither_runner=fake_slither,
        external_tools=("mythril",),
        external_tool_runner=fake_external_tool_runner,
    )

    assert report.overall_status == "finding"
    assert report.findings[0].static_tool_source == "mythril"
    assert report.findings[0].vulnerability_type == "reentrancy"
    assert report.findings[0].detector_name == "mythril:SWC-107"
    with sqlite3.connect(tmp_path / "reports" / "analysis_trace.sqlite") as conn:
        row = conn.execute(
            "SELECT detector_name, rag_mode FROM trace_findings WHERE finding_id = 'f_001'"
        ).fetchone()
    assert row == ("mythril:SWC-107", "external_tool")


def test_analyze_contract_adds_echidna_failures_to_formal_report(tmp_path: Path) -> None:
    contract = tmp_path / "InvariantVault.sol"
    contract.write_text(
        "pragma solidity ^0.8.19;\ncontract InvariantVault { function withdraw() external {} }\n",
        encoding="utf-8",
    )

    def fake_slither(_: Path, native_build_policy: str = "trusted") -> SlitherRunResult:
        return SlitherRunResult(
            raw_json={"results": {"detectors": []}},
            solc_version="0.8.19",
            slither_version="0.11.5",
            warnings=[],
        )

    def fake_external_tool_runner(
        _: Path,
        output_dir: Path,
        __: tuple[str, ...],
        ___: int,
    ) -> list[ExternalToolResult]:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "echidna.json"
        output_path.write_text(
            """
            {
              "tests": [
                {
                  "contract": "InvariantVault",
                  "name": "echidna_total_assets_never_decrease",
                  "status": "failed",
                  "error": "property falsified after withdraw",
                  "transactions": [{"function": "withdraw"}]
                }
              ]
            }
            """,
            encoding="utf-8",
        )
        return [
            ExternalToolResult(
                tool_name="echidna",
                command=["echidna", str(contract), "--format", "json"],
                status="finding",
                findings_count=1,
                summary="Echidna reported 1 failed property.",
                output_path=str(output_path),
            )
        ]

    report = analyze_contract(
        contract,
        output_dir=tmp_path / "reports",
        dataset_chunks=tmp_path / "missing-chunks.jsonl",
        slither_runner=fake_slither,
        external_tools=("echidna",),
        external_tool_runner=fake_external_tool_runner,
    )

    assert report.overall_status == "finding"
    assert report.findings[0].static_tool_source == "echidna"
    assert report.findings[0].vulnerability_type == "invariant_violation"
    assert report.findings[0].detector_name == "echidna:echidna_total_assets_never_decrease"
    assert report.security_score == 91.6
    with sqlite3.connect(tmp_path / "reports" / "analysis_trace.sqlite") as conn:
        row = conn.execute(
            "SELECT detector_name, rag_mode FROM trace_findings WHERE finding_id = 'f_001'"
        ).fetchone()
    assert row == ("echidna:echidna_total_assets_never_decrease", "external_tool")


def test_analyze_contract_adds_aderyn_findings_to_formal_report(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text(
        "pragma solidity ^0.8.19;\ncontract Vault { function callTarget() external {} }\n",
        encoding="utf-8",
    )

    def fake_slither(_: Path, native_build_policy: str = "trusted") -> SlitherRunResult:
        return SlitherRunResult(
            raw_json={"results": {"detectors": []}},
            solc_version="0.8.19",
            slither_version="0.11.5",
            warnings=[],
        )

    def fake_external_tool_runner(
        _: Path,
        output_dir: Path,
        __: tuple[str, ...],
        ___: int,
    ) -> list[ExternalToolResult]:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "aderyn.json"
        output_path.write_text(
            """
            {
              "issues": [
                {
                  "title": "Unchecked return value",
                  "description": "External call return value is not checked.",
                  "severity": "High",
                  "filename": "Vault.sol",
                  "line": 2
                }
              ]
            }
            """,
            encoding="utf-8",
        )
        return [
            ExternalToolResult(
                tool_name="aderyn",
                command=["aderyn", "--output", str(output_path), str(contract)],
                status="finding",
                findings_count=1,
                summary="Aderyn reported 1 issue.",
                output_path=str(output_path),
                artifact_paths={"sarif": str(output_dir / "aderyn.sarif")},
            )
        ]

    report = analyze_contract(
        contract,
        output_dir=tmp_path / "reports",
        dataset_chunks=tmp_path / "missing-chunks.jsonl",
        slither_runner=fake_slither,
        external_tools=("aderyn",),
        external_tool_runner=fake_external_tool_runner,
    )

    assert report.overall_status == "finding"
    assert report.findings[0].static_tool_source == "aderyn"
    assert report.findings[0].vulnerability_type == "unchecked_external_call"
    assert report.external_tool_results[0].artifact_paths["sarif"].endswith("aderyn.sarif")
    with sqlite3.connect(tmp_path / "reports" / "analysis_trace.sqlite") as conn:
        row = conn.execute(
            "SELECT detector_name, rag_mode FROM trace_findings WHERE finding_id = 'f_001'"
        ).fetchone()
    assert row == ("aderyn:unchecked-return-value", "external_tool")


def test_analyze_contract_skips_halmos_without_trusted_foundry_project(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19;\ncontract Vault {}\n", encoding="utf-8")

    def fake_slither(_: Path, native_build_policy: str = "trusted") -> SlitherRunResult:
        return SlitherRunResult(
            raw_json={"results": {"detectors": []}},
            solc_version="0.8.19",
            slither_version="0.11.5",
            warnings=[],
        )

    def fake_external_tool_runner(
        _: Path,
        __: Path,
        tools: tuple[str, ...],
        ___: int,
    ) -> list[ExternalToolResult]:
        assert tools == ()
        return []

    report = analyze_contract(
        contract,
        output_dir=tmp_path / "reports",
        dataset_chunks=tmp_path / "missing-chunks.jsonl",
        slither_runner=fake_slither,
        external_tools=("halmos",),
        external_tool_runner=fake_external_tool_runner,
        native_build_policy="disabled",
    )

    assert report.overall_status == "no_finding"
    assert report.external_tool_results[0].tool_name == "halmos"
    assert report.external_tool_results[0].status == "skipped"
