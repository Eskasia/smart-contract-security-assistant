from __future__ import annotations

from .common import base_result, evidence_text, has_access_guard, source_node_id

RULE_ID = "scsa.auth_sensitive_state_write.v1"
SENSITIVE_MARKERS = (
    "owner",
    "admin",
    "implementation",
    "treasury",
    "oracle",
    "fee",
    "router",
)


def evaluate_auth_sensitive_write(finding) -> dict:
    text = evidence_text(finding)
    type_match = finding.vulnerability_type in {
        "access_control",
        "privilege_escalation",
        "upgrade_risk",
    }
    public_entry = " public " in f" {text} " or " external " in f" {text} "
    sensitive_name = any(marker in text for marker in SENSITIVE_MARKERS)
    assignment = "=" in text or "transfer(" in text or ".call" in text
    if (
        (type_match or (public_entry and sensitive_name))
        and assignment
        and not has_access_guard(text)
    ):
        return base_result(
            rule_id=RULE_ID,
            status="confirmed_by_evidence",
            confidence_delta=0.12,
            summary="Public/external flow touches sensitive state without visible access guard.",
            evidence_nodes=[source_node_id(finding)],
        )
    if type_match:
        return base_result(
            rule_id=RULE_ID,
            status="needs_review",
            confidence_delta=0.03,
            summary="Authorization-sensitive type needs reviewer confirmation.",
            evidence_nodes=[source_node_id(finding)],
        )
    return base_result(rule_id=RULE_ID, status="not_applicable")
