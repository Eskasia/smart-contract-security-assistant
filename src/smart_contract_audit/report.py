from __future__ import annotations

import json
from pathlib import Path

from .models import AnalysisReport


def write_json_report(report: AnalysisReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_markdown_report(report: AnalysisReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Smart Contract Security Report",
        "",
        f"- Contract ID: `{report.contract_id}`",
        f"- Status: `{report.overall_status}`",
        f"- Human review required: `{report.requires_human_review}`",
        f"- Business logic review required: `{report.business_logic_review_required}`",
        f"- Review reason: {report.review_reason}",
        "",
        "## Findings",
        "",
    ]

    if not report.findings:
        lines.append("No mapped Slither findings were included in the formal report.")
    else:
        for finding in report.findings:
            lines.extend(
                [
                    f"### {finding.finding_id}: {finding.vulnerability_type}",
                    "",
                    f"- Severity: `{finding.severity}`",
                    f"- Detector: `{finding.detector_name}`",
                    f"- Location: `{finding.location.file}:{finding.location.line_start}`",
                    f"- Finding confidence: `{finding.finding_confidence:.2f}`",
                    f"- Explanation confidence: `{finding.explanation_confidence:.2f}`",
                    "",
                    "Evidence:",
                    "",
                    finding.evidence,
                    "",
                    "Explanation:",
                    "",
                    finding.explanation or "Deterministic finding only.",
                    "",
                    "Attack path:",
                    "",
                    finding.attack_path or "Not generated.",
                    "",
                    "Fix suggestion:",
                    "",
                    finding.fix_suggestion or "Not generated.",
                    "",
                ]
            )

    output_path.write_text("\n".join(lines), encoding="utf-8")
