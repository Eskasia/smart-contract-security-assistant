from pathlib import Path

from smart_contract_audit.models import Finding, Location
from smart_contract_audit.report_builder import (
    build_analysis_report,
    finish_analysis_report,
    overall_status_for,
    review_status_for,
)
from smart_contract_audit.trace.store import TraceStore


def test_build_analysis_report_aggregates_metadata_and_score() -> None:
    finding = _finding()
    finding.prompt_tokens = 10
    finding.completion_tokens = 20
    finding.total_tokens = 30

    report = build_analysis_report(
        status="finding",
        contract_id="contract_001",
        business_logic_review_required=False,
        review_reason="Human review required.",
        findings=[finding],
        trace_id="trace_001",
        solc_version="0.8.34",
        slither_version="0.11.5",
        rag_mode="fallback",
        total_duration_ms=123,
        errors=["warning"],
        target=None,
        external_tool_results=[],
    )

    assert report.review_status == "pending_human_review"
    assert report.analysis_metadata.total_duration_ms == 123
    assert report.analysis_metadata.total_tokens == 30
    assert report.analysis_metadata.local_average_judge_score == 5.0
    assert report.security_score == 70.0
    assert report.analysis_metadata.input_kind == "unknown"


def test_finish_analysis_report_writes_reports_and_updates_trace(tmp_path: Path) -> None:
    with TraceStore(tmp_path / "trace.sqlite") as trace_store:
        trace_id = trace_store.create_trace(
            contract_id="contract_001",
            solc_version=None,
            slither_version=None,
            model_version="fallback",
            dataset_version="dataset_v1",
            initial_rag_mode="fallback",
            review_status="blocked",
        )
        report = build_analysis_report(
            status="no_finding",
            contract_id="contract_001",
            business_logic_review_required=False,
            review_reason="Human review required.",
            findings=[],
            trace_id=trace_id,
            solc_version=None,
            slither_version=None,
            rag_mode="fallback",
            total_duration_ms=7,
            errors=[],
            target=None,
            external_tool_results=[],
        )
        finish_analysis_report(
            trace_store,
            trace_id=trace_id,
            report=report,
            output_dir=tmp_path / "reports",
            contract_id="contract_001",
        )
        row = trace_store.conn.execute(
            "SELECT final_status, total_duration_ms, review_status FROM analysis_trace"
        ).fetchone()

    assert row == ("no_finding", 7, "pending_human_review")
    assert (tmp_path / "reports" / "contract_001.json").exists()
    assert (tmp_path / "reports" / "contract_001.md").exists()


def test_status_helpers_are_stable() -> None:
    partial = _finding()
    partial.partial = True

    assert review_status_for("error") == "blocked"
    assert review_status_for("finding") == "pending_human_review"
    assert overall_status_for([]) == "no_finding"
    assert overall_status_for([_finding()]) == "finding"
    assert overall_status_for([partial]) == "partial_analysis"


def _finding() -> Finding:
    return Finding(
        finding_id="f_001",
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(file="Vault.sol", function="withdraw", line_start=1, line_end=1),
        evidence="External call before balance update.",
        reference=["SWC-107"],
        finding_confidence=1.0,
        explanation_confidence=1.0,
        explanation="explanation",
        attack_path="attack path",
        fix_suggestion="fix",
        remediation_code="code",
        vulnerable_code="code",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
        local_judge_score=5.0,
        external_judge_score=5.0,
    )
