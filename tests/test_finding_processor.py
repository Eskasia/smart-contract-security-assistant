from pathlib import Path

from smart_contract_audit.finding_processor import process_slither_findings
from smart_contract_audit.models import RagChunk
from smart_contract_audit.rag.indexer import write_chunks
from smart_contract_audit.solidity_target import resolve_solidity_target
from smart_contract_audit.trace.store import TraceStore


def test_process_slither_findings_enriches_findings_and_records_trace(tmp_path: Path) -> None:
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
                content="Reentrancy happens when ETH is sent before state is updated.",
                token_count=12,
                created_at="2026-04-29",
                sha256="abc",
            )
        ],
        chunks_path,
    )
    raw_slither = {
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
    }

    target = resolve_solidity_target(contract)
    with TraceStore(tmp_path / "trace.sqlite") as trace_store:
        trace_id = trace_store.create_trace(
            contract_id="contract_001",
            solc_version=None,
            slither_version=None,
            model_version="fallback",
            dataset_version="dataset_v1",
            initial_rag_mode="fallback",
            review_status="pending_human_review",
        )
        result = process_slither_findings(
            raw_slither=raw_slither,
            target=target,
            dataset_chunks=chunks_path,
            initial_rag_mode="fallback",
            model_path=None,
            trace_store=trace_store,
            trace_id=trace_id,
            started_at=0.0,
            clock=lambda: 1.0,
        )

        rows = trace_store.conn.execute(
            "SELECT finding_id, chunks_used, schema_valid FROM trace_findings"
        ).fetchall()

    assert result.current_rag_mode == "fallback"
    assert len(result.findings) == 1
    assert result.findings[0].finding_id == "f_001"
    assert "call{value: amount}" in result.findings[0].vulnerable_code
    assert result.findings[0].total_tokens > 0
    assert rows == [("f_001", 1, 1)]
