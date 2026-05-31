from __future__ import annotations

from .common import base_result, evidence_text, source_node_id

RULE_ID = "scsa.unchecked_low_level_call.v1"


def evaluate_unchecked_call(finding) -> dict:
    text = evidence_text(finding)
    has_low_level_call = any(marker in text for marker in (".call", ".delegatecall", ".staticcall"))
    checked = any(
        marker in text.replace(" ", "")
        for marker in (
            "require(success",
            "assert(success",
            "if(!success",
            "if(success",
            "revert",
        )
    )
    type_match = finding.vulnerability_type == "unchecked_external_call"
    if (type_match or has_low_level_call) and has_low_level_call and not checked:
        return base_result(
            rule_id=RULE_ID,
            status="confirmed_by_evidence",
            confidence_delta=0.10,
            summary="Low-level call return value is not guarded by require/assert/revert.",
            evidence_nodes=[source_node_id(finding)],
        )
    if type_match:
        return base_result(
            rule_id=RULE_ID,
            status="needs_review",
            confidence_delta=0.02,
            summary="Unchecked-call type is present but guard evidence is ambiguous.",
            evidence_nodes=[source_node_id(finding)],
        )
    return base_result(rule_id=RULE_ID, status="not_applicable")
