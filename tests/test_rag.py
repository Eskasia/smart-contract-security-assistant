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
    assert loaded[0].source_path == str(report)
    assert loaded[0].section_title == "High Reentrancy"
    assert retrieved
    assert retrieved[0].vuln_type == "reentrancy"


def test_chunker_labels_expanded_web50_categories(tmp_path: Path) -> None:
    report = tmp_path / "oracle.md"
    report.write_text(
        """
        # Oracle Price Manipulation

        The protocol reads a stale price feed without checking Chainlink update time.
        A privileged owner can also upgrade the proxy implementation.
        """,
        encoding="utf-8",
    )

    chunks = chunk_document(report)

    assert chunks[0].vuln_type == "oracle"
    assert chunks[0].eligible_for_eval is True
    assert chunks[0].section_title == "Oracle Price Manipulation"
