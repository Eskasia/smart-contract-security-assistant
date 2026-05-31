from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def suggest_formal_properties(
    finding: Any,
    *,
    output_format: str = "foundry_invariant",
) -> list[dict[str, Any]]:
    function_name = finding.location.function or "target"
    property_text = _property_text(finding.vulnerability_type, function_name, output_format)
    return [
        {
            "property_id": f"property:{finding.finding_id}:001",
            "finding_id": finding.finding_id,
            "format": output_format,
            "status": "draft",
            "property_text": property_text,
            "compile_status": "not_checked",
            "verification_status": "not_proven",
            "supported_by": _support_nodes(finding),
            "review_notes": "Reviewer must adapt this draft before relying on it.",
        }
    ]


def suggest_properties_for_report(
    *,
    report_path: Path,
    output_dir: Path,
    output_format: str,
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    suggestions: list[dict[str, Any]] = []
    for finding in report.get("findings", []):
        suggestions.extend(_suggest_from_dict(finding, output_format=output_format))
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"property_count": len(suggestions), "properties": suggestions}
    (output_dir / "property_suggestions.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "property_suggestions.md").write_text(
        _render_property_markdown(suggestions),
        encoding="utf-8",
    )
    return payload


def _suggest_from_dict(finding: dict[str, Any], *, output_format: str) -> list[dict[str, Any]]:
    finding_id = str(finding.get("finding_id", "finding"))
    location = finding.get("location", {})
    function_name = str(location.get("function") or "target")
    source_node = (
        f"source:{str(location.get('file', 'unknown')).replace(' ', '_')}:"
        f"{location.get('line_start', 0)}-{location.get('line_end', 0)}"
    )
    return [
        {
            "property_id": f"property:{finding_id}:001",
            "finding_id": finding_id,
            "format": output_format,
            "status": "draft",
            "property_text": _property_text(
                str(finding.get("vulnerability_type", "generic")),
                function_name,
                output_format,
            ),
            "compile_status": "not_checked",
            "verification_status": "not_proven",
            "supported_by": [f"finding:{finding_id}", source_node],
            "review_notes": "Reviewer must adapt this draft before relying on it.",
        }
    ]


def _property_text(vulnerability_type: str, function_name: str, output_format: str) -> str:
    if output_format in {"foundry-invariant", "foundry_invariant"}:
        if vulnerability_type == "reentrancy":
            return (
                "function invariant_totalAssetsCoverBalances() public { "
                "// draft: assert vault assets remain >= recorded balances after "
                f"{function_name} fuzz sequences; }}"
            )
        if vulnerability_type in {"access_control", "privilege_escalation"}:
            return (
                "function invariant_privilegedCallsRequireAuthorizedActor() public { "
                "// draft: unauthorized callers must not change protected state via "
                f"{function_name}; }}"
            )
        return (
            "function invariant_reportedPathPreservesSecurityProperty() public { "
            f"// draft: adapt to the reported {function_name} path; }}"
        )
    return f"draft property for {function_name}; status: not_proven"


def _render_property_markdown(suggestions: list[dict[str, Any]]) -> str:
    lines = ["# Formal Property Suggestions", ""]
    if not suggestions:
        lines.append("No property suggestions were generated.")
    for suggestion in suggestions:
        lines.extend(
            [
                f"## {suggestion['property_id']}",
                "",
                f"- Finding: `{suggestion['finding_id']}`",
                f"- Format: `{suggestion['format']}`",
                f"- Status: `{suggestion['status']}`",
                f"- Verification: `{suggestion['verification_status']}`",
                "",
                "```solidity",
                suggestion["property_text"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _support_nodes(finding: Any) -> list[str]:
    return [
        f"finding:{finding.finding_id}",
        (
            f"source:{str(finding.location.file).replace(' ', '_')}:"
            f"{finding.location.line_start}-{finding.location.line_end}"
        ),
    ]
