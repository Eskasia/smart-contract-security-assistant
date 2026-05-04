from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compare_report_files(base_report_path: Path, head_report_path: Path) -> dict[str, Any]:
    base_report = _read_report(base_report_path)
    head_report = _read_report(head_report_path)
    return compare_reports(base_report, head_report)


def compare_reports(base_report: dict[str, Any], head_report: dict[str, Any]) -> dict[str, Any]:
    base_findings = _findings_by_key(base_report)
    head_findings = _findings_by_key(head_report)
    base_keys = set(base_findings)
    head_keys = set(head_findings)

    added = [head_findings[key] for key in sorted(head_keys - base_keys)]
    fixed = [base_findings[key] for key in sorted(base_keys - head_keys)]
    persistent = [head_findings[key] for key in sorted(base_keys & head_keys)]
    base_score = _score(base_report)
    head_score = _score(head_report)
    score_delta = round(head_score - base_score, 2)

    return {
        "base_contract_id": str(base_report.get("contract_id", "")),
        "head_contract_id": str(head_report.get("contract_id", "")),
        "base_security_score": base_score,
        "head_security_score": head_score,
        "security_score_delta": score_delta,
        "added_count": len(added),
        "fixed_count": len(fixed),
        "persistent_count": len(persistent),
        "high_severity_added_count": sum(1 for finding in added if _severity(finding) >= 3),
        "added_findings": added,
        "fixed_findings": fixed,
        "persistent_findings": persistent,
    }


def comparison_should_fail(
    comparison: dict[str, Any],
    fail_on_high_added: bool = False,
    fail_on_score_drop: float | None = None,
) -> bool:
    if fail_on_high_added and int(comparison["high_severity_added_count"]) > 0:
        return True
    if fail_on_score_drop is not None:
        return float(comparison["security_score_delta"]) <= -abs(fail_on_score_drop)
    return False


def render_comparison_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# Smart Contract Audit Comparison",
        "",
        f"- Base contract: `{comparison['base_contract_id']}`",
        f"- Head contract: `{comparison['head_contract_id']}`",
        f"- Base security score: `{comparison['base_security_score']:.2f}`",
        f"- Head security score: `{comparison['head_security_score']:.2f}`",
        f"- Security score delta: `{comparison['security_score_delta']:.2f}`",
        f"- Added findings: `{comparison['added_count']}`",
        f"- Fixed findings: `{comparison['fixed_count']}`",
        f"- Persistent findings: `{comparison['persistent_count']}`",
        f"- High severity added findings: `{comparison['high_severity_added_count']}`",
        "",
    ]
    lines.extend(_finding_section("Added Findings", comparison["added_findings"]))
    lines.extend(_finding_section("Fixed Findings", comparison["fixed_findings"]))
    lines.extend(_finding_section("Persistent Findings", comparison["persistent_findings"]))
    return "\n".join(lines) + "\n"


def _read_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _findings_by_key(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    findings = {}
    for raw_finding in report.get("findings", []):
        if isinstance(raw_finding, dict):
            findings[_finding_key(raw_finding)] = raw_finding
    return findings


def _finding_key(finding: dict[str, Any]) -> str:
    location = finding.get("location", {})
    if not isinstance(location, dict):
        location = {}
    return "|".join(
        [
            str(finding.get("vulnerability_type", "")),
            str(finding.get("detector_name", "")),
            Path(str(location.get("file", ""))).name,
            str(location.get("line_start", "")),
        ]
    )


def _finding_section(title: str, findings: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not findings:
        lines.extend(["None.", ""])
        return lines
    for finding in findings:
        location = finding.get("location", {})
        if not isinstance(location, dict):
            location = {}
        lines.extend(
            [
                f"- `{finding.get('vulnerability_type', 'unknown')}` "
                f"severity `{_severity(finding)}` "
                f"at `{location.get('file', '')}:{location.get('line_start', '')}` "
                f"via `{finding.get('detector_name', '')}`",
            ]
        )
    lines.append("")
    return lines


def _score(report: dict[str, Any]) -> float:
    return round(float(report.get("security_score", 100.0)), 2)


def _severity(finding: dict[str, Any]) -> int:
    try:
        return int(finding.get("severity", 0))
    except (TypeError, ValueError):
        return 0
