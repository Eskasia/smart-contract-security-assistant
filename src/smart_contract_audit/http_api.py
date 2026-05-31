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
from .external_tools import SUPPORTED_EXTERNAL_TOOLS
from .identifiers import require_safe_path_segment
from .models import FINDING_REVIEW_STATUSES, AnalysisReport
from .report import write_json_report, write_markdown_report
from .scoring.security_score import compute_security_score
from .source_import import (
    ImportedSource,
    ImportLimits,
    decode_archive_base64,
    import_explorer_source,
    import_github_source,
    stage_zip_archive,
)
from .trace.lookup import lookup_trace

AnalysisStatus = str
AnalysisEvent = dict[str, Any]
AnalyzerFn = Callable[..., AnalysisReport]

RAG_MODES = {"quality", "balanced", "fast", "fallback"}
NATIVE_BUILD_POLICIES = {"trusted", "disabled"}
EXTERNAL_TOOLS = SUPPORTED_EXTERNAL_TOOLS
REVIEW_STATUSES = {"pending_human_review", "approved", "rejected", "blocked"}
MAX_REVIEW_NOTE_LENGTH = 2_000
DEFAULT_EXTERNAL_TIMEOUT_SECONDS = 60
MIN_EXTERNAL_TIMEOUT_SECONDS = 5
MAX_EXTERNAL_TIMEOUT_SECONDS = 120


class RequestBodyTooLarge(ValueError):
    pass


@dataclass(frozen=True)
class ApiConfig:
    output_dir: Path = Path("reports-api")
    trace_db: Path | None = None
    input_root: Path | None = None
    imports_dir: Path | None = None
    api_token: str | None = None
    cors_origin: str = "http://127.0.0.1:5173"
    max_request_bytes: int = 1_048_576
    max_import_files: int = 128
    max_import_bytes: int = 5_000_000
    max_import_single_file_bytes: int = 1_000_000
    native_build_policy: str = "trusted"

    def resolved_trace_db(self) -> Path:
        return self.trace_db or self.output_dir / "analysis_trace.sqlite"

    def resolved_imports_dir(self) -> Path:
        return self.imports_dir or self.output_dir / "imports"

    def import_limits(self) -> ImportLimits:
        return ImportLimits(
            max_files=self.max_import_files,
            max_total_bytes=self.max_import_bytes,
            max_single_file_bytes=self.max_import_single_file_bytes,
        )


@dataclass
class AnalysisJob:
    analysis_id: str
    status: AnalysisStatus
    input_path: str
    rag_mode: str
    dataset_chunks: str | None
    model_path: str | None
    native_build_policy: str
    external_tools: tuple[str, ...]
    external_timeout_seconds: int
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
        request = _parse_create_analysis(
            payload,
            self.config.input_root,
            self.config.resolved_imports_dir(),
            self.config.native_build_policy,
        )
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
                external_tools=job.external_tools,
                external_timeout_seconds=job.external_timeout_seconds,
                native_build_policy=job.native_build_policy,
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
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        if not self._authorize_request():
            return
        path = _path_parts(self.path)
        try:
            payload = self._read_json_body()
            if path == ["api", "analyses"]:
                job = self.server.manager.create_job(payload)
                self._send_json(job.to_dict(), status=HTTPStatus.ACCEPTED)
                return
            if path == ["api", "imports"]:
                imported = self._create_import(payload)
                self._send_json(imported.to_dict(), status=HTTPStatus.CREATED)
                return
            self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")
        except RequestBodyTooLarge as exc:
            self._send_request_too_large_response(exc)
        except ValueError as exc:
            self._send_validation_error_response(str(exc))
        return

    def do_GET(self) -> None:
        if not self._authorize_request():
            return
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
        if len(path) == 4 and path[:2] == ["api", "reports"] and path[3] == "markdown":
            self._get_report_markdown(path[2])
            return
        if len(path) == 3 and path[:2] == ["api", "traces"]:
            finding_id = query.get("finding_id", [None])[0]
            self._get_trace(path[2], finding_id)
            return
        self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")

    def do_PATCH(self) -> None:
        if not self._authorize_request():
            return
        path = _path_parts(self.path)
        if len(path) == 4 and path[:2] == ["api", "reports"] and path[3] == "review":
            self._patch_review(path[2])
            return
        if (
            len(path) == 6
            and path[:2] == ["api", "reports"]
            and path[3] == "findings"
            and path[5] == "review"
        ):
            self._patch_finding_review(path[2], path[4])
            return
        self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _authorize_request(self) -> bool:
        token = self.server.config.api_token
        if not token:
            return True
        if self.headers.get("Authorization", "") == f"Bearer {token}":
            return True
        self._send_error_response(HTTPStatus.UNAUTHORIZED, "UNAUTHORIZED", "Invalid API token.")
        return False

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
        try:
            report = _read_report(self.server.config.output_dir, contract_id)
        except ValueError as exc:
            self._send_validation_error_response(str(exc))
            return
        if report is None:
            self._send_report_not_found_response()
            return
        self._send_json(report)

    def _get_report_markdown(self, contract_id: str) -> None:
        try:
            markdown = _read_report_markdown(self.server.config.output_dir, contract_id)
        except ValueError as exc:
            self._send_validation_error_response(str(exc))
            return
        if markdown is None:
            self._send_report_not_found_response()
            return
        safe_contract_id = require_safe_path_segment(contract_id, "contract_id")
        self._send_text(
            markdown,
            content_type="text/markdown; charset=utf-8",
            disposition=f'attachment; filename="{safe_contract_id}.md"',
        )

    def _get_trace(self, trace_id: str, finding_id: str | None) -> None:
        trace_db = self.server.config.resolved_trace_db()
        if not trace_db.exists():
            self._send_error_response(
                HTTPStatus.NOT_FOUND,
                "TRACE_DB_NOT_FOUND",
                "Trace database not found.",
            )
            return
        self._send_json(
            lookup_trace(
                trace_db,
                trace_id,
                finding_id,
                include_sensitive=False,
            )
        )

    def _patch_review(self, contract_id: str) -> None:
        try:
            payload = self._read_json_body()
            review_status = _parse_review_status(payload)
        except RequestBodyTooLarge as exc:
            self._send_request_too_large_response(exc)
            return
        except ValueError as exc:
            self._send_validation_error_response(str(exc))
            return

        try:
            report = _read_report(self.server.config.output_dir, contract_id)
        except ValueError as exc:
            self._send_validation_error_response(str(exc))
            return
        if report is None:
            self._send_report_not_found_response()
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

    def _patch_finding_review(self, contract_id: str, finding_id: str) -> None:
        try:
            payload = self._read_json_body()
            review_status, review_note = _parse_finding_review(payload)
        except RequestBodyTooLarge as exc:
            self._send_request_too_large_response(exc)
            return
        except ValueError as exc:
            self._send_validation_error_response(str(exc))
            return

        try:
            report = _read_report(self.server.config.output_dir, contract_id)
        except ValueError as exc:
            self._send_validation_error_response(str(exc))
            return
        if report is None:
            self._send_report_not_found_response()
            return

        finding = _update_report_finding_review(
            report,
            finding_id,
            review_status,
            review_note,
        )
        if finding is None:
            self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Finding not found.")
            return

        _refresh_report_security_score(report)
        _write_report_dict(self.server.config.output_dir, contract_id, report)
        trace_id = report.get("analysis_metadata", {}).get("analysis_trace_id")
        if isinstance(trace_id, str):
            _update_trace_finding_review(
                self.server.config.resolved_trace_db(),
                trace_id,
                finding_id,
                review_status,
                review_note,
            )
        self._send_json({"report": report, "finding": finding})

    def _read_json_body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length.") from exc
        if length > self.server.config.max_request_bytes:
            raise RequestBodyTooLarge("Request body exceeds max_request_bytes.")
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

    def _create_import(self, payload: dict[str, Any]) -> ImportedSource:
        source_kind = payload.get("source_kind")
        if source_kind not in {"zip_base64", "github_archive", "etherscan_api"}:
            raise ValueError(
                "source_kind must be one of: etherscan_api, github_archive, zip_base64."
            )

        destination_root = self.server.config.resolved_imports_dir()
        destination_root.mkdir(parents=True, exist_ok=True)
        limits = self.server.config.import_limits()

        if source_kind == "zip_base64":
            archive_base64 = payload.get("archive_base64")
            if not isinstance(archive_base64, str) or not archive_base64.strip():
                raise ValueError("archive_base64 must be a non-empty base64 string.")
            archive_bytes = decode_archive_base64(archive_base64)
            archive_name = payload.get("archive_name", "import.zip")
            if archive_name is None:
                archive_name = "import.zip"
            if not isinstance(archive_name, str):
                raise ValueError("archive_name must be a string or null.")
            return stage_zip_archive(
                archive_bytes,
                destination_root,
                import_name=Path(archive_name).stem or "import",
                source_kind="zip_base64",
                limits=limits,
            )

        if source_kind == "github_archive":
            url = payload.get("repository")
            if not isinstance(url, str) or not url.strip():
                raise ValueError("repository must be a non-empty string.")
            return import_github_source(
                url,
                destination_root,
                limits=limits,
            )

        api_host = payload.get("explorer_host")
        address = payload.get("contract_address")
        api_key = payload.get("api_key")
        if not isinstance(api_host, str) or not api_host.strip():
            raise ValueError("explorer_host must be a non-empty string.")
        if not isinstance(address, str) or not address.strip():
            raise ValueError("contract_address must be a non-empty string.")
        if api_key is not None and not isinstance(api_key, str):
            raise ValueError("api_key must be a string or null.")
        return import_explorer_source(
            api_host=api_host,
            address=address,
            destination_root=destination_root,
            api_key=api_key,
            limits=limits,
        )

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(
        self,
        body_text: str,
        *,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
        disposition: str | None = None,
    ) -> None:
        body = body_text.encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if disposition:
            self.send_header("Content-Disposition", disposition)
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

    def _send_request_too_large_response(self, exc: RequestBodyTooLarge) -> None:
        self._send_error_response(
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            "REQUEST_TOO_LARGE",
            str(exc),
        )

    def _send_validation_error_response(self, message: str) -> None:
        self._send_error_response(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            message,
        )

    def _send_report_not_found_response(self) -> None:
        self._send_error_response(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Report not found.")

    def _send_common_headers(self) -> None:
        origin = self.server.config.cors_origin
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
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
    input_root: Path | None = None,
    imports_dir: Path | None = None,
    api_token: str | None = None,
    cors_origin: str = "http://127.0.0.1:5173",
    max_request_bytes: int = 1_048_576,
    max_import_files: int = 128,
    max_import_bytes: int = 5_000_000,
    max_import_single_file_bytes: int = 1_000_000,
    native_build_policy: str = "trusted",
) -> None:
    server = create_api_server(
        host=host,
        port=port,
        config=ApiConfig(
            output_dir=output_dir,
            trace_db=trace_db,
            input_root=input_root,
            imports_dir=imports_dir,
            api_token=api_token,
            cors_origin=cors_origin,
            max_request_bytes=max_request_bytes,
            max_import_files=max_import_files,
            max_import_bytes=max_import_bytes,
            max_import_single_file_bytes=max_import_single_file_bytes,
            native_build_policy=native_build_policy,
        ),
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _parse_create_analysis(
    payload: dict[str, Any],
    input_root: Path | None = None,
    import_root: Path | None = None,
    default_native_build_policy: str = "trusted",
) -> dict[str, Any]:
    input_path = payload.get("input_path")
    if not isinstance(input_path, str) or not input_path.strip():
        raise ValueError("input_path must be a non-empty string.")
    input_path, imported_source = _validate_allowed_input_path(input_path, input_root, import_root)

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

    native_build_policy = payload.get("native_build_policy", default_native_build_policy)
    if native_build_policy not in NATIVE_BUILD_POLICIES:
        raise ValueError("native_build_policy must be one of: disabled, trusted.")
    if default_native_build_policy == "disabled" and native_build_policy == "trusted":
        raise ValueError("native_build_policy cannot override server disabled policy.")
    if imported_source:
        native_build_policy = "disabled"

    external_tools = _parse_external_tools(payload.get("external_tools"))
    if "halmos" in external_tools and native_build_policy == "disabled":
        raise ValueError("halmos requires native_build_policy trusted.")
    external_timeout_seconds = _parse_external_timeout_seconds(
        payload.get("external_timeout_seconds", DEFAULT_EXTERNAL_TIMEOUT_SECONDS)
    )

    return {
        "input_path": input_path,
        "rag_mode": rag_mode,
        "dataset_chunks": dataset_chunks,
        "model_path": model_path,
        "native_build_policy": str(native_build_policy),
        "external_tools": external_tools,
        "external_timeout_seconds": external_timeout_seconds,
    }


def _validate_allowed_input_path(
    input_path: str,
    input_root: Path | None,
    import_root: Path | None,
) -> tuple[str, bool]:
    resolved = Path(input_path).expanduser().resolve()
    resolved_import_root = import_root.expanduser().resolve() if import_root is not None else None
    imported_source = (
        resolved_import_root is not None and resolved.is_relative_to(resolved_import_root)
    )
    if input_root is None:
        return str(resolved), imported_source
    allowed_roots = [input_root.expanduser().resolve()]
    if resolved_import_root is not None:
        allowed_roots.append(resolved_import_root)
    if any(resolved.is_relative_to(root) for root in allowed_roots):
        return str(resolved), imported_source
    message = f"input_path must be inside input_root: {allowed_roots[0]}"
    if resolved_import_root is not None:
        message = f"{message} or imports_dir: {resolved_import_root}"
    raise ValueError(message)


def _parse_external_tools(value: Any) -> tuple[str, ...]:
    if value in (None, []):
        return ()
    if not isinstance(value, list):
        raise ValueError("external_tools must be an array of tool names.")

    parsed: list[str] = []
    seen: set[str] = set()
    for raw_tool in value:
        if not isinstance(raw_tool, str):
            raise ValueError("external_tools entries must be strings.")
        tool = raw_tool.strip().lower()
        if tool not in EXTERNAL_TOOLS:
            raise ValueError(
                "external_tools must contain only: aderyn, echidna, halmos, medusa, mythril."
            )
        if tool not in seen:
            seen.add(tool)
            parsed.append(tool)
    return tuple(parsed)


def _parse_external_timeout_seconds(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("external_timeout_seconds must be an integer.")
    return max(MIN_EXTERNAL_TIMEOUT_SECONDS, min(MAX_EXTERNAL_TIMEOUT_SECONDS, value))


def _parse_review_status(payload: dict[str, Any]) -> str:
    review_status = payload.get("review_status")
    if review_status not in REVIEW_STATUSES:
        raise ValueError(
            "review_status must be one of: approved, blocked, pending_human_review, rejected."
        )
    return str(review_status)


def _parse_finding_review(payload: dict[str, Any]) -> tuple[str, str]:
    review_status = payload.get("review_status")
    if review_status not in FINDING_REVIEW_STATUSES:
        raise ValueError(
            "review_status must be one of: accepted_risk, false_positive, fixed, "
            "true_positive, unreviewed."
        )

    review_note = payload.get("review_note", "")
    if review_note is None:
        review_note = ""
    if not isinstance(review_note, str):
        raise ValueError("review_note must be a string or null.")
    if len(review_note) > MAX_REVIEW_NOTE_LENGTH:
        raise ValueError("review_note must be 2000 characters or fewer.")

    return str(review_status), review_note


def _path_parts(path: str) -> list[str]:
    parsed = urlparse(path)
    return [unquote(part) for part in parsed.path.strip("/").split("/") if part]


def _read_report(output_dir: Path, contract_id: str) -> dict[str, Any] | None:
    report_text = _read_report_file_text(output_dir, contract_id, ".json")
    if report_text is None:
        return None
    return json.loads(report_text)


def _read_report_markdown(output_dir: Path, contract_id: str) -> str | None:
    return _read_report_file_text(output_dir, contract_id, ".md")


def _read_report_file_text(output_dir: Path, contract_id: str, suffix: str) -> str | None:
    report_path = _report_path(output_dir, contract_id, suffix)
    if not report_path.exists():
        return None
    return report_path.read_text(encoding="utf-8")


def _write_report_dict(output_dir: Path, contract_id: str, report: dict[str, Any]) -> None:
    report_path = _report_path(output_dir, contract_id, ".json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path = _report_path(output_dir, contract_id, ".md")
    if not markdown_path.exists():
        return
    _sync_markdown_report(markdown_path, report)


def _report_path(output_dir: Path, contract_id: str, suffix: str) -> Path:
    safe_contract_id = require_safe_path_segment(contract_id, "contract_id")
    output_root = output_dir.resolve()
    report_path = (output_root / f"{safe_contract_id}{suffix}").resolve()
    if not report_path.is_relative_to(output_root):
        raise ValueError("contract_id must resolve inside output_dir.")
    return report_path


def _update_report_finding_review(
    report: dict[str, Any],
    finding_id: str,
    review_status: str,
    review_note: str,
) -> dict[str, Any] | None:
    findings = report.get("findings")
    if not isinstance(findings, list):
        return None

    for finding in findings:
        if isinstance(finding, dict) and finding.get("finding_id") == finding_id:
            finding["review_status"] = review_status
            finding["review_note"] = review_note
            return finding
    return None


def _refresh_report_security_score(report: dict[str, Any]) -> None:
    findings = report.get("findings")
    if not isinstance(findings, list):
        findings = []
    metadata = report.get("analysis_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    result = compute_security_score(
        findings=findings,
        review_status=str(report.get("review_status", "pending_human_review")),
        partial_analysis=bool(metadata.get("partial_analysis", False)),
        business_logic_review_required=bool(
            report.get("business_logic_review_required", False)
        ),
    )
    report["security_score"] = result.score
    report["score_formula_version"] = result.formula_version
    report["score_factors"] = result.factors


def _sync_markdown_report(markdown_path: Path, report: dict[str, Any]) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    updated = [
        _update_markdown_summary_line(line, report)
        for line in lines
    ]
    findings = report.get("findings")
    if isinstance(findings, list):
        for finding in findings:
            if isinstance(finding, dict):
                updated = _upsert_finding_review_lines(updated, finding)
    markdown_path.write_text("\n".join(updated), encoding="utf-8")


def _update_markdown_summary_line(line: str, report: dict[str, Any]) -> str:
    if line.startswith("- Reviewer status: `"):
        return f"- Reviewer status: `{report['review_status']}`"
    if line.startswith("- Contract security score: `"):
        try:
            score = float(report.get("security_score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        return f"- Contract security score: `{score:.2f}/100`"
    if line.startswith("- Security score formula: `"):
        return f"- Security score formula: `{report.get('score_formula_version', '')}`"
    return line


def _upsert_finding_review_lines(
    lines: list[str],
    finding: dict[str, Any],
) -> list[str]:
    finding_id = finding.get("finding_id")
    if not isinstance(finding_id, str):
        return lines

    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith(f"### {finding_id}: ")
        ),
        None,
    )
    if start is None:
        return lines

    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("### ")
        ),
        len(lines),
    )
    review_status = str(finding.get("review_status", "unreviewed"))
    review_note = str(finding.get("review_note", ""))
    status_line = f"- Finding review status: `{review_status}`"
    note_line = f"- Finding review note: {review_note}"

    status_index = _find_line_index(lines, start, end, "- Finding review status:")
    if status_index is None:
        insert_at = _finding_review_insert_index(lines, start, end)
        lines.insert(insert_at, status_line)
        end += 1
        status_index = insert_at
    else:
        lines[status_index] = status_line

    note_index = _find_line_index(lines, start, end, "- Finding review note:")
    if review_note:
        if note_index is None:
            lines.insert(status_index + 1, note_line)
        else:
            lines[note_index] = note_line
    elif note_index is not None:
        del lines[note_index]

    return lines


def _find_line_index(
    lines: list[str],
    start: int,
    end: int,
    prefix: str,
) -> int | None:
    return next(
        (
            index
            for index in range(start, end)
            if lines[index].startswith(prefix)
        ),
        None,
    )


def _finding_review_insert_index(lines: list[str], start: int, end: int) -> int:
    detector_index = _find_line_index(lines, start, end, "- Detector:")
    if detector_index is not None:
        return detector_index + 1
    return min(start + 2, len(lines))


def _update_trace_review_status(trace_db: Path, trace_id: str, review_status: str) -> None:
    if not trace_db.exists():
        return
    with sqlite3.connect(trace_db) as conn:
        conn.execute(
            "UPDATE analysis_trace SET review_status = ? WHERE trace_id = ?",
            (review_status, trace_id),
        )
        conn.commit()


def _update_trace_finding_review(
    trace_db: Path,
    trace_id: str,
    finding_id: str,
    review_status: str,
    review_note: str,
) -> None:
    if not trace_db.exists():
        return

    with sqlite3.connect(trace_db) as conn:
        _ensure_trace_finding_review_columns(conn)
        row = conn.execute(
            """
            SELECT normalized_finding
            FROM trace_findings
            WHERE trace_id = ? AND finding_id = ?
            """,
            (trace_id, finding_id),
        ).fetchone()
        normalized_finding = _updated_normalized_finding(
            row[0] if row else None,
            review_status,
            review_note,
        )
        conn.execute(
            """
            UPDATE trace_findings
            SET review_status = ?, review_note = ?, normalized_finding = ?
            WHERE trace_id = ? AND finding_id = ?
            """,
            (
                review_status,
                review_note,
                normalized_finding,
                trace_id,
                finding_id,
            ),
        )
        conn.commit()


def _ensure_trace_finding_review_columns(conn: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(trace_findings)").fetchall()
    }
    if "review_status" not in columns:
        conn.execute(
            "ALTER TABLE trace_findings ADD COLUMN review_status TEXT DEFAULT 'unreviewed'"
        )
    if "review_note" not in columns:
        conn.execute("ALTER TABLE trace_findings ADD COLUMN review_note TEXT DEFAULT ''")


def _updated_normalized_finding(
    normalized_finding: str | None,
    review_status: str,
    review_note: str,
) -> str | None:
    if not normalized_finding:
        return normalized_finding
    try:
        payload = json.loads(normalized_finding)
    except json.JSONDecodeError:
        return normalized_finding
    if not isinstance(payload, dict):
        return normalized_finding
    payload["review_status"] = review_status
    payload["review_note"] = review_note
    return json.dumps(payload, ensure_ascii=False)
