from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field, replace
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .analyzer import analyze_contract
from .models import AnalysisReport
from .report import write_json_report, write_markdown_report
from .trace.lookup import lookup_trace

AnalysisStatus = str
AnalysisEvent = dict[str, Any]
AnalyzerFn = Callable[..., AnalysisReport]

RAG_MODES = {"quality", "balanced", "fast", "fallback"}
REVIEW_STATUSES = {"pending_human_review", "approved", "rejected", "blocked"}


@dataclass(frozen=True)
class ApiConfig:
    output_dir: Path = Path("reports-api")
    trace_db: Path | None = None

    def resolved_trace_db(self) -> Path:
        return self.trace_db or self.output_dir / "analysis_trace.sqlite"


@dataclass
class AnalysisJob:
    analysis_id: str
    status: AnalysisStatus
    input_path: str
    rag_mode: str
    dataset_chunks: str | None
    model_path: str | None
    message: str | None = None
    report_id: str | None = None
    contract_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "analysis_id": self.analysis_id,
            "status": self.status,
        }
        for key in ("message", "report_id", "contract_id"):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        return payload


@dataclass
class _JobRecord:
    job: AnalysisJob
    events: list[AnalysisEvent] = field(default_factory=list)


class AnalysisJobManager:
    def __init__(
        self,
        config: ApiConfig,
        analyzer: AnalyzerFn = analyze_contract,
    ) -> None:
        self.config = config
        self.analyzer = analyzer
        self._condition = threading.Condition()
        self._jobs: dict[str, _JobRecord] = {}

    def create_job(self, payload: dict[str, Any]) -> AnalysisJob:
        request = _parse_create_analysis(payload)
        analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"
        job = AnalysisJob(analysis_id=analysis_id, status="queued", **request)
        response_job = replace(job)
        with self._condition:
            self._jobs[analysis_id] = _JobRecord(job=job)
            self._append_event_locked(
                analysis_id,
                {"type": "status", "status": "queued", "message": "Analysis queued."},
            )
        thread = threading.Thread(target=self._run_job, args=(analysis_id,), daemon=True)
        thread.start()
        return response_job

    def get_job(self, analysis_id: str) -> AnalysisJob | None:
        with self._condition:
            record = self._jobs.get(analysis_id)
            if record is None:
                return None
            return record.job

    def iter_events(self, analysis_id: str) -> Iterator[AnalysisEvent] | None:
        with self._condition:
            if analysis_id not in self._jobs:
                return None
        return self._event_iterator(analysis_id)

    def _event_iterator(self, analysis_id: str) -> Iterator[AnalysisEvent]:
        cursor = 0
        while True:
            with self._condition:
                while True:
                    record = self._jobs.get(analysis_id)
                    if record is None:
                        return
                    if cursor < len(record.events):
                        event = record.events[cursor]
                        cursor += 1
                        break
                    self._condition.wait(timeout=15)
            yield event
            if event.get("type") in {"done", "error"}:
                return

    def _run_job(self, analysis_id: str) -> None:
        with self._condition:
            record = self._jobs[analysis_id]
            record.job.status = "running"
            self._append_event_locked(
                analysis_id,
                {"type": "status", "status": "running", "message": "Analysis running."},
            )
            job = record.job

        try:
            output_dir = self.config.output_dir
            report = self.analyzer(
                contract_path=Path(job.input_path),
                output_dir=output_dir,
                trace_db=self.config.resolved_trace_db(),
                dataset_chunks=Path(job.dataset_chunks) if job.dataset_chunks else None,
                rag_mode=job.rag_mode,
                model_path=job.model_path,
            )
            write_json_report(report, output_dir / f"{report.contract_id}.json")
            write_markdown_report(report, output_dir / f"{report.contract_id}.md")
        except Exception as exc:  # pragma: no cover - exact analyzer failures vary by host.
            message = str(exc) or exc.__class__.__name__
            with self._condition:
                record = self._jobs[analysis_id]
                record.job.status = "error"
                record.job.message = message
                self._append_event_locked(
                    analysis_id,
                    {"type": "error", "status": "error", "message": message},
                )
            return

        with self._condition:
            record = self._jobs[analysis_id]
            record.job.status = report.overall_status
            record.job.contract_id = report.contract_id
            record.job.report_id = report.contract_id
            record.job.message = f"Analysis finished with status {report.overall_status}."
            for finding in report.findings:
                self._append_event_locked(
                    analysis_id,
                    {"type": "finding_complete", "finding": finding.to_dict()},
                )
            self._append_event_locked(
                analysis_id,
                {
                    "type": "done",
                    "status": report.overall_status,
                    "report_id": report.contract_id,
                    "contract_id": report.contract_id,
                },
            )

    def _append_event_locked(self, analysis_id: str, event: AnalysisEvent) -> None:
        self._jobs[analysis_id].events.append(event)
        self._condition.notify_all()


class _SmartContractAPIServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        config: ApiConfig,
        analyzer: AnalyzerFn,
    ) -> None:
        self.config = config
        self.manager = AnalysisJobManager(config, analyzer)
        super().__init__(server_address, _SmartContractAPIHandler)


class _SmartContractAPIHandler(BaseHTTPRequestHandler):
    server: _SmartContractAPIServer

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        path = _path_parts(self.path)
        if path != ["api", "analyses"]:
            self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")
            return
        try:
            payload = self._read_json_body()
            job = self.server.manager.create_job(payload)
        except ValueError as exc:
            self._send_error_response(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                str(exc),
            )
            return
        self._send_json(job.to_dict(), status=HTTPStatus.ACCEPTED)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
        query = parse_qs(parsed.query)

        if len(path) == 3 and path[:2] == ["api", "analyses"]:
            self._get_analysis(path[2])
            return
        if len(path) == 4 and path[:2] == ["api", "analyses"] and path[3] == "stream":
            self._stream_analysis(path[2])
            return
        if len(path) == 3 and path[:2] == ["api", "reports"]:
            self._get_report(path[2])
            return
        if len(path) == 3 and path[:2] == ["api", "traces"]:
            finding_id = query.get("finding_id", [None])[0]
            self._get_trace(path[2], finding_id)
            return
        self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")

    def do_PATCH(self) -> None:
        path = _path_parts(self.path)
        if len(path) == 4 and path[:2] == ["api", "reports"] and path[3] == "review":
            self._patch_review(path[2])
            return
        self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _get_analysis(self, analysis_id: str) -> None:
        job = self.server.manager.get_job(analysis_id)
        if job is None:
            self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Analysis not found.")
            return
        self._send_json(job.to_dict())

    def _stream_analysis(self, analysis_id: str) -> None:
        events = self.server.manager.iter_events(analysis_id)
        if events is None:
            self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Analysis not found.")
            return

        self.send_response(HTTPStatus.OK)
        self._send_common_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            for event in events:
                payload = json.dumps(event, ensure_ascii=False)
                self.wfile.write(f"data: {payload}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return

    def _get_report(self, contract_id: str) -> None:
        report = _read_report(self.server.config.output_dir, contract_id)
        if report is None:
            self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Report not found.")
            return
        self._send_json(report)

    def _get_trace(self, trace_id: str, finding_id: str | None) -> None:
        trace_db = self.server.config.resolved_trace_db()
        if not trace_db.exists():
            self._send_error_response(
                HTTPStatus.NOT_FOUND,
                "TRACE_DB_NOT_FOUND",
                "Trace database not found.",
            )
            return
        self._send_json(lookup_trace(trace_db, trace_id, finding_id))

    def _patch_review(self, contract_id: str) -> None:
        try:
            payload = self._read_json_body()
            review_status = _parse_review_status(payload)
        except ValueError as exc:
            self._send_error_response(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "VALIDATION_ERROR",
                str(exc),
            )
            return

        report = _read_report(self.server.config.output_dir, contract_id)
        if report is None:
            self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Report not found.")
            return

        report["review_status"] = review_status
        _write_report_dict(self.server.config.output_dir, contract_id, report)
        trace_id = report.get("analysis_metadata", {}).get("analysis_trace_id")
        if isinstance(trace_id, str):
            _update_trace_review_status(
                self.server.config.resolved_trace_db(),
                trace_id,
                review_status,
            )
        self._send_json({"report": report})

    def _read_json_body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length.") from exc
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_response(
        self,
        status: HTTPStatus,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        error: dict[str, Any] = {"code": code, "message": message}
        if details is not None:
            error["details"] = details
        self._send_json({"error": error}, status=status)

    def _send_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Content-Type-Options", "nosniff")


def create_api_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    config: ApiConfig | None = None,
    analyzer: AnalyzerFn = analyze_contract,
) -> ThreadingHTTPServer:
    resolved_config = config or ApiConfig()
    resolved_config.output_dir.mkdir(parents=True, exist_ok=True)
    return _SmartContractAPIServer((host, port), resolved_config, analyzer)


def run_api_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    output_dir: Path = Path("reports-api"),
    trace_db: Path | None = None,
) -> None:
    server = create_api_server(host=host, port=port, config=ApiConfig(output_dir, trace_db))
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _parse_create_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    input_path = payload.get("input_path")
    if not isinstance(input_path, str) or not input_path.strip():
        raise ValueError("input_path must be a non-empty string.")

    rag_mode = payload.get("rag_mode", "balanced")
    if rag_mode not in RAG_MODES:
        raise ValueError("rag_mode must be one of: balanced, fallback, fast, quality.")

    dataset_chunks = payload.get("dataset_chunks")
    if dataset_chunks in ("", None):
        dataset_chunks = None
    if dataset_chunks is not None and not isinstance(dataset_chunks, str):
        raise ValueError("dataset_chunks must be a string or null.")

    model_path = payload.get("model_path")
    if model_path in ("", None):
        model_path = None
    if model_path is not None and not isinstance(model_path, str):
        raise ValueError("model_path must be a string or null.")

    return {
        "input_path": input_path,
        "rag_mode": rag_mode,
        "dataset_chunks": dataset_chunks,
        "model_path": model_path,
    }


def _parse_review_status(payload: dict[str, Any]) -> str:
    review_status = payload.get("review_status")
    if review_status not in REVIEW_STATUSES:
        raise ValueError(
            "review_status must be one of: approved, blocked, pending_human_review, rejected."
        )
    return str(review_status)


def _path_parts(path: str) -> list[str]:
    parsed = urlparse(path)
    return [unquote(part) for part in parsed.path.strip("/").split("/") if part]


def _read_report(output_dir: Path, contract_id: str) -> dict[str, Any] | None:
    report_path = output_dir / f"{contract_id}.json"
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))


def _write_report_dict(output_dir: Path, contract_id: str, report: dict[str, Any]) -> None:
    report_path = output_dir / f"{contract_id}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path = output_dir / f"{contract_id}.md"
    if not markdown_path.exists():
        return
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    updated = [
        f"- Reviewer status: `{report['review_status']}`"
        if line.startswith("- Reviewer status: `")
        else line
        for line in lines
    ]
    markdown_path.write_text("\n".join(updated), encoding="utf-8")


def _update_trace_review_status(trace_db: Path, trace_id: str, review_status: str) -> None:
    if not trace_db.exists():
        return
    with sqlite3.connect(trace_db) as conn:
        conn.execute(
            "UPDATE analysis_trace SET review_status = ? WHERE trace_id = ?",
            (review_status, trace_id),
        )
        conn.commit()
