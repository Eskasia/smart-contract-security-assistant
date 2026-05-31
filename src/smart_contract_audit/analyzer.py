from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from .analysis_context import (
    create_analysis_context,
    validate_analysis_target,
)
from .config import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_MODEL_VERSION,
    DEFAULT_RAG_MODE,
)
from .external_finding_adapter import (
    EXTERNAL_FINDING_TOOLS,
    external_findings_from_results,
    merge_external_findings,
    record_external_findings,
)
from .external_tools import run_external_tools
from .finding_processor import process_slither_findings
from .models import AnalysisReport, ExternalToolResult
from .report_builder import (
    build_analysis_report,
    elapsed_ms,
    finish_analysis_report,
    overall_status_for,
    review_status_for,
)
from .slither_runner import SlitherRunError, SlitherRunResult, run_slither
from .solidity_target import SolidityTarget
from .trace.store import TraceStore
from .validation.validator import validate_report

SlitherRunner = Callable[..., SlitherRunResult]
ExternalToolRunner = Callable[[Path, Path, tuple[str, ...], int], list[ExternalToolResult]]


def analyze_contract(
    contract_path: Path,
    output_dir: Path,
    trace_db: Path | None = None,
    dataset_chunks: Path | None = None,
    rag_mode: str = DEFAULT_RAG_MODE,
    model_path: str | None = None,
    slither_runner: SlitherRunner = run_slither,
    external_tools: tuple[str, ...] = (),
    external_timeout_seconds: int = 60,
    external_tool_runner: ExternalToolRunner = run_external_tools,
    native_build_policy: str = "trusted",
) -> AnalysisReport:
    started = time.perf_counter()
    errors: list[str] = []
    context = create_analysis_context(contract_path, output_dir, trace_db, dataset_chunks)

    solc_version: str | None = None
    slither_version: str | None = None
    raw_slither: dict = {}
    external_tool_results: list[ExternalToolResult] = []

    with TraceStore(context.trace_db) as trace_store:
        trace_id = trace_store.create_trace(
            contract_id=context.contract_id,
            solc_version=None,
            slither_version=None,
            model_version=DEFAULT_MODEL_VERSION,
            dataset_version=DEFAULT_DATASET_VERSION,
            initial_rag_mode=rag_mode,
            review_status=review_status_for("error"),
        )

        validation_error = context.target_error or validate_analysis_target(context.target)
        if validation_error:
            errors.append(validation_error)
            report = build_analysis_report(
                status="error",
                contract_id=context.contract_id,
                business_logic_review_required=context.business_logic_review_required,
                review_reason=context.review_reason,
                findings=[],
                trace_id=trace_id,
                solc_version=solc_version,
                slither_version=slither_version,
                rag_mode=rag_mode,
                total_duration_ms=elapsed_ms(started),
                errors=errors,
                target=context.target,
                external_tool_results=external_tool_results,
            )
            finish_analysis_report(
                trace_store,
                trace_id,
                report,
                context.output_dir,
                context.contract_id,
            )
            return report

        try:
            assert context.target is not None
            slither_result = slither_runner(
                context.target.input_path,
                native_build_policy=native_build_policy,
            )
            raw_slither = slither_result.raw_json
            solc_version = slither_result.solc_version
            slither_version = slither_result.slither_version
            errors.extend(slither_result.warnings)
            trace_store.update_versions(trace_id, solc_version, slither_version)
        except (SlitherRunError, TimeoutError) as exc:
            errors.append(str(exc))
            report = build_analysis_report(
                status="error",
                contract_id=context.contract_id,
                business_logic_review_required=context.business_logic_review_required,
                review_reason=context.review_reason,
                findings=[],
                trace_id=trace_id,
                solc_version=solc_version,
                slither_version=slither_version,
                rag_mode=rag_mode,
                total_duration_ms=elapsed_ms(started),
                errors=errors,
                target=context.target,
                external_tool_results=external_tool_results,
            )
            finish_analysis_report(
                trace_store,
                trace_id,
                report,
                context.output_dir,
                context.contract_id,
            )
            return report

        if external_tools:
            assert context.target is not None
            tools_to_run, preflight_results = _preflight_external_tools(
                external_tools,
                context.target,
                native_build_policy,
            )
            external_tool_results = external_tool_runner(
                context.target.input_path,
                context.output_dir / "external-tools" / context.contract_id,
                tools_to_run,
                external_timeout_seconds,
            )
            external_tool_results = [*preflight_results, *external_tool_results]

        assert context.target is not None
        finding_result = process_slither_findings(
            raw_slither=raw_slither,
            target=context.target,
            dataset_chunks=context.dataset_chunks,
            initial_rag_mode=rag_mode,
            model_path=model_path,
            trace_store=trace_store,
            trace_id=trace_id,
            started_at=started,
            clock=time.perf_counter,
        )
        processed_findings = finding_result.findings
        current_rag_mode = finding_result.current_rag_mode
        external_findings = external_findings_from_results(
            external_tool_results,
            context.target,
            start_index=len(processed_findings) + 1,
        )
        processed_findings = merge_external_findings(processed_findings, external_findings)
        record_external_findings(
            [
                finding
                for finding in processed_findings
                if finding.static_tool_source in EXTERNAL_FINDING_TOOLS
            ],
            trace_store,
            trace_id,
        )
        final_status = overall_status_for(processed_findings)

        report = build_analysis_report(
            status=final_status,
            contract_id=context.contract_id,
            business_logic_review_required=context.business_logic_review_required,
            review_reason=context.review_reason,
            findings=processed_findings,
            trace_id=trace_id,
            solc_version=solc_version,
            slither_version=slither_version,
            rag_mode=current_rag_mode,
            total_duration_ms=elapsed_ms(started),
            errors=errors,
            target=context.target,
            external_tool_results=external_tool_results,
        )

        validation = validate_report(report.to_dict())
        if not validation.valid:
            report.analysis_metadata.errors.extend(validation.errors)
            report.overall_status = "error"
            report.review_status = review_status_for("error")

        finish_analysis_report(
            trace_store,
            trace_id,
            report,
            context.output_dir,
            context.contract_id,
        )
        return report


def _preflight_external_tools(
    tools: tuple[str, ...],
    target: SolidityTarget,
    native_build_policy: str,
) -> tuple[tuple[str, ...], list[ExternalToolResult]]:
    runnable: list[str] = []
    preflight_results: list[ExternalToolResult] = []
    for tool in tools:
        if tool != "halmos":
            runnable.append(tool)
            continue
        if native_build_policy != "trusted" or target.project_type != "foundry":
            preflight_results.append(
                ExternalToolResult(
                    tool_name="halmos",
                    command=["halmos"],
                    status="skipped",
                    findings_count=0,
                    summary="halmos requires a trusted Foundry project; skipped optional analysis.",
                )
            )
            continue
        runnable.append(tool)
    return tuple(runnable), preflight_results
