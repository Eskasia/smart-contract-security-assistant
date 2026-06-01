from __future__ import annotations

import json
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .models import ExternalToolResult

CommandRunner = Callable[[list[str], int], subprocess.CompletedProcess[str]]
BinaryResolver = Callable[[str], str | None]


@dataclass(frozen=True)
class ExternalToolSpec:
    name: str
    binary: str
    execution_mode: str
    output_suffix: str
    command_builder: Callable[[str, Path, Path, int], list[str]]
    finding_counter: Callable[[str], int]
    artifact_builder: Callable[[str, Path, Path, int], dict[str, list[str]]] | None = None


def _mythril_command(binary_path: str, target_path: Path, _: Path, __: int) -> list[str]:
    return [binary_path, "analyze", str(target_path), "-o", "json"]


def _echidna_command(binary_path: str, target_path: Path, _: Path, __: int) -> list[str]:
    return [binary_path, str(target_path), "--format", "json", "--test-limit", "500"]


def _aderyn_command(binary_path: str, target_path: Path, output_path: Path, _: int) -> list[str]:
    return [binary_path, "--output", str(output_path), str(target_path)]


def _aderyn_artifact_commands(
    binary_path: str,
    target_path: Path,
    output_dir: Path,
    _: int,
) -> dict[str, list[str]]:
    sarif_path = output_dir / "aderyn.sarif"
    return {"sarif": [binary_path, "--output", str(sarif_path), str(target_path)]}


def _medusa_command(
    binary_path: str,
    target_path: Path,
    _: Path,
    timeout_seconds: int,
) -> list[str]:
    return [
        binary_path,
        "fuzz",
        "--compilation-target",
        str(target_path),
        "--timeout",
        str(timeout_seconds),
        "--test-limit",
        "500",
        "--no-color",
    ]


def _halmos_command(binary_path: str, target_path: Path, _: Path, __: int) -> list[str]:
    root = target_path if target_path.is_dir() else target_path.parent
    return [binary_path, "--root", str(root)]


TOOL_REGISTRY: dict[str, ExternalToolSpec] = {
    "mythril": ExternalToolSpec(
        name="mythril",
        binary="myth",
        execution_mode="symbolic",
        output_suffix=".json",
        command_builder=_mythril_command,
        finding_counter=lambda raw_output: _count_json_findings(raw_output, "mythril"),
    ),
    "echidna": ExternalToolSpec(
        name="echidna",
        binary="echidna",
        execution_mode="fuzzer",
        output_suffix=".json",
        command_builder=_echidna_command,
        finding_counter=lambda raw_output: _count_json_findings(raw_output, "echidna"),
    ),
    "aderyn": ExternalToolSpec(
        name="aderyn",
        binary="aderyn",
        execution_mode="read-only CLI",
        output_suffix=".json",
        command_builder=_aderyn_command,
        finding_counter=lambda raw_output: _count_json_findings(raw_output, "aderyn"),
        artifact_builder=_aderyn_artifact_commands,
    ),
    "medusa": ExternalToolSpec(
        name="medusa",
        binary="medusa",
        execution_mode="fuzzer",
        output_suffix=".json",
        command_builder=_medusa_command,
        finding_counter=lambda raw_output: _count_json_findings(raw_output, "medusa"),
    ),
    "halmos": ExternalToolSpec(
        name="halmos",
        binary="halmos",
        execution_mode="native build dependent",
        output_suffix=".txt",
        command_builder=_halmos_command,
        finding_counter=lambda raw_output: _count_halmos_failures(raw_output),
    ),
}
SUPPORTED_EXTERNAL_TOOLS = frozenset(TOOL_REGISTRY)


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
        spec = TOOL_REGISTRY.get(normalized_tool)
        if spec is None:
            results.append(_unsupported_tool(normalized_tool))
            continue
        results.append(
            _run_known_tool(
                spec,
                target_path,
                output_dir,
                timeout_seconds,
                runner,
                binary_resolver,
            )
        )
    return results


def _run_known_tool(
    spec: ExternalToolSpec,
    target_path: Path,
    output_dir: Path,
    timeout_seconds: int,
    command_runner: CommandRunner,
    binary_resolver: BinaryResolver,
) -> ExternalToolResult:
    binary_path = binary_resolver(spec.binary)
    if binary_path is None:
        return ExternalToolResult(
            tool_name=spec.name,
            command=[spec.binary],
            status="skipped",
            findings_count=0,
            summary=f"{spec.name} not installed; skipped optional external analysis.",
            execution_mode=spec.execution_mode,
            timeout_seconds=timeout_seconds,
        )

    output_path = output_dir / f"{spec.name}{spec.output_suffix}"
    command = spec.command_builder(binary_path, target_path, output_path, timeout_seconds)
    started = time.perf_counter()
    try:
        completed = command_runner(command, timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        return ExternalToolResult(
            tool_name=spec.name,
            command=command,
            status="error",
            findings_count=0,
            summary=f"{spec.name} exceeded {timeout_seconds} seconds.",
            execution_mode=spec.execution_mode,
            binary_path=binary_path,
            timeout_seconds=timeout_seconds,
            error=str(exc),
            duration_ms=_elapsed_ms(started),
        )
    except OSError as exc:
        return ExternalToolResult(
            tool_name=spec.name,
            command=command,
            status="error",
            findings_count=0,
            summary=f"{spec.name} failed to start.",
            execution_mode=spec.execution_mode,
            binary_path=binary_path,
            timeout_seconds=timeout_seconds,
            error=str(exc),
            duration_ms=_elapsed_ms(started),
        )

    raw_output = completed.stdout or completed.stderr
    if not output_path.exists() or raw_output:
        output_path.write_text(raw_output, encoding="utf-8")
    artifact_paths = _run_artifact_commands(
        spec,
        binary_path,
        target_path,
        output_dir,
        timeout_seconds,
        command_runner,
    )
    findings_count = spec.finding_counter(_read_tool_output(output_path, raw_output))
    status = _tool_status(completed.returncode, findings_count)
    return ExternalToolResult(
        tool_name=spec.name,
        command=command,
        status=status,
        findings_count=findings_count,
        summary=_summary(spec.name, status, findings_count),
        execution_mode=spec.execution_mode,
        binary_path=binary_path,
        timeout_seconds=timeout_seconds,
        output_path=str(output_path),
        artifact_paths=artifact_paths,
        error=completed.stderr if status == "error" else "",
        duration_ms=_elapsed_ms(started),
    )


def _run_artifact_commands(
    spec: ExternalToolSpec,
    binary_path: str,
    target_path: Path,
    output_dir: Path,
    timeout_seconds: int,
    command_runner: CommandRunner,
) -> dict[str, str]:
    if spec.artifact_builder is None:
        return {}
    artifacts: dict[str, str] = {}
    for artifact_name, command in spec.artifact_builder(
        binary_path, target_path, output_dir, timeout_seconds
    ).items():
        artifact_path = output_dir / f"{spec.name}.{artifact_name}"
        try:
            completed = command_runner(command, timeout_seconds)
        except (subprocess.TimeoutExpired, OSError):
            continue
        raw_output = completed.stdout or completed.stderr
        if raw_output or not artifact_path.exists():
            artifact_path.write_text(raw_output, encoding="utf-8")
        artifacts[artifact_name] = str(artifact_path)
    return artifacts


def _read_tool_output(output_path: Path, fallback: str) -> str:
    if output_path.exists():
        return output_path.read_text(encoding="utf-8", errors="replace")
    return fallback


def _unsupported_tool(tool_name: str) -> ExternalToolResult:
    return ExternalToolResult(
        tool_name=tool_name,
        command=[],
        status="skipped",
        findings_count=0,
        summary=f"{tool_name} is not supported by this integration.",
        execution_mode="unsupported",
    )


def _run_command(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )


def _count_json_findings(raw_output: str, tool_name: str) -> int:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        if tool_name in {"medusa", "halmos"}:
            return _count_text_failures(raw_output)
        return 0

    if tool_name == "mythril":
        return _count_mythril_issues(payload)
    if tool_name == "echidna":
        return _count_echidna_failures(payload)
    if tool_name == "aderyn":
        return len(_aderyn_issues(payload))
    if tool_name == "medusa":
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


def _aderyn_issues(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        for key in ("issues", "detectors", "results", "findings"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        high_issues = payload.get("high_issues")
        low_issues = payload.get("low_issues")
        issues = []
        if isinstance(high_issues, list):
            issues.extend(item for item in high_issues if isinstance(item, dict))
        if isinstance(low_issues, list):
            issues.extend(item for item in low_issues if isinstance(item, dict))
        return issues
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _count_halmos_failures(raw_output: str) -> int:
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return _count_text_failures(raw_output)
    if isinstance(payload, dict):
        for key in ("failures", "counterexamples", "errors", "failed"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
            if isinstance(value, int):
                return max(0, value)
    return _count_echidna_failures(payload)


def _count_text_failures(raw_output: str) -> int:
    lowered = raw_output.lower()
    markers = ("counterexample", "falsified", "failed", "failure", "assertion violation")
    return sum(lowered.count(marker) for marker in markers)


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
