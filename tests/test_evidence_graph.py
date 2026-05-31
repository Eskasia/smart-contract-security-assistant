from pathlib import Path

from smart_contract_audit.evidence_graph import attach_evidence_graphs
from smart_contract_audit.models import Finding, Location
from smart_contract_audit.trace.store import TraceStore


def test_attach_evidence_graph_records_nodes_edges_and_claims(tmp_path: Path) -> None:
    finding = _finding()
    with TraceStore(tmp_path / "trace.sqlite") as store:
        trace_id = store.create_trace(
            contract_id="contract_001",
            solc_version="0.8.34",
            slither_version="0.11.5",
            model_version="fallback",
            dataset_version="dataset_v1",
            initial_rag_mode="fallback",
            review_status="pending_human_review",
        )
        store.record_finding(
            trace_id=trace_id,
            finding_id=finding.finding_id,
            detector_name=finding.detector_name,
            rag_mode="fallback",
            retrieval_duration_ms=3,
            llm_duration_ms=4,
            chunks_used=1,
            slither_raw={"check": finding.detector_name},
            normalized_finding=finding.to_dict(),
            rag_chunk_ids=["chunk_001"],
            packed_prompt="Explain reentrancy",
            llm_raw_output={"explanation": finding.explanation},
            schema_valid=True,
        )

        attach_evidence_graphs([finding], store, trace_id)

        node_types = {
            row[0]
            for row in store.conn.execute(
                "SELECT DISTINCT node_type FROM evidence_nodes"
            ).fetchall()
        }
        edge_types = {
            row[0]
            for row in store.conn.execute(
                "SELECT DISTINCT edge_type FROM evidence_edges"
            ).fetchall()
        }
        claim_rows = store.conn.execute(
            "SELECT finding_id, groundedness_status FROM evidence_claims"
        ).fetchall()

    assert {"normalized_finding", "source_range", "tool_signal", "llm_claim"} <= node_types
    assert {"reports", "supports", "maps_to", "reviewed_as"} <= edge_types
    assert claim_rows
    assert {row[1] for row in claim_rows} == {"supported"}
    assert finding.evidence_graph["root_finding_node_id"] == "finding:f_001"
    assert finding.evidence_graph["source_nodes"]
    assert finding.evidence_graph["tool_signal_nodes"]
    assert finding.evidence_graph["claim_nodes"]
    assert finding.evidence_graph["unsupported_security_claims"] == 0


def _finding() -> Finding:
    return Finding(
        finding_id="f_001",
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(file="Vault.sol", function="withdraw", line_start=11, line_end=16),
        evidence="External call happens before balances[msg.sender] is reset.",
        reference=["SWC-107"],
        finding_confidence=0.9,
        explanation_confidence=0.8,
        explanation="The external call occurs before the balance reset.",
        attack_path="Attacker re-enters withdraw before balance is zero.",
        fix_suggestion="Move balance reset before the external call.",
        remediation_code="",
        vulnerable_code=(
            "11: function withdraw() external {\n"
            "12:   uint256 amount = balances[msg.sender];\n"
            "13:   (bool success, ) = msg.sender.call{value: amount}(\"\");\n"
            "14:   require(success);\n"
            "15:   balances[msg.sender] = 0;\n"
            "16: }"
        ),
        static_tool_source="slither",
        detector_name="reentrancy-eth",
        local_judge_score=5.0,
        external_judge_score=5.0,
    )
