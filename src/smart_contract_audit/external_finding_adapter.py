from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ExternalToolResult, Finding, Location
from .solidity_target import SolidityTarget
from .trace.store import TraceStore

MYTHRIL_SWC_MAPPING = {
    "SWC-104": ("unchecked_external_call", 2),
    "SWC-105": ("access_control", 3),
    "SWC-106": ("access_control", 3),
    "SWC-107": ("reentrancy", 3),
    "SWC-112": ("dangerous_delegatecall", 3),
    "SWC-115": ("privilege_escalation", 3),
    "SWC-116": ("price_manipulation", 2),
    "SWC-120": ("oracle", 2),
    "SWC-132": ("price_manipulation", 2),
}


def external_findings_from_results(
    results: list[ExternalToolResult],
    target: SolidityTarget,
    start_index: int,
) -> list[Finding]:
    findings: list[Finding] = []
    next_index = start_index
    for result in results:
        if result.tool_name not in {"mythril", "echidna"} or not result.output_path:
            continue
        path = Path(result.output_path)
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if result.tool_name == "mythril":
            parsed = normalize_mythril_output(payload, target, next_index)
        else:
            parsed = normalize_echidna_output(payload, target, next_index)
        findings.extend(parsed)
        next_index += len(parsed)
    return findings


def normalize_mythril_output(
    payload: object,
    target: SolidityTarget,
    start_index: int = 1,
) -> list[Finding]:
    issues = _mythril_issues(payload)
    findings: list[Finding] = []
    for offset, issue in enumerate(issues):
        swc_id = str(issue.get("swc-id") or issue.get("swcID") or "Mythril")
        vulnerability_type, default_severity = _classify_mythril_issue(issue, swc_id)
        severity = _severity(issue.get("severity"), default_severity)
        title = str(issue.get("title") or issue.get("check") or "Mythril issue")
        description = str(issue.get("description") or issue.get("debug") or "")
        location = _mythril_location(issue, target)
        findings.append(
            Finding(
                finding_id=f"f_{start_index + offset:03d}",
                vulnerability_type=vulnerability_type,
                severity=severity,
                location=location,
                evidence=_join_text(title, description),
                reference=[swc_id] if swc_id.startswith("SWC-") else ["Mythril"],
                finding_confidence=_confidence_for_severity(severity),
                explanation_confidence=0.6,
                explanation=_join_text(
                    "Mythril reported this issue.",
                    description or title,
                ),
                attack_path="Review the Mythril issue path and source location.",
                fix_suggestion="Apply the SWC-specific mitigation and rerun Slither/Mythril.",
                remediation_code="",
                vulnerable_code="",
                static_tool_source="mythril",
                detector_name=f"mythril:{swc_id}",
            )
        )
    return findings


def normalize_echidna_output(
    payload: object,
    target: SolidityTarget,
    start_index: int = 1,
) -> list[Finding]:
    failures = _echidna_failures(payload)
    findings: list[Finding] = []
    for offset, failure in enumerate(failures):
        test_name = _echidna_test_name(failure, offset)
        status = str(failure.get("status") or "failed")
        error = str(failure.get("error") or failure.get("message") or "")
        transactions = failure.get("transactions") or failure.get("sequence") or []
        transaction_text = _join_text("Replay:", json.dumps(transactions, ensure_ascii=False))
        findings.append(
            Finding(
                finding_id=f"f_{start_index + offset:03d}",
                vulnerability_type="invariant_violation",
                severity=2,
                location=_echidna_location(failure, target),
                evidence=_join_text(test_name, status, error, transaction_text),
                reference=["Echidna"],
                finding_confidence=0.7,
                explanation_confidence=0.55,
                explanation=_join_text(
                    "Echidna falsified a property or invariant.",
                    error or test_name,
                ),
                attack_path=(
                    "Replay the Echidna transaction sequence and inspect the broken "
                    "invariant."
                ),
                fix_suggestion=(
                    "Constrain the failing state transition or update the invariant if "
                    "it encodes an invalid business rule."
                ),
                remediation_code="",
                vulnerable_code="",
                static_tool_source="echidna",
                detector_name=f"echidna:{test_name}",
            )
        )
    return findings


def merge_external_findings(
    existing_findings: list[Finding],
    external_findings: list[Finding],
) -> list[Finding]:
    merged = list(existing_findings)
    next_index = len(merged) + 1
    for finding in external_findings:
        if _duplicates_existing(finding, merged):
            continue
        finding.finding_id = f"f_{next_index:03d}"
        next_index += 1
        merged.append(finding)
    return merged


def record_external_findings(
    findings: list[Finding],
    trace_store: TraceStore,
    trace_id: str,
) -> None:
    for finding in findings:
        trace_store.record_finding(
            trace_id=trace_id,
            finding_id=finding.finding_id,
            detector_name=finding.detector_name,
            rag_mode="external_tool",
            retrieval_duration_ms=0,
            llm_duration_ms=0,
            chunks_used=0,
            slither_raw={"tool": finding.static_tool_source},
            normalized_finding=finding.to_dict(),
            rag_chunk_ids=[],
            packed_prompt="",
            llm_raw_output=None,
            schema_valid=True,
            partial=finding.partial,
        )


def _mythril_issues(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        issues = payload.get("issues")
        if isinstance(issues, list):
            return [issue for issue in issues if isinstance(issue, dict)]
    if isinstance(payload, list):
        return [issue for issue in payload if isinstance(issue, dict)]
    return []


def _echidna_failures(payload: object) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            status = str(item.get("status", "")).lower()
            if status in {"failed", "fail", "falsified"}:
                failures.append(item)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    failures.reverse()
    return failures


def _echidna_test_name(failure: dict[str, Any], offset: int) -> str:
    for key in ("name", "test", "property", "function"):
        value = failure.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    contract = failure.get("contract")
    if isinstance(contract, str) and contract.strip():
        return f"{contract.strip()}_property_{offset + 1}"
    return f"property_{offset + 1}"


def _echidna_location(failure: dict[str, Any], target: SolidityTarget) -> Location:
    file_name = str(failure.get("filename") or failure.get("file") or target.entry_path)
    line = _line_number(failure) or 1
    return Location(
        file=file_name,
        function=_echidna_test_name(failure, 0),
        line_start=line,
        line_end=line,
    )


def _classify_mythril_issue(issue: dict[str, Any], swc_id: str) -> tuple[str, int]:
    if swc_id in MYTHRIL_SWC_MAPPING:
        return MYTHRIL_SWC_MAPPING[swc_id]
    text = " ".join(str(issue.get(key, "")) for key in ("title", "description")).lower()
    if "reentr" in text:
        return "reentrancy", 3
    if "delegatecall" in text:
        return "dangerous_delegatecall", 3
    if "tx.origin" in text or "authorization" in text:
        return "privilege_escalation", 3
    if "unchecked" in text or "return value" in text:
        return "unchecked_external_call", 2
    return "mythril_issue", 2


def _severity(value: object, default: int) -> int:
    severity = str(value or "").lower()
    if severity in {"critical", "high"}:
        return 3
    if severity == "medium":
        return 2
    if severity in {"low", "informational", "info"}:
        return 1
    return default


def _confidence_for_severity(severity: int) -> float:
    if severity >= 3:
        return 0.85
    if severity == 2:
        return 0.75
    return 0.6


def _mythril_location(issue: dict[str, Any], target: SolidityTarget) -> Location:
    location = _first_location(issue)
    file_name = str(
        location.get("filename")
        or location.get("file")
        or location.get("source")
        or target.entry_path
    )
    line = _line_number(location) or _line_number(issue) or 1
    return Location(file=file_name, function=None, line_start=line, line_end=line)


def _first_location(issue: dict[str, Any]) -> dict[str, Any]:
    locations = issue.get("locations")
    if isinstance(locations, list):
        for location in locations:
            if isinstance(location, dict):
                return location
    return {}


def _line_number(data: dict[str, Any]) -> int | None:
    for key in ("line", "lineno", "line_start", "lineStart"):
        value = data.get(key)
        if isinstance(value, int):
            return max(1, value)
        if isinstance(value, str) and value.isdigit():
            return max(1, int(value))
    return None


def _duplicates_existing(finding: Finding, existing_findings: list[Finding]) -> bool:
    for existing in existing_findings:
        if existing.vulnerability_type != finding.vulnerability_type:
            continue
        if Path(existing.location.file).name != Path(finding.location.file).name:
            continue
        if _line_ranges_overlap(existing, finding):
            return True
    return False


def _line_ranges_overlap(left: Finding, right: Finding) -> bool:
    if left.location.line_start <= 1 or right.location.line_start <= 1:
        return False
    return (
        left.location.line_start <= right.location.line_end
        and right.location.line_start <= left.location.line_end
    )


def _join_text(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())
