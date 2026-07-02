from pathlib import Path

from smart_contract_audit.advanced_evidence import attach_advanced_evidence
from smart_contract_audit.evidence_graph import build_evidence_graph
from smart_contract_audit.models import Finding, Location
from smart_contract_audit.trace.store import TraceStore


def test_attach_advanced_evidence_defaults_and_trace(tmp_path: Path) -> None:
    finding = _finding()
    with TraceStore(tmp_path / "trace.sqlite") as trace_store:
        attach_advanced_evidence([finding], trace_store, "trace_001")
        attach_advanced_evidence([_finding()], trace_store, "trace_002")
        rows = trace_store.conn.execute(
            "SELECT validation_id, status, mode, triggered "
            "FROM exploit_validations WHERE finding_id = ? ORDER BY validation_id",
            (finding.finding_id,),
        ).fetchall()

    assert finding.exploit_validation["status"] == "not_attempted"
    assert finding.exploit_validation["mode"] == "sandbox_only"
    assert finding.exploit_validation["human_review_required"] is True
    assert finding.fuzz_seed_suggestions[0]["finding_id"] == finding.finding_id
    assert finding.fuzz_seed_suggestions[0]["supported_by"]
    assert finding.formal_property_suggestions[0]["status"] == "draft"
    assert finding.formal_property_suggestions[0]["verification_status"] == "not_proven"
    assert finding.defi_profit_signal["status"] == "not_observed"
    assert rows == [
        ("exploit_validation:trace_001:f_001:001", "not_attempted", "sandbox_only", None),
        ("exploit_validation:trace_002:f_001:001", "not_attempted", "sandbox_only", None),
    ]


def test_evidence_graph_records_advanced_output_nodes() -> None:
    finding = _finding()
    attach_advanced_evidence([finding])

    graph = build_evidence_graph(
        finding=finding,
        trace_id="trace_001",
        rag_chunk_ids=["chunk:001"],
        rule_results=[],
    )

    node_types = {node.node_type for node in graph.nodes}
    assert "exploit_validation" in node_types
    assert "fuzz_seed" in node_types
    assert "formal_property" in node_types
    assert "defi_profit_signal" in node_types
    assert "exploit_validation:trace_001:f_001:001" in graph.summary["advanced_nodes"]


def _finding() -> Finding:
    return Finding(
        finding_id="f_001",
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(
            file="tests/poc/reentrancy/src/VulnerableVault.sol",
            function="withdraw",
            line_start=11,
            line_end=19,
        ),
        evidence="External call before balance reset.",
        reference=["SWC-107"],
        finding_confidence=0.9,
        explanation_confidence=0.8,
        explanation="withdraw sends ETH before clearing balances.",
        attack_path="Attacker re-enters from receive().",
        fix_suggestion="Apply checks-effects-interactions.",
        remediation_code="",
        vulnerable_code="",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
    )
