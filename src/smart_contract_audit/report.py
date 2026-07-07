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
        f"- Contract security score: `{report.security_score:.2f}/100`",
        f"- Security score formula: `{report.score_formula_version}`",
        f"- Human review required: `{report.requires_human_review}`",
        f"- Business logic review required: `{report.business_logic_review_required}`",
        f"- Review reason: {report.review_reason}",
        f"- Trace ID: `{report.analysis_metadata.analysis_trace_id}`",
        f"- Dataset version: `{report.analysis_metadata.dataset_version}`",
        f"- Model version: `{report.analysis_metadata.model_version}`",
        f"- Prompt tokens: `{report.analysis_metadata.prompt_tokens}`",
        f"- Completion tokens: `{report.analysis_metadata.completion_tokens}`",
        f"- Total tokens: `{report.analysis_metadata.total_tokens}`",
        "- Judge score meaning: report-quality completeness score, not a contract security score",
        "- Local report-quality judge score: "
        f"`{report.analysis_metadata.local_average_judge_score:.2f}/5`",
        "- External report-quality judge score: "
        f"`{report.analysis_metadata.external_average_judge_score:.2f}/5`",
        f"- Entry path: `{report.analysis_metadata.entry_path}`",
        "",
        "## External Tool Results",
        "",
    ]

    if not report.external_tool_results:
        lines.append("No optional external tools were executed.")
    else:
        for result in report.external_tool_results:
            lines.extend(
                [
                    f"- `{result.tool_name}`: `{result.status}`, "
                    f"findings `{result.findings_count}`",
                    f"  - Execution mode: `{result.execution_mode or 'unknown'}`",
                    f"  - Binary path: `{result.binary_path or 'not resolved'}`",
                    f"  - Timeout seconds: `{result.timeout_seconds}`",
                    f"  - Duration ms: `{result.duration_ms}`",
                    f"  - Summary: {result.summary}",
                    f"  - Command: `{_format_command(result.command)}`",
                    f"  - Output: `{result.output_path or 'not generated'}`",
                ]
            )
            if result.error:
                lines.append(f"  - Error: `{result.error}`")
            for artifact_name, artifact_path in result.artifact_paths.items():
                lines.append(f"  - {artifact_name.upper()} artifact: `{artifact_path}`")

    lines.extend(
        [
            "",
            "## Evidence Graph Summary",
            "",
            "- Nodes: `analysis_trace.sqlite:evidence_nodes`",
            "- Edges: `analysis_trace.sqlite:evidence_edges`",
            "- Claims: `analysis_trace.sqlite:evidence_claims`",
            "- Unsupported security claims: "
            f"`{report.evidence_graph_summary.get('unsupported_security_claims', 0)}`",
        ]
    )

    lines.extend(
        [
            "",
            "## Findings",
            "",
        ]
    )

    if not report.findings:
        lines.append("No mapped Slither findings were included in the formal report.")
    else:
        for finding in report.findings:
            finding_data = finding.to_dict()
            falsification_pack = finding_data.get("falsification_pack", {})
            finding_lines = [
                f"### {finding.finding_id}: {finding.vulnerability_type}",
                "",
                f"- Severity: `{finding.severity}`",
                f"- Detector: `{finding.detector_name}`",
                f"- Finding review status: `{finding.review_status}`",
            ]
            if finding.review_note:
                finding_lines.append(f"- Finding review note: {finding.review_note}")
            standard_refs = finding_data.get("standard_refs", [])
            finding_lines.extend(
                [
                    f"- Location: `{finding.location.file}:{finding.location.line_start}`",
                    f"- Finding confidence: `{finding.finding_confidence:.2f}`",
                    f"- Explanation confidence: `{finding.explanation_confidence:.2f}`",
                    f"- Local report-quality judge score: `{finding.local_judge_score:.2f}/5`",
                    "- External report-quality judge score: "
                    f"`{finding.external_judge_score:.2f}/5`",
                    f"- Tokens: prompt `{finding.prompt_tokens}`, completion "
                    f"`{finding.completion_tokens}`, total `{finding.total_tokens}`",
                    "- Standards: "
                    + _format_standard_refs(standard_refs),
                    "- Evidence graph root: "
                    + f"`{finding.evidence_graph.get('root_finding_node_id', 'unavailable')}`",
                    "- Groundedness: "
                    + f"`{finding.evidence_graph.get('groundedness_status', 'unavailable')}`",
                    "- Native rules: "
                    + _format_native_rules(finding.evidence_graph.get("rule_results", [])),
                    "- Exploit validation: "
                    + _format_exploit_validation(finding.exploit_validation),
                    "- Fuzz seeds: "
                    + _format_count(finding.fuzz_seed_suggestions, "seed"),
                    "- Formal properties: "
                    + _format_count(finding.formal_property_suggestions, "property"),
                    "- DeFi profit signal: "
                    + f"`{finding.defi_profit_signal.get('status', 'not_observed')}`",
                    "- Falsification checks: "
                    + _format_count(
                        falsification_pack.get("counterevidence_checks", []),
                        "check",
                    ),
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
                    "Exploit Validation:",
                    "",
                    _render_exploit_validation(finding.exploit_validation),
                    "",
                    "Fuzz Seed Suggestions:",
                    "",
                    _render_fuzz_seeds(finding.fuzz_seed_suggestions),
                    "",
                    "Formal Property Suggestions:",
                    "",
                    _render_formal_properties(finding.formal_property_suggestions),
                    "",
                    "DeFi Profit Signal:",
                    "",
                    _render_defi_profit_signal(finding.defi_profit_signal),
                    "",
                    "Falsification Pack:",
                    "",
                    _render_falsification_pack(falsification_pack),
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
            lines.extend(finding_lines)

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _format_standard_refs(standard_refs: object) -> str:
    if not isinstance(standard_refs, list) or not standard_refs:
        return "`[]`"
    formatted = []
    for ref in standard_refs:
        if not isinstance(ref, dict):
            continue
        standard = ref.get("standard")
        ref_id = ref.get("id")
        label = ref.get("label")
        if standard and ref_id and label:
            formatted.append(f"`{standard} {ref_id}` ({label})")
        elif ref_id:
            formatted.append(f"`{ref_id}`")
    return ", ".join(formatted) if formatted else "`[]`"


def _format_native_rules(rule_results: object) -> str:
    if not isinstance(rule_results, list) or not rule_results:
        return "`[]`"
    formatted = []
    for result in rule_results:
        if not isinstance(result, dict):
            continue
        rule_id = result.get("rule_id")
        status = result.get("status")
        if rule_id and status:
            formatted.append(f"`{rule_id}` ({status})")
    return ", ".join(formatted) if formatted else "`[]`"


def _format_exploit_validation(validation: object) -> str:
    if not isinstance(validation, dict) or not validation:
        return "`not_attempted`"
    status = validation.get("status", "not_attempted")
    mode = validation.get("mode", "sandbox_only")
    human_review = validation.get("human_review_required", True)
    return f"`{status}` / `{mode}` / human review `{human_review}`"


def _format_command(command: list[str]) -> str:
    return " ".join(command) if command else "not run"


def _format_count(items: object, label: str) -> str:
    if not isinstance(items, list):
        return "`0`"
    return f"`{len(items)}` {label}{'' if len(items) == 1 else 's'}"


def _render_exploit_validation(validation: object) -> str:
    if not isinstance(validation, dict) or not validation:
        return "Status: `not_attempted`"
    lines = [
        f"Status: `{validation.get('status', 'not_attempted')}`",
        f"Mode: `{validation.get('mode', 'sandbox_only')}`",
        f"Triggered: `{validation.get('triggered')}`",
        f"Human review required: `{validation.get('human_review_required', True)}`",
    ]
    if validation.get("profit_delta"):
        lines.append(f"Profit delta: `{validation['profit_delta']}`")
    if validation.get("execution_log_path"):
        lines.append(f"Execution log: `{validation['execution_log_path']}`")
    sequence = validation.get("transaction_sequence")
    if isinstance(sequence, list) and sequence:
        lines.append("Transaction sequence: " + " -> ".join(f"`{step}`" for step in sequence))
    return "\n".join(lines)


def _render_fuzz_seeds(seeds: object) -> str:
    if not isinstance(seeds, list) or not seeds:
        return "No fuzz seed suggestions."
    lines = []
    for seed in seeds:
        if not isinstance(seed, dict):
            continue
        lines.append(
            "- "
            f"`{seed.get('seed_id', 'seed')}` targets "
            f"`{seed.get('target_function', 'target')}`; "
            f"supported by `{', '.join(seed.get('supported_by', []))}`."
        )
    return "\n".join(lines) if lines else "No fuzz seed suggestions."


def _render_formal_properties(properties: object) -> str:
    if not isinstance(properties, list) or not properties:
        return "No formal property suggestions."
    lines = []
    for prop in properties:
        if not isinstance(prop, dict):
            continue
        lines.append(
            "- "
            f"`{prop.get('property_id', 'property')}` is `{prop.get('status', 'draft')}` "
            f"and `{prop.get('verification_status', 'not_proven')}`."
        )
    return "\n".join(lines) if lines else "No formal property suggestions."


def _render_defi_profit_signal(signal: object) -> str:
    if not isinstance(signal, dict) or not signal:
        return "Status: `not_observed`"
    lines = [
        f"Status: `{signal.get('status', 'not_observed')}`",
        f"Profitability: `{signal.get('profitability_status', 'not_assessed')}`",
    ]
    asset_flow = signal.get("asset_flow")
    if isinstance(asset_flow, list) and asset_flow:
        lines.append(f"Asset delta: `{asset_flow}`")
    return "\n".join(lines)


def _render_falsification_pack(pack: object) -> str:
    if not isinstance(pack, dict) or not pack:
        return "Status: `unavailable`"
    lines = [
        f"Status: `{pack.get('status', 'needs_human_review')}`",
        f"Human review required: `{pack.get('human_review_required', True)}`",
    ]
    reviewer_goal = pack.get("reviewer_goal")
    if reviewer_goal:
        lines.append(f"Reviewer goal: {reviewer_goal}")
    checks = pack.get("counterevidence_checks")
    if isinstance(checks, list) and checks:
        lines.append("")
        lines.append("Counterevidence checks:")
        for check in checks:
            if not isinstance(check, dict):
                continue
            lines.append(
                "- "
                f"`{check.get('check_id', 'check')}`: "
                f"{check.get('question', 'Review the finding evidence.')} "
                f"Refutes if: {check.get('would_refute_if', 'counterevidence is confirmed')}"
            )
    requirements = pack.get("confirmation_requirements")
    if isinstance(requirements, list) and requirements:
        lines.append("")
        lines.append("Confirmation requirements:")
        lines.extend(f"- {requirement}" for requirement in requirements)
    missing = pack.get("missing_evidence")
    if isinstance(missing, list) and missing:
        lines.append("")
        lines.append("Missing evidence:")
        lines.extend(f"- {item}" for item in missing)
    return "\n".join(lines)
