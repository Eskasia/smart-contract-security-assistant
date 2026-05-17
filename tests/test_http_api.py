from __future__ import annotations

import base64
import io
import json
import threading
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import smart_contract_audit.http_api as http_api_module
from smart_contract_audit.http_api import ApiConfig, create_api_server
from smart_contract_audit.models import AnalysisMetadata, AnalysisReport, Finding, Location
from smart_contract_audit.source_import import ImportedSource
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
        assert trace_rows[0]["packed_prompt"] is None
        assert trace_rows[0]["slither_raw"] is None
        assert trace_rows[0]["llm_raw_output"] is None
        assert trace_rows[0]["sensitive_fields_redacted"] is True

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
            f"{base_url}/api/imports",
            method="POST",
            payload={"source_kind": "zip_base64"},
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


def test_http_api_requires_token_when_configured(tmp_path: Path) -> None:
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=tmp_path / "reports", api_token="dev-token"),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": "Vault.sol"},
            expect_error=401,
        )
        assert error["error"]["code"] == "UNAUTHORIZED"

        created = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": "Vault.sol", "rag_mode": "slow"},
            headers={"Authorization": "Bearer dev-token"},
            expect_error=422,
        )
        assert created["error"]["code"] == "VALIDATION_ERROR"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_rejects_oversized_json_body(tmp_path: Path) -> None:
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=tmp_path / "reports", max_request_bytes=8),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": "Vault.sol"},
            expect_error=413,
        )
        assert error["error"]["code"] == "REQUEST_TOO_LARGE"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_rejects_input_outside_allowed_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside" / "Vault.sol"
    allowed.mkdir()
    outside.parent.mkdir()
    outside.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")

    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=tmp_path / "reports", input_root=allowed),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": str(outside)},
            expect_error=422,
        )
        assert error["error"]["code"] == "VALIDATION_ERROR"
        assert "input_root" in error["error"]["message"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_rejects_native_build_policy_upgrade(tmp_path: Path) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(
            output_dir=tmp_path / "reports",
            native_build_policy="disabled",
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={
                "input_path": str(contract),
                "native_build_policy": "trusted",
            },
            expect_error=422,
        )
        assert error["error"]["code"] == "VALIDATION_ERROR"
        assert "native_build_policy" in error["error"]["message"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_imports_archive_and_passes_external_tool_settings(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    analyzer_calls: list[dict[str, Any]] = []

    def fake_analyzer(**kwargs: Any) -> AnalysisReport:
        analyzer_calls.append(kwargs)
        return AnalysisReport(
            report_version="1.0",
            overall_status="no_finding",
            contract_id="contract_api_002",
            review_status="pending_human_review",
            requires_human_review=True,
            business_logic_review_required=False,
            review_reason="Human review required.",
            findings=[],
            analysis_metadata=AnalysisMetadata(
                dataset_version="dataset_v1",
                model_version="fallback",
                solc_version="0.8.34",
                slither_version="0.11.5",
                partial_analysis=False,
                analysis_trace_id="trace_002",
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
        imported = _json_request(
            f"{base_url}/api/imports",
            method="POST",
            payload={
                "source_kind": "zip_base64",
                "archive_base64": base64.b64encode(
                    _zip_bytes(
                        {
                            "repo-main/Vault.sol": (
                                "pragma solidity ^0.8.19; contract Vault {}"
                            )
                        }
                    )
                ).decode("ascii"),
            },
        )
        staged_path = Path(imported["input_path"])
        assert staged_path.exists()
        assert staged_path.is_file()
        assert staged_path.is_relative_to(output_dir.resolve() / "imports")
        assert imported["imported"] is True
        assert imported["trust_level"] == "untrusted"

        created = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={
                "input_path": imported["input_path"],
                "external_tools": ["echidna", "echidna", "mythril"],
                "external_timeout_seconds": 999,
                "native_build_policy": "trusted",
            },
        )
        job = _wait_for_terminal_job(base_url, created["analysis_id"])
        assert job["status"] == "no_finding"
        assert analyzer_calls
        assert analyzer_calls[0]["contract_path"] == staged_path
        assert analyzer_calls[0]["external_tools"] == ("echidna", "mythril")
        assert analyzer_calls[0]["external_timeout_seconds"] == 120
        assert analyzer_calls[0]["native_build_policy"] == "disabled"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_imports_remote_payload_contracts(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "reports"
    calls: list[dict[str, Any]] = []

    def fake_import_github_source(
        repository: str,
        destination_root: Path,
        *,
        limits: Any = None,
    ) -> ImportedSource:
        calls.append(
            {
                "kind": "github",
                "repository": repository,
                "destination_root": destination_root,
                "limits": limits,
            }
        )
        return _imported_source(destination_root, "github_archive")

    def fake_import_explorer_source(
        *,
        api_host: str,
        address: str,
        destination_root: Path,
        api_key: str | None = None,
        limits: Any = None,
    ) -> ImportedSource:
        calls.append(
            {
                "kind": "etherscan",
                "api_host": api_host,
                "address": address,
                "api_key": api_key,
                "destination_root": destination_root,
                "limits": limits,
            }
        )
        return _imported_source(destination_root, "etherscan_api")

    monkeypatch.setattr(
        http_api_module,
        "import_github_source",
        fake_import_github_source,
    )
    monkeypatch.setattr(
        http_api_module,
        "import_explorer_source",
        fake_import_explorer_source,
    )

    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=output_dir),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        github = _json_request(
            f"{base_url}/api/imports",
            method="POST",
            payload={
                "source_kind": "github_archive",
                "repository": "https://github.com/example/audit-target",
            },
        )
        etherscan = _json_request(
            f"{base_url}/api/imports",
            method="POST",
            payload={
                "source_kind": "etherscan_api",
                "contract_address": "0x1111111111111111111111111111111111111111",
                "explorer_host": "api.etherscan.io",
                "api_key": "scan-token",
            },
        )

        assert github["source_kind"] == "github_archive"
        assert etherscan["source_kind"] == "etherscan_api"
        assert calls[0]["repository"] == "https://github.com/example/audit-target"
        assert calls[0]["destination_root"] == output_dir.resolve() / "imports"
        assert calls[1]["address"] == "0x1111111111111111111111111111111111111111"
        assert calls[1]["api_host"] == "api.etherscan.io"
        assert calls[1]["api_key"] == "scan-token"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_uses_configured_cors_origin(tmp_path: Path) -> None:
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(
            output_dir=tmp_path / "reports",
            cors_origin="http://127.0.0.1:5173",
        ),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        request = urllib.request.Request(
            f"{base_url}/api/analyses",
            method="OPTIONS",
            headers={"Origin": "http://127.0.0.1:5173"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
            assert response.headers["Access-Control-Allow-Headers"] == (
                "Authorization, Content-Type"
            )
            assert response.headers["Vary"] == "Origin"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_rejects_path_like_report_id(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    escaped_report = tmp_path / "escape.json"
    escaped_report.write_text(json.dumps({"contract_id": "escape"}), encoding="utf-8")
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=output_dir),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/reports/..%2Fescape",
            expect_error=422,
        )
        assert error["error"]["code"] == "VALIDATION_ERROR"
        assert "contract_id" in error["error"]["message"]
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
    headers: dict[str, str] | None = None,
) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=request_headers,
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


def _zip_bytes(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _imported_source(destination_root: Path, source_kind: str) -> ImportedSource:
    staging_dir = destination_root / source_kind
    staging_dir.mkdir(parents=True, exist_ok=True)
    input_path = staging_dir / "Vault.sol"
    input_path.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")
    return ImportedSource(
        import_id=f"import_{source_kind}",
        source_kind=source_kind,
        input_path=input_path,
        staging_dir=staging_dir,
        extracted_files=("Vault.sol",),
        total_bytes=input_path.stat().st_size,
    )
