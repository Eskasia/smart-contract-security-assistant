from __future__ import annotations

from .common import base_result, source_node_id

RULE_ID = "scsa.multi_tool_consensus_scorer.v1"


def evaluate_consensus(finding, sibling_findings) -> dict:
    matching_tools = {
        sibling.static_tool_source
        for sibling in sibling_findings
        if sibling.vulnerability_type == finding.vulnerability_type
        and sibling.location.file == finding.location.file
        and sibling.location.line_start == finding.location.line_start
        and sibling.location.line_end == finding.location.line_end
    }
    static_signal = 0.45 if finding.static_tool_source else 0.0
    multi_tool_agreement = 0.20 if len(matching_tools) >= 2 else 0.0
    source_pattern_confirmation = 0.15 if finding.evidence else 0.0
    negative_evidence_penalty = 0.0
    final = min(
        1.0,
        static_signal
        + multi_tool_agreement
        + source_pattern_confirmation
        + negative_evidence_penalty,
    )
    status = "confirmed_by_evidence" if multi_tool_agreement else "single_tool_signal"
    return base_result(
        rule_id=RULE_ID,
        status=status,
        confidence_delta=0.08 if multi_tool_agreement else 0.0,
        summary="Confidence is decomposed across static signal, consensus, and source evidence.",
        evidence_nodes=[source_node_id(finding)],
        confidence_breakdown={
            "static_signal": static_signal,
            "multi_tool_agreement": multi_tool_agreement,
            "source_pattern_confirmation": source_pattern_confirmation,
            "negative_evidence_penalty": negative_evidence_penalty,
            "final": final,
        },
    )
