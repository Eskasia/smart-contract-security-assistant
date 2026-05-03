from pathlib import Path

from smart_contract_audit.analyzer import analyze_contract
from smart_contract_audit.models import RagChunk
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

    def fake_slither(_: Path) -> SlitherRunResult:
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
    assert (tmp_path / "reports" / f"{report.contract_id}.json").exists()
    assert (tmp_path / "reports" / "analysis_trace.sqlite").exists()
