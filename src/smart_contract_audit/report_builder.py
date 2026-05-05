from __future__ import annotations

import time
from pathlib import Path

from .analysis_context import empty_target
from .config import DEFAULT_DATASET_VERSION, DEFAULT_MODEL_VERSION, REPORT_SCHEMA_VERSION
from .models import AnalysisMetadata, AnalysisReport, ExternalToolResult, Finding
from .report import write_json_report, write_markdown_report
from .scoring.security_score import compute_security_score
from .solidity_target import SolidityTarget
from .trace.store import TraceStore


def review_status_for(status: str) -> str:
    if status == "error":
        return "blocked"
    return "pending_human_review"


def overall_status_for(findings: list[Finding]) -> str:
    if findings and any(finding.partial for finding in findings):
        return "partial_analysis"
    if findings:
        return "finding"
    return "no_finding"


def build_analysis_report(
    status: str,
    contract_id: str,
    business_logic_review_required: bool,
    review_reason: str,
    findings: list[Finding],
    trace_id: str,
    solc_version: str | None,
    slither_version: str | None,
    rag_mode: str,
    total_duration_ms: int,
    errors: list[str],
    target: SolidityTarget | None,
    external_tool_results: list[ExternalToolResult],
) -> AnalysisReport:
    target = target or empty_target()
    review_status = review_status_for(status)
    security_score = compute_security_score(
        findings=findings,
        review_status=review_status,
        partial_analysis=status == "partial_analysis",
        business_logic_review_required=business_logic_review_required,
    )
    return AnalysisReport(
        report_version=REPORT_SCHEMA_VERSION,
        overall_status=status,
        contract_id=contract_id,
        review_status=review_status,
        requires_human_review=True,
        business_logic_review_required=business_logic_review_required,
        review_reason=review_reason,
        findings=findings,
        analysis_metadata=AnalysisMetadata(
            dataset_version=DEFAULT_DATASET_VERSION,
            model_version=DEFAULT_MODEL_VERSION,
            solc_version=solc_version,
            slither_version=slither_version,
            partial_analysis=status == "partial_analysis",
            analysis_trace_id=trace_id,
            context_tokens_used=sum(len(finding.evidence.split()) for finding in findings),
            prompt_tokens=sum(finding.prompt_tokens for finding in findings),
            completion_tokens=sum(finding.completion_tokens for finding in findings),
            total_tokens=sum(finding.total_tokens for finding in findings),
            local_average_judge_score=_average_score(
                [finding.local_judge_score for finding in findings]
            ),
            external_average_judge_score=_average_score(
                [finding.external_judge_score for finding in findings]
            ),
            rag_mode=rag_mode,
            total_duration_ms=total_duration_ms,
            input_kind=target.input_kind,
            project_type=target.project_type,
            entry_path=str(target.entry_path),
            project_root=str(target.project_root),
            source_files_count=len(target.source_files),
            errors=errors,
        ),
        security_score=security_score.score,
        score_formula_version=security_score.formula_version,
        score_factors=security_score.factors,
        external_tool_results=external_tool_results,
    )


def finish_analysis_report(
    trace_store: TraceStore,
    trace_id: str,
    report: AnalysisReport,
    output_dir: Path,
    contract_id: str,
) -> None:
    trace_store.finish_trace(
        trace_id,
        report.overall_status,
        report.analysis_metadata.total_duration_ms,
        report.review_status,
    )
    write_json_report(report, output_dir / f"{contract_id}.json")
    write_markdown_report(report, output_dir / f"{contract_id}.md")


def elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def _average_score(scores: list[float]) -> float:
    return round(sum(scores) / len(scores), 2) if scores else 0.0
