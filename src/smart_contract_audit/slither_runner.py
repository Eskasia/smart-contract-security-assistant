from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import SUPPORTED_DETECTORS
from .solidity_target import (
    SolidityTarget,
    resolve_solidity_target,
    slither_command_args_for_target,
)


class SlitherRunError(RuntimeError):
    """Raised when deterministic static analysis cannot complete."""


@dataclass
class SlitherRunResult:
    raw_json: dict[str, Any]
    solc_version: str | None
    slither_version: str | None
    warnings: list[str]


def detect_pragma_version(source: str) -> str | None:
    match = re.search(r"pragma\s+solidity\s+([^;]+);", source)
    if not match:
        return None
    constraint = match.group(1)
    versions = re.findall(r"(\d+\.\d+\.\d+)", constraint)
    if versions:
        return versions[0]
    minor = re.search(r"(0\.[678])", constraint)
    if minor:
        return f"{minor.group(1)}.0"
    return None


def ensure_solc_version(version: str | None) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if version is None:
        return None, ["No pragma solidity version detected; Slither will use its default solc."]

    system_version = get_system_solc_version()
    if system_version and _compatible_solc(system_version, version):
        if system_version != version:
            warnings.append(f"Using system solc {system_version} for pragma-compatible {version}.")
        return system_version, warnings

    try:
        import solcx  # type: ignore[import-not-found]
    except ImportError:
        return version, ["py-solc-x is not installed; Slither will use any available solc."]

    try:
        installed = {str(v) for v in solcx.get_installed_solc_versions()}
        if version not in installed:
            solcx.install_solc(version)
        solcx.set_solc_version(version)
    except Exception as exc:  # pragma: no cover - depends on local solc network state
        raise SlitherRunError(f"Unable to prepare solc {version}: {exc}") from exc

    return version, warnings


def get_system_solc_version() -> str | None:
    if shutil.which("solc") is None:
        return None
    result = subprocess.run(
        ["solc", "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    text = result.stdout or result.stderr
    match = re.search(r"Version:\s+(\d+\.\d+\.\d+)", text)
    return match.group(1) if match else None


def _compatible_solc(system_version: str, requested_version: str) -> bool:
    system = _version_tuple(system_version)
    requested = _version_tuple(requested_version)
    if system is None or requested is None:
        return False
    return system[0] == requested[0] and system[1] == requested[1] and system[2] >= requested[2]


def _version_tuple(version: str) -> tuple[int, int, int] | None:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def get_slither_version() -> str | None:
    if shutil.which("slither") is None:
        return None
    result = subprocess.run(
        ["slither", "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    text = (result.stdout or result.stderr).strip()
    return text or None


def run_slither(contract_path: Path, timeout_seconds: int = 90) -> SlitherRunResult:
    if shutil.which("slither") is None:
        raise SlitherRunError("slither executable not found; install with `uv sync --extra audit`.")

    try:
        target = resolve_solidity_target(contract_path)
    except ValueError as exc:
        raise SlitherRunError(str(exc)) from exc

    source = target.combined_source
    solc_version, warnings = ensure_solc_version(detect_pragma_version(source))

    raw_results = [
        _run_slither_once(target, analysis_path, timeout_seconds)
        for analysis_path in _analysis_paths(target)
    ]

    return SlitherRunResult(
        raw_json=_merge_slither_results(raw_results),
        solc_version=solc_version,
        slither_version=get_slither_version(),
        warnings=warnings,
    )


def _analysis_paths(target: SolidityTarget) -> tuple[Path, ...]:
    if target.input_kind == "project_directory":
        return target.source_files
    return (target.analysis_path,)


def _run_slither_once(
    target: SolidityTarget, analysis_path: Path, timeout_seconds: int
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "slither.json"
        analysis_arg = analysis_path
        execution_root = Path.cwd().resolve()
        if analysis_path.is_relative_to(execution_root):
            analysis_arg = analysis_path.relative_to(execution_root)
        command = [
            "slither",
            str(analysis_arg),
            "--json",
            str(output_path),
            "--detect",
            ",".join(SUPPORTED_DETECTORS),
            *slither_command_args_for_target(target, execution_root),
        ]
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        raw_text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        if result.returncode != 0 and not raw_text.strip():
            stderr = result.stderr.strip() or result.stdout.strip()
            raise SlitherRunError(stderr or f"Slither failed with exit code {result.returncode}.")

        try:
            return json.loads(raw_text or "{}")
        except json.JSONDecodeError as exc:
            raise SlitherRunError(f"Slither returned invalid JSON: {exc}") from exc


def _merge_slither_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    merged_detectors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_json in results:
        detectors = raw_json.get("results", {}).get("detectors", []) or []
        for detector in detectors:
            key = json.dumps(detector, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            merged_detectors.append(detector)
            seen.add(key)
    return {
        "success": all(result.get("success", True) for result in results),
        "results": {"detectors": merged_detectors},
    }
