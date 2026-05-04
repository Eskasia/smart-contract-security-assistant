from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from smart_contract_audit.http_api import ApiConfig, create_api_server
from smart_contract_audit.models import AnalysisMetadata, AnalysisReport, Finding, Location
from smart_contract_audit.trace.lookup import trace_dashboard
from smart_contract_audit.trace.store import TraceStore


def test_http_api_analysis_report_trace_review_and_sse(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")
    output_dir = tmp_path / "reports"

    def fake_analyzer(**kwargs: Any) -> AnalysisReport:
        trace_db = kwargs["trace_db"]
        with TraceStore(trace_db) as store:
            trace_id = store.create_trace(
                contract_id="contract_api_001",
                solc_version="0.8.34",
                slither_version="0.11.5",
                model_version="fallback",
                dataset_version="dataset_v1",
                initial_rag_mode=kwargs["rag_mode"],
                review_status="pending_human_review",
            )
            finding = _finding()
            store.record_finding(
                trace_id=trace_id,
                finding_id=finding.finding_id,
                detector_name=finding.detector_name,
                rag_mode=kwargs["rag_mode"],
                retrieval_duration_ms=3,
                llm_duration_ms=4,
                chunks_used=1,
                slither_raw={"check": finding.detector_name},
                normalized_finding=finding.to_dict(),
                rag_chunk_ids=["chunk_001"],
                packed_prompt="Explain reentrancy",
                llm_raw_output={"explanation": finding.explanation},
                schema_valid=True,
            )
            store.finish_trace(trace_id, "finding", 7, "pending_human_review")

        return AnalysisReport(
            report_version="1.0",
            overall_status="finding",
            contract_id="contract_api_001",
            review_status="pending_human_review",
            requires_human_review=True,
            business_logic_review_required=False,
            review_reason="Human review required.",
            findings=[finding],
            analysis_metadata=AnalysisMetadata(
                dataset_version="dataset_v1",
                model_version="fallback",
                solc_version="0.8.34",
                slither_version="0.11.5",
                partial_analysis=False,
                analysis_trace_id=trace_id,
                context_tokens_used=1,
                prompt_tokens=2,
                completion_tokens=3,
                total_tokens=5,
                local_average_judge_score=5.0,
                external_average_judge_score=5.0,
                rag_mode=kwargs["rag_mode"],
                total_duration_ms=7,
                errors=[],
            ),
        )

    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=output_dir),
        analyzer=fake_analyzer,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        created = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={
                "input_path": str(contract),
                "rag_mode": "fallback",
                "dataset_chunks": "data/dataset_v1.0/chunks/chunks.jsonl",
                "model_path": None,
            },
        )
        assert created["status"] == "queued"

        job = _wait_for_terminal_job(base_url, created["analysis_id"])
        assert job["status"] == "finding"
        assert job["contract_id"] == "contract_api_001"

        events = _read_sse_events(f"{base_url}/api/analyses/{created['analysis_id']}/stream")
        assert any(event["type"] == "status" and event["status"] == "running" for event in events)
        assert events[-1]["type"] == "done"
        assert events[-1]["contract_id"] == "contract_api_001"

        report = _json_request(f"{base_url}/api/reports/contract_api_001")
        trace_id = report["analysis_metadata"]["analysis_trace_id"]
        assert report["findings"][0]["finding_id"] == "f_001"

        trace_rows = _json_request(f"{base_url}/api/traces/{trace_id}?finding_id=f_001")
        assert trace_rows[0]["packed_prompt"] == "Explain reentrancy"

        patched = _json_request(
            f"{base_url}/api/reports/contract_api_001/review",
            method="PATCH",
            payload={"review_status": "approved"},
        )
        assert patched["report"]["review_status"] == "approved"
        updated_report = _json_request(f"{base_url}/api/reports/contract_api_001")
        assert updated_report["review_status"] == "approved"
        dashboard = trace_dashboard(output_dir / "analysis_trace.sqlite")
        assert dashboard[0]["review_status"] == "approved"

        patched_finding = _json_request(
            f"{base_url}/api/reports/contract_api_001/findings/f_001/review",
            method="PATCH",
            payload={
                "review_status": "false_positive",
                "review_note": "Known safe fixture.",
            },
        )
        assert patched_finding["finding"]["review_status"] == "false_positive"
        assert patched_finding["finding"]["review_note"] == "Known safe fixture."
        assert patched_finding["report"]["security_score"] == 100.0
        assert (
            patched_finding["report"]["score_factors"]["finding_penalties"][0][
                "finding_review_multiplier"
            ]
            == 0.0
        )

        trace_rows = _json_request(f"{base_url}/api/traces/{trace_id}?finding_id=f_001")
        assert trace_rows[0]["review_status"] == "false_positive"
        assert trace_rows[0]["review_note"] == "Known safe fixture."
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_rejects_invalid_payload_and_review_status(tmp_path: Path) -> None:
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=tmp_path / "reports"),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": "Vault.sol", "rag_mode": "slow"},
            expect_error=422,
        )
        assert error["error"]["code"] == "VALIDATION_ERROR"

        error = _json_request(
            f"{base_url}/api/reports/missing/review",
            method="PATCH",
            payload={"review_status": "needs_more_work"},
            expect_error=422,
        )
        assert error["error"]["code"] == "VALIDATION_ERROR"

        error = _json_request(
            f"{base_url}/api/reports/missing/findings/f_001/review",
            method="PATCH",
            payload={"review_status": "needs_more_work"},
            expect_error=422,
        )
        assert error["error"]["code"] == "VALIDATION_ERROR"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def _finding() -> Finding:
    return Finding(
        finding_id="f_001",
        vulnerability_type="reentrancy",
        severity=3,
        location=Location(file="Vault.sol", function="withdraw", line_start=4, line_end=7),
        evidence="External call before state update.",
        reference=["SWC-107"],
        finding_confidence=1.0,
        explanation_confidence=1.0,
        explanation="Balance update happens after external call.",
        attack_path="Call withdraw recursively before balance is zero.",
        fix_suggestion="Move state update before external call.",
        remediation_code="balances[msg.sender] = 0;",
        vulnerable_code="msg.sender.call{value: amount}(\"\");",
        static_tool_source="slither",
        detector_name="reentrancy-eth",
        local_judge_score=5.0,
        external_judge_score=5.0,
        prompt_tokens=2,
        completion_tokens=3,
        total_tokens=5,
    )


def _json_request(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    expect_error: int | None = None,
) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            assert expect_error is None
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if expect_error is None:
            raise
        assert exc.code == expect_error
        return json.loads(exc.read().decode("utf-8"))


def _wait_for_terminal_job(base_url: str, analysis_id: str) -> dict[str, Any]:
    deadline = time.time() + 5
    while time.time() < deadline:
        job = _json_request(f"{base_url}/api/analyses/{analysis_id}")
        if job["status"] in {"finding", "no_finding", "partial_analysis", "error"}:
            return job
        time.sleep(0.05)
    raise AssertionError("analysis job did not reach a terminal status")


def _read_sse_events(url: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with urllib.request.urlopen(url, timeout=5) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            event = json.loads(line.removeprefix("data: "))
            events.append(event)
            if event["type"] in {"done", "error"}:
                return events
    return events
