from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .config import (
    BUSINESS_LOGIC_KEYWORDS,
    MAX_PROJECT_SOLIDITY_FILES,
    MAX_PROJECT_SOLIDITY_LINES,
    MAX_SOLIDITY_LINES,
)
from .solidity_target import SolidityTarget, resolve_solidity_target


@dataclass(frozen=True)
class AnalysisContext:
    contract_path: Path
    output_dir: Path
    trace_db: Path
    dataset_chunks: Path
    target: SolidityTarget | None
    target_error: str | None
    source: str
    contract_id: str
    business_logic_review_required: bool
    review_reason: str


def create_analysis_context(
    contract_path: Path,
    output_dir: Path,
    trace_db: Path | None,
    dataset_chunks: Path | None,
) -> AnalysisContext:
    contract_path = contract_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    trace_db = trace_db or output_dir / "analysis_trace.sqlite"
    dataset_chunks = dataset_chunks or Path("data/dataset_v1.0/chunks/chunks.jsonl")

    target_error: str | None = None
    target: SolidityTarget | None = None
    try:
        target = resolve_solidity_target(contract_path)
        source = target.combined_source
    except ValueError as exc:
        target_error = str(exc)
        source = ""

    business_logic_review_required = requires_business_logic_review(source)
    return AnalysisContext(
        contract_path=contract_path,
        output_dir=output_dir,
        trace_db=trace_db,
        dataset_chunks=dataset_chunks,
        target=target,
        target_error=target_error,
        source=source,
        contract_id=hashlib.sha256(source.encode("utf-8")).hexdigest()[:12],
        business_logic_review_required=business_logic_review_required,
        review_reason=review_reason_for(business_logic_review_required),
    )


def validate_analysis_target(target: SolidityTarget | None) -> str | None:
    if target is None:
        return "Input target could not be resolved."
    if target.input_kind == "single_file" and target.total_source_lines > MAX_SOLIDITY_LINES:
        return f"Input exceeds {MAX_SOLIDITY_LINES} lines."
    if target.input_kind != "single_file":
        if len(target.source_files) > MAX_PROJECT_SOLIDITY_FILES:
            return f"Project exceeds {MAX_PROJECT_SOLIDITY_FILES} Solidity files."
        if target.total_source_lines > MAX_PROJECT_SOLIDITY_LINES:
            return f"Project exceeds {MAX_PROJECT_SOLIDITY_LINES} Solidity lines."
    return None


def requires_business_logic_review(source: str) -> bool:
    lowered = source.lower()
    return any(keyword in lowered for keyword in BUSINESS_LOGIC_KEYWORDS)


def review_reason_for(required: bool) -> str:
    if required:
        return (
            "Contract contains DeFi reward/oracle/pool/swap/staking related logic "
            "outside Slither v1.0 coverage."
        )
    return "Slither-based MVP findings still require human security review."


def empty_target() -> SolidityTarget:
    empty = Path("")
    return SolidityTarget(
        input_path=empty,
        analysis_path=empty,
        entry_path=empty,
        project_root=empty,
        input_kind="unknown",
        project_type="unknown",
        source_files=(),
        remappings=(),
    )
