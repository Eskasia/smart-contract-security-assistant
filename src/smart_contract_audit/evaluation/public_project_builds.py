from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from smart_contract_audit.analyzer import analyze_contract
from smart_contract_audit.models import AnalysisReport

Analyzer = Callable[..., AnalysisReport]
BinaryResolver = Callable[[str], str | None]
DependencyPreparer = Callable[[Path], list[str]]


class PublicProjectBuildFailure(RuntimeError):
    pass


def preflight_public_project_builds(
    manifest_path: Path,
    tool_resolver: BinaryResolver = shutil.which,
) -> dict[str, Any]:
    cases = json.loads(manifest_path.read_text(encoding="utf-8"))
    framework_hints: dict[str, int] = {}
    for case in cases:
        hint = str(case.get("framework_hint", "unknown"))
        framework_hints[hint] = framework_hints.get(hint, 0) + 1
    native_tool_availability = _native_tool_availability(tool_resolver)
    missing_required_tools = _missing_required_tools(framework_hints, native_tool_availability)
    return {
        "cases": len(cases),
        "framework_hints": dict(sorted(framework_hints.items())),
        "native_tool_availability": native_tool_availability,
        "missing_required_tools": missing_required_tools,
    }


def run_public_project_builds(
    manifest_path: Path,
    workspace_dir: Path,
    reports_dir: Path,
    rag_mode: str = "fallback",
    min_analyzer_success_rate: float = 0.0,
    min_native_build_success_rate: float = 0.0,
    analyzer: Analyzer = analyze_contract,
    tool_resolver: BinaryResolver = shutil.which,
    dependency_preparer: DependencyPreparer | None = None,
) -> dict[str, Any]:
    cases = json.loads(manifest_path.read_text(encoding="utf-8"))
    workspace_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    dependency_preparer = dependency_preparer or prepare_project_dependencies
    results = [
        _run_case(case, workspace_dir, reports_dir, rag_mode, analyzer, dependency_preparer)
        for case in cases
    ]
    summary = _summarize(results, tool_resolver)
    (reports_dir / "public_project_builds_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _enforce_thresholds(
        summary,
        min_analyzer_success_rate,
        min_native_build_success_rate,
    )
    return summary


def _run_case(
    case: dict[str, Any],
    workspace_dir: Path,
    reports_dir: Path,
    rag_mode: str,
    analyzer: Analyzer,
    dependency_preparer: DependencyPreparer,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    try:
        project_path = _project_path(case, workspace_dir)
        dependency_messages = dependency_preparer(project_path)
        report = analyzer(
            project_path,
            output_dir=reports_dir / case_id,
            rag_mode=rag_mode,
        ).to_dict()
        errors = report.get("analysis_metadata", {}).get("errors", [])
        overall_status = str(report.get("overall_status", "error"))
        return {
            "case_id": case_id,
            "repo_url": case.get("repo_url", ""),
            "ref": case.get("ref", ""),
            "project_path": str(project_path),
            "overall_status": overall_status,
            "analyzer_succeeded": overall_status
            in {"finding", "no_finding", "partial_analysis"},
            "native_build_succeeded": _native_build_succeeded(errors),
            "native_build_blocker": _native_build_blocker(errors),
            "dependency_preparation": dependency_messages,
            "errors": errors,
        }
    except Exception as exc:
        return {
            "case_id": case_id,
            "repo_url": case.get("repo_url", ""),
            "ref": case.get("ref", ""),
            "project_path": "",
            "overall_status": "error",
            "analyzer_succeeded": False,
            "native_build_succeeded": False,
            "native_build_blocker": "analysis_error",
            "dependency_preparation": [],
            "errors": [str(exc)],
        }


def prepare_project_dependencies(project_path: Path, timeout_seconds: int = 600) -> list[str]:
    messages: list[str] = []
    if (project_path / ".gitmodules").exists():
        _run_prepare_command(
            ["git", "submodule", "update", "--init", "--recursive", "--depth", "1"],
            project_path,
            timeout_seconds,
            "git submodule update",
        )
        messages.append("git submodules initialized before native build.")

    package_path = project_path / "package.json"
    if package_path.exists() and not (project_path / "node_modules").exists():
        _run_first_prepare_command(
            _dependency_install_commands(project_path),
            project_path,
            timeout_seconds,
            "npm dependency install",
        )
        messages.append("npm dependencies installed before native build.")
    return messages


def _dependency_install_commands(project_path: Path) -> list[list[str]]:
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("npm executable not found; cannot install project dependencies.")
    common = ["--ignore-scripts", "--no-audit", "--no-fund", "--engine-strict=false"]
    fallback = [*common, "--legacy-peer-deps"]
    if (project_path / "package-lock.json").exists():
        return [[npm, "ci", *common], [npm, "ci", *fallback]]
    return [[npm, "install", *common], [npm, "install", *fallback]]


def _run_first_prepare_command(
    commands: list[list[str]],
    cwd: Path,
    timeout_seconds: int,
    label: str,
) -> None:
    failures: list[str] = []
    for command in commands:
        try:
            _run_prepare_command(command, cwd, timeout_seconds, label)
            return
        except RuntimeError as exc:
            failures.append(str(exc))
    detail = failures[-1] if failures else "no install command available"
    raise RuntimeError(detail)


def _run_prepare_command(
    command: list[str],
    cwd: Path,
    timeout_seconds: int,
    label: str,
) -> None:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"{label} failed: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        reason = detail[-1] if detail else f"exit code {result.returncode}"
        raise RuntimeError(f"{label} failed: {reason}")


def _project_path(case: dict[str, Any], workspace_dir: Path) -> Path:
    local_path = case.get("local_path")
    if local_path:
        path = Path(str(local_path)).resolve()
        subdir = str(case.get("project_path", "")).strip()
        return path / subdir if subdir else path

    repo_url = str(case["repo_url"])
    checkout_dir = workspace_dir / str(case["case_id"])
    if not checkout_dir.exists():
        ref = str(case.get("ref", "")).strip()
        _clone_project(repo_url, checkout_dir, ref)

    project_subdir = str(case.get("project_path", "")).strip()
    return checkout_dir / project_subdir if project_subdir else checkout_dir


def _clone_project(repo_url: str, checkout_dir: Path, ref: str) -> None:
    if _looks_like_commit_ref(ref):
        subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", repo_url, str(checkout_dir)],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        subprocess.run(
            ["git", "-C", str(checkout_dir), "fetch", "--depth", "1", "origin", ref],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        subprocess.run(
            ["git", "-C", str(checkout_dir), "checkout", "--detach", ref],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return

    command = ["git", "clone", "--depth", "1"]
    if ref:
        command.extend(["--branch", ref])
    command.extend([repo_url, str(checkout_dir)])
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)


def _looks_like_commit_ref(ref: str) -> bool:
    return re.fullmatch(r"[0-9a-fA-F]{40}", ref) is not None


def _summarize(
    results: list[dict[str, Any]],
    tool_resolver: BinaryResolver,
) -> dict[str, Any]:
    cases = len(results)
    analyzer_successes = sum(1 for result in results if result["analyzer_succeeded"])
    native_build_successes = sum(1 for result in results if result["native_build_succeeded"])
    native_tool_availability = _native_tool_availability(tool_resolver)
    return {
        "cases": cases,
        "successful_analyzer_runs": analyzer_successes,
        "native_build_successes": native_build_successes,
        "analyzer_success_rate": round(analyzer_successes / cases, 4) if cases else 0.0,
        "native_build_success_rate": (
            round(native_build_successes / cases, 4) if cases else 0.0
        ),
        "native_tool_availability": native_tool_availability,
        "native_build_tool_missing_cases": sum(
            1 for result in results if result["native_build_blocker"] == "tool_missing"
        ),
        "native_build_failed_cases": sum(
            1 for result in results if result["native_build_blocker"] == "build_failed"
        ),
        "results": results,
    }


def _native_build_succeeded(errors: object) -> bool:
    if not isinstance(errors, list):
        return False
    return any("native build completed before Slither" in str(error) for error in errors)


def _native_build_blocker(errors: object) -> str:
    if not isinstance(errors, list):
        return ""
    text = "\n".join(str(error) for error in errors)
    if "native build tool not found" in text:
        return "tool_missing"
    if "native build failed" in text:
        return "build_failed"
    return ""


def _native_tool_availability(tool_resolver: BinaryResolver) -> dict[str, bool]:
    return {
        "forge": tool_resolver("forge") is not None,
        "npx": tool_resolver("npx") is not None,
    }


def _missing_required_tools(
    framework_hints: dict[str, int],
    native_tool_availability: dict[str, bool],
) -> list[str]:
    required: set[str] = set()
    for hint, count in framework_hints.items():
        if count <= 0:
            continue
        if "foundry" in hint:
            required.add("forge")
        if "hardhat" in hint:
            required.add("npx")
    return sorted(tool for tool in required if not native_tool_availability.get(tool, False))


def _enforce_thresholds(
    summary: dict[str, Any],
    min_analyzer_success_rate: float,
    min_native_build_success_rate: float,
) -> None:
    analyzer_rate = float(summary["analyzer_success_rate"])
    native_rate = float(summary["native_build_success_rate"])
    if analyzer_rate < min_analyzer_success_rate:
        raise PublicProjectBuildFailure(
            f"analyzer_success_rate {analyzer_rate:.4f} is below "
            f"{min_analyzer_success_rate:.4f}"
        )
    if native_rate < min_native_build_success_rate:
        raise PublicProjectBuildFailure(
            f"native_build_success_rate {native_rate:.4f} is below "
            f"{min_native_build_success_rate:.4f}"
        )
