from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from pathlib import Path

from .confidence.explanation_score import compute_explanation_confidence
from .confidence.finding_score import compute_finding_confidence
from .config import (
    BUSINESS_LOGIC_KEYWORDS,
    DEFAULT_DATASET_VERSION,
    DEFAULT_MODEL_VERSION,
    DEFAULT_RAG_MODE,
    MAX_SOLIDITY_LINES,
)
from .finding_adapter import normalize_slither_json
from .llm.generator import generate_finding_details
from .llm.mlx_runtime import MLXRuntimeConfig
from .llm.prompt_template import pack_finding_prompt
from .models import AnalysisMetadata, AnalysisReport, Finding
from .rag.indexer import load_chunks
from .rag.retriever import retrieve_chunks
from .report import write_json_report, write_markdown_report
from .slither_runner import SlitherRunError, SlitherRunResult, run_slither
from .trace.store import TraceStore
from .validation.validator import validate_report

SlitherRunner = Callable[[Path], SlitherRunResult]


def analyze_contract(
    contract_path: Path,
    output_dir: Path,
    trace_db: Path | None = None,
    dataset_chunks: Path | None = None,
    rag_mode: str = DEFAULT_RAG_MODE,
    model_path: str | None = None,
    slither_runner: SlitherRunner = run_slither,
) -> AnalysisReport:
    started = time.perf_counter()
    errors: list[str] = []
    contract_path = contract_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    trace_db = trace_db or output_dir / "analysis_trace.sqlite"
    dataset_chunks = dataset_chunks or Path("data/dataset_v1.0/chunks/chunks.jsonl")

    source = _read_contract(contract_path)
    contract_id = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
    business_logic_review_required = _business_logic_review_required(source)
    review_reason = _review_reason(business_logic_review_required)

    solc_version: str | None = None
    slither_version: str | None = None
    raw_slither: dict = {}
    mapped: list[Finding] = []
    unmapped: list[dict] = []
    final_status = "error"

    with TraceStore(trace_db) as trace_store:
        trace_id = trace_store.create_trace(
            contract_id=contract_id,
            solc_version=None,
            slither_version=None,
            model_version=DEFAULT_MODEL_VERSION,
            dataset_version=DEFAULT_DATASET_VERSION,
            initial_rag_mode=rag_mode,
        )

        validation_error = _validate_input(contract_path, source)
        if validation_error:
            errors.append(validation_error)
            report = _build_report(
                "error",
                contract_id,
                business_logic_review_required,
                review_reason,
                [],
                trace_id,
                solc_version,
                slither_version,
                rag_mode,
                started,
                errors,
            )
            _finish(trace_store, trace_id, report, output_dir, contract_id)
            return report

        try:
            slither_result = slither_runner(contract_path)
            raw_slither = slither_result.raw_json
            solc_version = slither_result.solc_version
            slither_version = slither_result.slither_version
            errors.extend(slither_result.warnings)
            trace_store.update_versions(trace_id, solc_version, slither_version)
        except (SlitherRunError, TimeoutError) as exc:
            errors.append(str(exc))
            report = _build_report(
                "error",
                contract_id,
                business_logic_review_required,
                review_reason,
                [],
                trace_id,
                solc_version,
                slither_version,
                rag_mode,
                started,
                errors,
            )
            _finish(trace_store, trace_id, report, output_dir, contract_id)
            return report

        adapter_result = normalize_slither_json(raw_slither, contract_path)
        mapped = adapter_result.findings
        unmapped = adapter_result.unmapped
        chunks = load_chunks(dataset_chunks)

        processed_findings: list[Finding] = []
        current_rag_mode = rag_mode
        for finding in mapped:
            elapsed = time.perf_counter() - started
            if elapsed >= 115:
                finding.partial = True
                processed_findings.append(finding)
                continue
            if elapsed >= 100:
                current_rag_mode = "fallback"
            elif elapsed >= 80:
                current_rag_mode = "fast"

            retrieval_start = time.perf_counter()
            query = f"{finding.vulnerability_type} {finding.evidence[:200]}"
            rag_chunks = retrieve_chunks(query, chunks, current_rag_mode)
            retrieval_duration_ms = _elapsed_ms(retrieval_start)

            if retrieval_duration_ms > 40_000:
                current_rag_mode = "fast"
            elif retrieval_duration_ms > 20_000:
                current_rag_mode = "balanced"

            llm_start = time.perf_counter()
            details = generate_finding_details(
                finding,
                rag_chunks,
                MLXRuntimeConfig(model_path=model_path),
            )
            llm_duration_ms = _elapsed_ms(llm_start)

            finding.explanation = details["explanation"]
            finding.attack_path = details["attack_path"]
            finding.fix_suggestion = details["fix_suggestion"]
            rag_dicts = [chunk.to_dict() for chunk in rag_chunks]
            finding.finding_confidence = compute_finding_confidence(
                finding.severity,
                finding.vulnerability_type,
                rag_dicts,
            )
            finding.explanation_confidence = compute_explanation_confidence(
                details,
                schema_valid=True,
                rag_chunks=rag_dicts,
            )
            if not rag_chunks:
                finding.explanation_confidence = min(finding.explanation_confidence, 0.5)

            prompt = pack_finding_prompt(finding, rag_chunks)
            trace_store.record_finding(
                trace_id=trace_id,
                finding_id=finding.finding_id,
                detector_name=finding.detector_name,
                rag_mode=current_rag_mode,
                retrieval_duration_ms=retrieval_duration_ms,
                llm_duration_ms=llm_duration_ms,
                chunks_used=len(rag_chunks),
                slither_raw=_find_raw_detector(raw_slither, finding.detector_name),
                normalized_finding=finding.to_dict(),
                rag_chunk_ids=[chunk.chunk_id for chunk in rag_chunks],
                packed_prompt=prompt,
                llm_raw_output=details,
                schema_valid=True,
                partial=finding.partial,
            )
            processed_findings.append(finding)

        for index, detector in enumerate(unmapped, start=1):
            detector_name = str(detector.get("check") or detector.get("detector") or "unknown")
            trace_store.record_finding(
                trace_id=trace_id,
                finding_id=f"unmapped_{index:03d}",
                detector_name=detector_name,
                rag_mode=current_rag_mode,
                retrieval_duration_ms=0,
                llm_duration_ms=0,
                chunks_used=0,
                slither_raw=detector,
                normalized_finding=None,
                rag_chunk_ids=[],
                packed_prompt="",
                llm_raw_output=None,
                schema_valid=False,
                partial=True,
            )

        if processed_findings and any(finding.partial for finding in processed_findings):
            final_status = "partial_analysis"
        elif processed_findings:
            final_status = "finding"
        else:
            final_status = "no_finding"

        report = _build_report(
            final_status,
            contract_id,
            business_logic_review_required,
            review_reason,
            processed_findings,
            trace_id,
            solc_version,
            slither_version,
            current_rag_mode,
            started,
            errors,
        )

        validation = validate_report(report.to_dict())
        if not validation.valid:
            report.analysis_metadata.errors.extend(validation.errors)
            report.overall_status = "error"

        _finish(trace_store, trace_id, report, output_dir, contract_id)
        return report


def _read_contract(contract_path: Path) -> str:
    return contract_path.read_text(encoding="utf-8")


def _validate_input(contract_path: Path, source: str) -> str | None:
    if contract_path.suffix != ".sol":
        return "Input must be a single `.sol` file."
    if len(source.splitlines()) > MAX_SOLIDITY_LINES:
        return f"Input exceeds {MAX_SOLIDITY_LINES} lines."
    return None


def _business_logic_review_required(source: str) -> bool:
    lowered = source.lower()
    return any(keyword in lowered for keyword in BUSINESS_LOGIC_KEYWORDS)


def _review_reason(required: bool) -> str:
    if required:
        return (
            "Contract contains DeFi reward/oracle/pool/swap/staking related logic "
            "outside Slither v1.0 coverage."
        )
    return "Slither-based MVP findings still require human security review."


def _build_report(
    status: str,
    contract_id: str,
    business_logic_review_required: bool,
    review_reason: str,
    findings: list[Finding],
    trace_id: str,
    solc_version: str | None,
    slither_version: str | None,
    rag_mode: str,
    started: float,
    errors: list[str],
) -> AnalysisReport:
    return AnalysisReport(
        overall_status=status,
        contract_id=contract_id,
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
            rag_mode=rag_mode,
            total_duration_ms=_elapsed_ms(started),
            errors=errors,
        ),
    )


def _finish(
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
    )
    write_json_report(report, output_dir / f"{contract_id}.json")
    write_markdown_report(report, output_dir / f"{contract_id}.md")


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _find_raw_detector(raw_slither: dict, detector_name: str) -> dict | None:
    detectors = raw_slither.get("results", {}).get("detectors", []) or []
    for detector in detectors:
        name = detector.get("check") or detector.get("detector") or detector.get("name")
        if name == detector_name:
            return detector
    return None
