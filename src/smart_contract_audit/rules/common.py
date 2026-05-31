from __future__ import annotations

from typing import Any


def base_result(
    *,
    rule_id: str,
    status: str,
    confidence_delta: float = 0.0,
    summary: str = "",
    evidence_nodes: list[str] | None = None,
    confidence_breakdown: dict[str, float] | None = None,
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "status": status,
        "confidence_delta": confidence_delta,
        "summary": summary,
        "evidence_nodes": evidence_nodes or [],
        "confidence_breakdown": confidence_breakdown or {},
    }


def source_node_id(finding) -> str:
    location = finding.location
    file_name = str(location.file).replace(" ", "_")
    return f"source:{file_name}:{location.line_start}-{location.line_end}"


def evidence_text(finding) -> str:
    return "\n".join(
        str(part)
        for part in (
            finding.vulnerability_type,
            finding.detector_name,
            finding.evidence,
            finding.vulnerable_code,
            finding.explanation,
            finding.attack_path,
        )
        if part
    ).lower()


def has_access_guard(text: str) -> bool:
    guard_markers = (
        "onlyowner",
        "onlyadmin",
        "require(msg.sender",
        "require(owner",
        "_authorizeupgrade",
        "nonreentrant",
    )
    return any(marker in text.replace(" ", "") for marker in guard_markers)
