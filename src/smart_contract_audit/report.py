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
        f"- Report version: `{report.report_version}`",
        f"- Contract ID: `{report.contract_id}`",
        f"- Status: `{report.overall_status}`",
        f"- Reviewer status: `{report.review_status}`",
        f"- Human review required: `{report.requires_human_review}`",
        f"- Business logic review required: `{report.business_logic_review_required}`",
        f"- Review reason: {report.review_reason}",
        f"- Trace ID: `{report.analysis_metadata.analysis_trace_id}`",
        f"- Dataset version: `{report.analysis_metadata.dataset_version}`",
        f"- Model version: `{report.analysis_metadata.model_version}`",
        f"- Prompt tokens: `{report.analysis_metadata.prompt_tokens}`",
        f"- Completion tokens: `{report.analysis_metadata.completion_tokens}`",
        f"- Total tokens: `{report.analysis_metadata.total_tokens}`",
        f"- Local judge score: `{report.analysis_metadata.local_average_judge_score:.2f}/5`",
        f"- External judge score: `{report.analysis_metadata.external_average_judge_score:.2f}/5`",
        f"- Entry path: `{report.analysis_metadata.entry_path}`",
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
                    f"- Local judge score: `{finding.local_judge_score:.2f}/5`",
                    f"- External judge score: `{finding.external_judge_score:.2f}/5`",
                    f"- Tokens: prompt `{finding.prompt_tokens}`, completion "
                    f"`{finding.completion_tokens}`, total `{finding.total_tokens}`",
                    "",
                    "Evidence:",
                    "",
                    finding.evidence,
                    "",
                    "Vulnerable code:",
                    "",
                    "```solidity",
                    finding.vulnerable_code or "Code snippet unavailable.",
                    "```",
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
                    "AI remediation code:",
                    "",
                    "```solidity",
                    finding.remediation_code or "Remediation code unavailable.",
                    "```",
                    "",
                ]
            )

    output_path.write_text("\n".join(lines), encoding="utf-8")
