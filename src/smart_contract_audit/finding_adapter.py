from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .confidence.finding_score import compute_finding_confidence
from .config import DETECTOR_MAPPING
from .models import Finding, Location


@dataclass
class AdapterResult:
    findings: list[Finding]
    unmapped: list[dict[str, Any]]


def normalize_slither_json(raw_json: dict[str, Any], contract_path: Path) -> AdapterResult:
    detectors = raw_json.get("results", {}).get("detectors", []) or []
    findings: list[Finding] = []
    unmapped: list[dict[str, Any]] = []

    for detector in detectors:
        detector_name = _detector_name(detector)
        if detector_name not in DETECTOR_MAPPING:
            unmapped.append(detector)
            continue

        vuln_type, severity, references = DETECTOR_MAPPING[detector_name]
        location = _extract_location(detector, contract_path)
        finding = Finding(
            finding_id=f"f_{len(findings) + 1:03d}",
            vulnerability_type=vuln_type,
            severity=severity,
            location=location,
            evidence=_evidence(detector),
            reference=references,
            finding_confidence=compute_finding_confidence(severity, vuln_type, []),
            explanation_confidence=0.0,
            explanation="",
            attack_path="",
            fix_suggestion="",
            remediation_code="",
            vulnerable_code="",
            static_tool_source="slither",
            detector_name=detector_name,
            partial=False,
        )
        findings.append(finding)

    return AdapterResult(findings=findings, unmapped=unmapped)


def _detector_name(detector: dict[str, Any]) -> str:
    return str(
        detector.get("check")
        or detector.get("detector")
        or detector.get("name")
        or detector.get("id")
        or "unknown"
    )


def _evidence(detector: dict[str, Any]) -> str:
    return str(detector.get("description") or detector.get("markdown") or detector)


def _extract_location(detector: dict[str, Any], contract_path: Path) -> Location:
    elements = detector.get("elements", []) or []
    lines: list[int] = []
    file_name = contract_path.name
    function_name: str | None = None

    for element in elements:
        source_mapping = element.get("source_mapping") or {}
        mapped_lines = source_mapping.get("lines") or []
        lines.extend(
            int(line)
            for line in mapped_lines
            if isinstance(line, int | str) and str(line).isdigit()
        )

        filename = (
            source_mapping.get("filename_relative")
            or source_mapping.get("filename_short")
            or source_mapping.get("filename_absolute")
        )
        if filename:
            file_name = str(filename)

        element_type = str(element.get("type") or "").lower()
        if function_name is None and "function" in element_type:
            function_name = str(element.get("name") or "")

    if not lines:
        source_mapping = detector.get("source_mapping") or {}
        mapped_lines = source_mapping.get("lines") or []
        lines.extend(
            int(line)
            for line in mapped_lines
            if isinstance(line, int | str) and str(line).isdigit()
        )

    line_start = min(lines) if lines else 1
    line_end = max(lines) if lines else line_start
    return Location(
        file=file_name, function=function_name, line_start=line_start, line_end=line_end
    )
