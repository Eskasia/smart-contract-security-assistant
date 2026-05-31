from __future__ import annotations

from typing import Any


def evaluate_groundedness(findings) -> dict[str, Any]:
    finding_results = []
    unsupported_security_claims = 0
    claims_total = 0
    for finding in findings:
        evidence_graph = getattr(finding, "evidence_graph", {}) or {}
        claims = evidence_graph.get("claims", [])
        if not isinstance(claims, list):
            claims = []
        if not claims:
            claims = [
                {
                    "claim_id": f"claim:{finding.finding_id}:fallback",
                    "text": finding.evidence,
                    "groundedness_status": "supported" if finding.location else "unsupported",
                    "support_node_ids": evidence_graph.get("source_nodes", []),
                }
            ]
        statuses = [
            str(claim.get("groundedness_status", "unsupported"))
            for claim in claims
            if isinstance(claim, dict)
        ]
        unsupported = sum(1 for status in statuses if status in {"unsupported", "contradicted"})
        claims_total += len(statuses)
        unsupported_security_claims += unsupported
        finding_results.append(
            {
                "finding_id": finding.finding_id,
                "claims": len(statuses),
                "unsupported_security_claims": unsupported,
                "groundedness_status": "supported" if unsupported == 0 else "unsupported",
            }
        )
    return {
        "findings": finding_results,
        "claims_total": claims_total,
        "unsupported_security_claims": unsupported_security_claims,
        "groundedness_pass": unsupported_security_claims == 0,
    }
