from __future__ import annotations

import json
import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from .models import ExternalToolResult

CommandRunner = Callable[[list[str], int], subprocess.CompletedProcess[str]]
BinaryResolver = Callable[[str], str | None]

TOOL_BINARIES = {
    "mythril": "myth",
    "echidna": "echidna",
}


def run_external_tools(
    target_path: Path,
    output_dir: Path,
    tools: tuple[str, ...] = (),
    timeout_seconds: int = 60,
    command_runner: CommandRunner | None = None,
    binary_resolver: BinaryResolver = shutil.which,
) -> list[ExternalToolResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    runner = command_runner or _run_command
    results = []
    for tool in tools:
        normalized_tool = tool.strip().lower()
        if not normalized_tool:
            continue
        if normalized_tool not in TOOL_BINARIES:
            results.append(_unsupported_tool(normalized_tool))
            continue
        results.append(
            _run_known_tool(
                normalized_tool,
                target_path,
                output_dir,
                timeout_seconds,
                runner,
                binary_resolver,
            )
        )
    return results


def _run_known_tool(
    tool_name: str,
    target_path: Path,
    output_dir: Path,
    timeout_seconds: int,
    command_runner: CommandRunner,
    binary_resolver: BinaryResolver,
) -> ExternalToolResult:
    binary_name = TOOL_BINARIES[tool_name]
    binary_path = binary_resolver(binary_name)
    if binary_path is None:
        return ExternalToolResult(
            tool_name=tool_name,
            command=[binary_name],
            status="skipped",
            findings_count=0,
            summary=f"{tool_name} not installed; skipped optional external analysis.",
        )

    command = _build_command(tool_name, binary_path, target_path)
    started = time.perf_counter()
    output_path = output_dir / f"{tool_name}.json"
    try:
        completed = command_runner(command, timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        return ExternalToolResult(
            tool_name=tool_name,
            command=command,
            status="error",
            findings_count=0,
            summary=f"{tool_name} exceeded {timeout_seconds} seconds.",
            error=str(exc),
            duration_ms=_elapsed_ms(started),
        )
    except OSError as exc:
        return ExternalToolResult(
            tool_name=tool_name,
            command=command,
            status="error",
            findings_count=0,
            summary=f"{tool_name} failed to start.",
            error=str(exc),
            duration_ms=_elapsed_ms(started),
        )

    raw_output = completed.stdout or completed.stderr
    output_path.write_text(raw_output, encoding="utf-8")
    findings_count = _count_findings(tool_name, raw_output)
    status = _tool_status(completed.returncode, findings_count)
    return ExternalToolResult(
        tool_name=tool_name,
        command=command,
        status=status,
        findings_count=findings_count,
        summary=_summary(tool_name, status, findings_count),
        output_path=str(output_path),
        error=completed.stderr if status == "error" else "",
        duration_ms=_elapsed_ms(started),
    )


def _unsupported_tool(tool_name: str) -> ExternalToolResult:
    return ExternalToolResult(
        tool_name=tool_name,
        command=[],
        status="skipped",
        findings_count=0,
        summary=f"{tool_name} is not supported by this integration.",
    )


def _build_command(tool_name: str, binary_path: str, target_path: Path) -> list[str]:
    if tool_name == "mythril":
        return [binary_path, "analyze", str(target_path), "-o", "json"]
    if tool_name == "echidna":
        return [binary_path, str(target_path), "--format", "json", "--test-limit", "500"]
    raise ValueError(f"Unsupported external tool: {tool_name}")


def _run_command(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )


def _count_findings(tool_name: str, raw_output: str) -> int:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return 0

    if tool_name == "mythril":
        return _count_mythril_issues(payload)
    if tool_name == "echidna":
        return _count_echidna_failures(payload)
    return 0


def _count_mythril_issues(payload: object) -> int:
    if isinstance(payload, dict):
        issues = payload.get("issues")
        return len(issues) if isinstance(issues, list) else 0
    if isinstance(payload, list):
        return len(payload)
    return 0


def _count_echidna_failures(payload: object) -> int:
    failures = 0
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            status = str(item.get("status", "")).lower()
            if status in {"failed", "fail", "falsified"}:
                failures += 1
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return failures


def _tool_status(returncode: int, findings_count: int) -> str:
    if findings_count > 0:
        return "finding"
    if returncode == 0:
        return "passed"
    return "error"


def _summary(tool_name: str, status: str, findings_count: int) -> str:
    if status == "finding":
        return f"{tool_name} reported {findings_count} issue(s)."
    if status == "passed":
        return f"{tool_name} completed without reported issues."
    return f"{tool_name} completed with an execution error."


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
