from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .confidence.explanation_score import compute_explanation_confidence
from .confidence.finding_score import compute_finding_confidence
from .finding_adapter import normalize_slither_json
from .judge import score_finding_output
from .llm.generator import generate_finding_details
from .llm.mlx_runtime import MLXRuntimeConfig
from .llm.prompt_template import pack_finding_prompt
from .models import Finding
from .rag.indexer import load_chunks
from .rag.retriever import retrieve_chunks
from .solidity_target import SolidityTarget
from .trace.store import TraceStore

Clock = Callable[[], float]


@dataclass(frozen=True)
class FindingProcessingResult:
    findings: list[Finding]
    current_rag_mode: str


def process_slither_findings(
    raw_slither: dict,
    target: SolidityTarget,
    dataset_chunks: Path,
    initial_rag_mode: str,
    model_path: str | None,
    trace_store: TraceStore,
    trace_id: str,
    started_at: float,
    clock: Clock = time.perf_counter,
) -> FindingProcessingResult:
    adapter_result = normalize_slither_json(raw_slither, target.entry_path)
    chunks = load_chunks(dataset_chunks)
    processed_findings: list[Finding] = []
    current_rag_mode = initial_rag_mode

    for finding in adapter_result.findings:
        elapsed = clock() - started_at
        if elapsed >= 115:
            finding.partial = True
            trace_store.record_finding(
                trace_id=trace_id,
                finding_id=finding.finding_id,
                detector_name=finding.detector_name,
                rag_mode=current_rag_mode,
                retrieval_duration_ms=0,
                llm_duration_ms=0,
                chunks_used=0,
                slither_raw=find_raw_detector(raw_slither, finding.detector_name),
                normalized_finding=finding.to_dict(),
                rag_chunk_ids=[],
                packed_prompt="",
                llm_raw_output=None,
                schema_valid=True,
                partial=True,
            )
            processed_findings.append(finding)
            continue
        if elapsed >= 100:
            current_rag_mode = "fallback"
        elif elapsed >= 80:
            current_rag_mode = "fast"

        retrieval_start = clock()
        query = f"{finding.vulnerability_type} {finding.evidence[:200]}"
        rag_chunks = retrieve_chunks(query, chunks, current_rag_mode)
        retrieval_duration_ms = _elapsed_ms(retrieval_start, clock)
        finding.vulnerable_code = extract_code_snippet(target, finding)
        prompt = pack_finding_prompt(finding, rag_chunks)
        finding.prompt_tokens = count_tokens(prompt)

        if retrieval_duration_ms > 40_000:
            current_rag_mode = "fast"
        elif retrieval_duration_ms > 20_000:
            current_rag_mode = "balanced"

        llm_start = clock()
        details = generate_finding_details(
            finding,
            rag_chunks,
            MLXRuntimeConfig(model_path=model_path),
        )
        llm_duration_ms = _elapsed_ms(llm_start, clock)

        finding.explanation = details["explanation"]
        finding.attack_path = details["attack_path"]
        finding.fix_suggestion = details["fix_suggestion"]
        finding.remediation_code = details.get("remediation_code", "")
        finding.completion_tokens = count_tokens(json.dumps(details, ensure_ascii=False))
        finding.total_tokens = finding.prompt_tokens + finding.completion_tokens
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
        finding.local_judge_score, finding.external_judge_score = score_finding_output(
            finding,
            rag_chunks,
        )

        trace_store.record_finding(
            trace_id=trace_id,
            finding_id=finding.finding_id,
            detector_name=finding.detector_name,
            rag_mode=current_rag_mode,
            retrieval_duration_ms=retrieval_duration_ms,
            llm_duration_ms=llm_duration_ms,
            chunks_used=len(rag_chunks),
            slither_raw=find_raw_detector(raw_slither, finding.detector_name),
            normalized_finding=finding.to_dict(),
            rag_chunk_ids=[chunk.chunk_id for chunk in rag_chunks],
            packed_prompt=prompt,
            llm_raw_output=details,
            schema_valid=True,
            partial=finding.partial,
        )
        processed_findings.append(finding)

    record_unmapped_findings(
        adapter_result.unmapped,
        trace_store=trace_store,
        trace_id=trace_id,
        rag_mode=current_rag_mode,
    )
    return FindingProcessingResult(
        findings=processed_findings,
        current_rag_mode=current_rag_mode,
    )


def record_unmapped_findings(
    unmapped: list[dict],
    trace_store: TraceStore,
    trace_id: str,
    rag_mode: str,
) -> None:
    for index, detector in enumerate(unmapped, start=1):
        detector_name = str(detector.get("check") or detector.get("detector") or "unknown")
        trace_store.record_finding(
            trace_id=trace_id,
            finding_id=f"unmapped_{index:03d}",
            detector_name=detector_name,
            rag_mode=rag_mode,
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


def count_tokens(text: str) -> int:
    try:
        import tiktoken
    except ImportError:
        return max(1, len(re.findall(r"\S+", text)))

    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def extract_code_snippet(target: SolidityTarget, finding: Finding) -> str:
    source_file = resolve_source_file(target, finding.location.file)
    if source_file is None or not source_file.exists():
        return ""
    lines = source_file.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(1, finding.location.line_start)
    end = min(len(lines), max(start, finding.location.line_end))
    return "\n".join(f"{line_no}: {lines[line_no - 1]}" for line_no in range(start, end + 1))


def resolve_source_file(target: SolidityTarget, location_file: str) -> Path | None:
    location_path = Path(location_file)
    candidates = []
    if location_path.is_absolute():
        candidates.append(location_path)
    else:
        candidates.extend([target.project_root / location_path, Path.cwd() / location_path])

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    normalized = location_file.replace("\\", "/")
    for source_file in target.source_files:
        source_normalized = str(source_file).replace("\\", "/")
        relative_normalized = str(source_file.relative_to(target.project_root)).replace("\\", "/")
        if source_file.name == location_file or source_normalized.endswith(normalized):
            return source_file
        if relative_normalized.endswith(normalized):
            return source_file
    return None


def find_raw_detector(raw_slither: dict, detector_name: str) -> dict | None:
    detectors = raw_slither.get("results", {}).get("detectors", []) or []
    for detector in detectors:
        name = detector.get("check") or detector.get("detector") or detector.get("name")
        if name == detector_name:
            return detector
    return None


def _elapsed_ms(started_at: float, clock: Clock) -> int:
    return int((clock() - started_at) * 1000)
