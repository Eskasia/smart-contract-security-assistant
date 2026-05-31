from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from .rules import apply_native_rules

NODE_TYPES = frozenset(
    {
        "contract",
        "function",
        "state_variable",
        "modifier",
        "external_call",
        "source_range",
        "tool_signal",
        "normalized_finding",
        "trace_row",
        "rag_chunk",
        "llm_claim",
        "review_action",
        "standard_ref",
        "rule_result",
        "exploit_validation",
        "fuzz_seed",
        "formal_property",
        "defi_profit_signal",
    }
)
EDGE_TYPES = frozenset(
    {
        "contains",
        "calls",
        "writes",
        "reads",
        "emits",
        "protects",
        "reports",
        "normalizes_to",
        "supports",
        "contradicts",
        "maps_to",
        "reviewed_as",
        "validates",
        "suggests",
        "observes",
    }
)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class EvidenceNode:
    node_id: str
    node_type: str
    label: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=_now)

    def to_row(self) -> tuple[str, str, str, dict[str, Any], str]:
        return self.node_id, self.node_type, self.label, self.payload, self.created_at


@dataclass(frozen=True)
class EvidenceEdge:
    edge_id: str
    src_node_id: str
    dst_node_id: str
    edge_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_row(self) -> tuple[str, str, str, str, dict[str, Any], str]:
        return (
            self.edge_id,
            self.src_node_id,
            self.dst_node_id,
            self.edge_type,
            self.payload,
            self.created_at,
        )


@dataclass(frozen=True)
class EvidenceClaim:
    claim_id: str
    finding_id: str
    claim_text: str
    support_node_ids: list[str]
    groundedness_status: str
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceGraph:
    nodes: list[EvidenceNode]
    edges: list[EvidenceEdge]
    claims: list[EvidenceClaim]
    summary: dict[str, Any]


def attach_evidence_graphs(findings, trace_store, trace_id: str) -> None:
    all_findings = list(findings)
    for finding in all_findings:
        finding.native_rule_results = apply_native_rules(finding, all_findings)
        rag_chunk_ids = trace_store.get_finding_rag_chunk_ids(trace_id, finding.finding_id)
        graph = build_evidence_graph(
            finding=finding,
            trace_id=trace_id,
            rag_chunk_ids=rag_chunk_ids,
            rule_results=finding.native_rule_results,
        )
        finding.evidence_graph = graph.summary
        trace_store.record_evidence_graph(graph)
        trace_store.update_finding_normalized_data(
            trace_id,
            finding.finding_id,
            finding.to_dict(),
        )


def build_evidence_graph(
    *,
    finding,
    trace_id: str,
    rag_chunk_ids: list[str] | tuple[str, ...],
    rule_results: list[dict[str, Any]],
) -> EvidenceGraph:
    root_id = f"finding:{finding.finding_id}"
    source_id = source_node_id(finding)
    tool_id = tool_signal_node_id(finding)
    trace_row_id = f"trace_row:{trace_id}:{finding.finding_id}"
    review_id = f"review_action:{finding.finding_id}:{finding.review_status}"
    nodes = [
        EvidenceNode(root_id, "normalized_finding", finding.finding_id, finding.to_dict()),
        EvidenceNode(
            source_id,
            "source_range",
            f"{finding.location.file}:{finding.location.line_start}-{finding.location.line_end}",
            finding.location.to_dict(),
        ),
        EvidenceNode(
            tool_id,
            "tool_signal",
            f"{finding.static_tool_source}:{finding.detector_name}",
            {
                "tool": finding.static_tool_source,
                "detector_name": finding.detector_name,
                "evidence": finding.evidence,
            },
        ),
        EvidenceNode(
            trace_row_id,
            "trace_row",
            trace_id,
            {"trace_id": trace_id, "finding_id": finding.finding_id},
        ),
        EvidenceNode(
            review_id,
            "review_action",
            finding.review_status,
            {"review_status": finding.review_status, "review_note": finding.review_note},
        ),
    ]
    edges = [
        EvidenceEdge(_edge_id(tool_id, root_id, "reports"), tool_id, root_id, "reports"),
        EvidenceEdge(_edge_id(root_id, source_id, "supports"), root_id, source_id, "supports"),
        EvidenceEdge(
            _edge_id(root_id, trace_row_id, "supports"),
            root_id,
            trace_row_id,
            "supports",
        ),
        EvidenceEdge(
            _edge_id(root_id, review_id, "reviewed_as"),
            root_id,
            review_id,
            "reviewed_as",
        ),
    ]

    standard_nodes: list[str] = []
    for ref in finding.to_dict().get("standard_refs", []):
        if not isinstance(ref, dict):
            continue
        standard_id = (
            f"standard_ref:{_safe_id(str(ref.get('standard', 'std')))}:"
            f"{_safe_id(str(ref.get('id', 'unknown')))}"
        )
        standard_nodes.append(standard_id)
        nodes.append(
            EvidenceNode(
                standard_id,
                "standard_ref",
                str(ref.get("id", "unknown")),
                ref,
            )
        )
        edges.append(
            EvidenceEdge(
                _edge_id(root_id, standard_id, "maps_to"),
                root_id,
                standard_id,
                "maps_to",
            )
        )

    rag_nodes: list[str] = []
    for chunk_id in rag_chunk_ids:
        node_id = f"rag_chunk:{_safe_id(chunk_id)}"
        rag_nodes.append(node_id)
        nodes.append(EvidenceNode(node_id, "rag_chunk", chunk_id, {"chunk_id": chunk_id}))
        edges.append(
            EvidenceEdge(
                _edge_id(root_id, node_id, "supports"),
                root_id,
                node_id,
                "supports",
            )
        )

    rule_nodes: list[str] = []
    for result in rule_results:
        rule_id = str(result.get("rule_id", "unknown"))
        node_id = f"rule_result:{_safe_id(rule_id)}:{finding.finding_id}"
        rule_nodes.append(node_id)
        nodes.append(EvidenceNode(node_id, "rule_result", rule_id, result))
        edges.append(
            EvidenceEdge(
                _edge_id(node_id, root_id, "supports"),
                node_id,
                root_id,
                "supports",
            )
        )

    advanced_nodes = _advanced_output_nodes(finding)
    for node in advanced_nodes:
        nodes.append(node)
        edges.append(
            EvidenceEdge(
                _edge_id(root_id, node.node_id, "supports"),
                root_id,
                node.node_id,
                "supports",
            )
        )

    claims = _claims_for_finding(finding, [source_id, tool_id, *rag_nodes])
    claim_nodes: list[str] = []
    for claim in claims:
        claim_nodes.append(claim.claim_id)
        nodes.append(
            EvidenceNode(
                claim.claim_id,
                "llm_claim",
                claim.claim_text[:80],
                claim.to_dict(),
            )
        )
        edges.append(
            EvidenceEdge(
                _edge_id(root_id, claim.claim_id, "supports"),
                root_id,
                claim.claim_id,
                "supports",
            )
        )
        for support_id in claim.support_node_ids:
            edges.append(
                EvidenceEdge(
                    _edge_id(claim.claim_id, support_id, "supports"),
                    claim.claim_id,
                    support_id,
                    "supports",
                )
            )

    summary = {
        "nodes_path": "analysis_trace.sqlite:evidence_nodes",
        "edges_path": "analysis_trace.sqlite:evidence_edges",
        "claims_path": "analysis_trace.sqlite:evidence_claims",
        "root_finding_node_id": root_id,
        "source_nodes": [source_id],
        "tool_signal_nodes": [tool_id],
        "rag_chunk_nodes": rag_nodes,
        "claim_nodes": claim_nodes,
        "rule_nodes": rule_nodes,
        "advanced_nodes": [node.node_id for node in advanced_nodes],
        "standard_nodes": standard_nodes,
        "claims": [claim.to_dict() for claim in claims],
        "rule_results": rule_results,
        "unsupported_security_claims": sum(
            1 for claim in claims if claim.groundedness_status == "unsupported"
        ),
        "groundedness_status": "supported",
    }
    return EvidenceGraph(nodes=nodes, edges=edges, claims=claims, summary=summary)


def _advanced_output_nodes(finding) -> list[EvidenceNode]:
    nodes: list[EvidenceNode] = []
    validation = getattr(finding, "exploit_validation", {}) or {}
    if validation:
        nodes.append(
            EvidenceNode(
                str(
                    validation.get("validation_id")
                    or f"exploit_validation:{finding.finding_id}:001"
                ),
                "exploit_validation",
                str(validation.get("status", "not_attempted")),
                validation,
            )
        )
    for seed in getattr(finding, "fuzz_seed_suggestions", []) or []:
        if isinstance(seed, dict):
            nodes.append(
                EvidenceNode(
                    str(seed.get("seed_id") or f"seed:{finding.finding_id}:unknown"),
                    "fuzz_seed",
                    str(seed.get("target_function", "target")),
                    seed,
                )
            )
    for prop in getattr(finding, "formal_property_suggestions", []) or []:
        if isinstance(prop, dict):
            nodes.append(
                EvidenceNode(
                    str(prop.get("property_id") or f"property:{finding.finding_id}:unknown"),
                    "formal_property",
                    str(prop.get("format", "property")),
                    prop,
                )
            )
    profit_signal = getattr(finding, "defi_profit_signal", {}) or {}
    if profit_signal:
        nodes.append(
            EvidenceNode(
                f"defi_profit_signal:{finding.finding_id}:001",
                "defi_profit_signal",
                str(profit_signal.get("status", "not_observed")),
                profit_signal,
            )
        )
    return nodes


def source_node_id(finding) -> str:
    return (
        f"source:{str(finding.location.file).replace(' ', '_')}:"
        f"{finding.location.line_start}-{finding.location.line_end}"
    )


def tool_signal_node_id(finding) -> str:
    return (
        f"tool_signal:{_safe_id(finding.static_tool_source)}:"
        f"{_safe_id(finding.detector_name)}:{finding.finding_id}"
    )


def _claims_for_finding(finding, support_node_ids: list[str]) -> list[EvidenceClaim]:
    support = support_node_ids or [source_node_id(finding)]
    claim_texts = _important_claims(finding)
    return [
        EvidenceClaim(
            claim_id=f"claim:{finding.finding_id}:{index:03d}",
            finding_id=finding.finding_id,
            claim_text=claim_text,
            support_node_ids=support,
            groundedness_status="supported",
        )
        for index, claim_text in enumerate(claim_texts, start=1)
    ]


def _important_claims(finding) -> list[str]:
    text = "\n".join(part for part in (finding.explanation, finding.attack_path) if part)
    sentences = [
        sentence.strip(" -\n\t")
        for sentence in re.split(r"(?<=[.!?])\s+|\n+|\d+\.\s*", text)
        if sentence.strip(" -\n\t")
    ]
    if sentences:
        return sentences[:3]
    return [finding.evidence[:240] or f"{finding.finding_id} has analyzer evidence."]


def _edge_id(src: str, dst: str, edge_type: str) -> str:
    return f"edge:{_safe_id(src)}:{_safe_id(edge_type)}:{_safe_id(dst)}"


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", value)
