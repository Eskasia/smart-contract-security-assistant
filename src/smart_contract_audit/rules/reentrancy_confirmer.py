from __future__ import annotations

from .common import base_result, evidence_text, source_node_id

RULE_ID = "scsa.reentrancy.evidence_confirmer.v1"


def evaluate_reentrancy(finding) -> dict:
    text = evidence_text(finding)
    is_reentrancy = finding.vulnerability_type == "reentrancy"
    call_index = _first_index(text, (".call", "call{value", "send(", "transfer("))
    compact = text.replace(" ", "")
    write_index = _first_index(
        compact,
        ("balances[msg.sender]=0", "balance[msg.sender]=0", "=0", "-="),
    )
    guarded = "nonreentrant" in text
    if (
        is_reentrancy
        and call_index >= 0
        and write_index >= 0
        and call_index < write_index
        and not guarded
    ):
        return base_result(
            rule_id=RULE_ID,
            status="confirmed_by_evidence",
            confidence_delta=0.15,
            summary="External value transfer appears before state update without a guard.",
            evidence_nodes=[source_node_id(finding)],
        )
    if is_reentrancy:
        return base_result(
            rule_id=RULE_ID,
            status="needs_review",
            confidence_delta=0.02,
            summary="Reentrancy type is present but source-order evidence is incomplete.",
            evidence_nodes=[source_node_id(finding)],
        )
    return base_result(rule_id=RULE_ID, status="not_applicable")


def _first_index(text: str, needles: tuple[str, ...]) -> int:
    positions = [text.find(needle) for needle in needles if text.find(needle) >= 0]
    return min(positions) if positions else -1
