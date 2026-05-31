from __future__ import annotations

from .common import base_result, evidence_text, has_access_guard, source_node_id

RULE_ID = "scsa.upgradeable_proxy_risk_mapper.v1"


def evaluate_proxy_risk(finding) -> dict:
    text = evidence_text(finding)
    type_match = finding.vulnerability_type in {"upgrade_risk", "dangerous_delegatecall"}
    proxy_signal = any(
        marker in text
        for marker in (
            "delegatecall",
            "implementation",
            "initializer",
            "uups",
            "proxy",
            "upgrade",
        )
    )
    if (type_match or proxy_signal) and proxy_signal and not has_access_guard(text):
        return base_result(
            rule_id=RULE_ID,
            status="confirmed_by_evidence",
            confidence_delta=0.10,
            summary="Proxy/delegatecall/upgrade evidence appears without visible guard.",
            evidence_nodes=[source_node_id(finding)],
        )
    if type_match:
        return base_result(
            rule_id=RULE_ID,
            status="needs_review",
            confidence_delta=0.02,
            summary="Upgradeability or delegatecall finding requires proxy review.",
            evidence_nodes=[source_node_id(finding)],
        )
    return base_result(rule_id=RULE_ID, status="not_applicable")
