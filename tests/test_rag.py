from pathlib import Path

from smart_contract_audit.rag.chunker import chunk_document
from smart_contract_audit.rag.indexer import load_chunks, write_chunks
from smart_contract_audit.rag.retriever import retrieve_chunks


def test_chunk_and_retrieve_reentrancy(tmp_path: Path) -> None:
    report = tmp_path / "audit.md"
    report.write_text(
        """
        # High Reentrancy

        The withdraw function performs an external call before updating balance.

        ```solidity
        msg.sender.call{value: amount}("");
        balances[msg.sender] = 0;
        ```
        """,
        encoding="utf-8",
    )

    chunks = chunk_document(report, source_id="report_001")
    output = tmp_path / "chunks.jsonl"
    write_chunks(chunks, output)
    loaded = load_chunks(output)
    retrieved = retrieve_chunks("reentrancy external call", loaded, "balanced")

    assert loaded
    assert retrieved
    assert retrieved[0].vuln_type == "reentrancy"
