import json
import re
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

import pytest

from smart_contract_audit.evaluation.public_project_builds import (
    PublicProjectBuildFailure,
    preflight_public_project_builds,
    prepare_project_dependencies,
    run_public_project_builds,
)

PUBLIC_PROJECT_MANIFEST = Path("eval/public_benchmark/public-project-builds-10-manifest.json")


def test_public_project_build_manifest_is_pinned_to_10_commit_refs() -> None:
    cases = json.loads(PUBLIC_PROJECT_MANIFEST.read_text(encoding="utf-8"))

    assert len(cases) == 10
    assert all(case["repo_url"].startswith("https://github.com/") for case in cases)
    assert all(re.fullmatch(r"[0-9a-f]{40}", case["ref"]) for case in cases)


def test_public_project_build_preflight_reports_missing_tools() -> None:
    preflight = preflight_public_project_builds(
        PUBLIC_PROJECT_MANIFEST,
        tool_resolver=lambda name: "/bin/npx" if name == "npx" else None,
    )

    assert preflight["cases"] == 10
    assert preflight["framework_hints"] == {
        "foundry": 5,
        "foundry-hardhat": 1,
        "hardhat": 4,
    }
    assert preflight["native_tool_availability"] == {"forge": False, "npx": True}
    assert preflight["missing_required_tools"] == ["forge"]


class FakeReport:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return self.payload


def test_public_project_builds_summarizes_local_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """
        [
          {
            "case_id": "fixture_foundry",
            "local_path": "tests/fixtures/solidity_projects/foundry"
          }
        ]
        """,
        encoding="utf-8",
    )

    def fake_analyzer(project_path: Path, **_: Any) -> FakeReport:
        assert project_path.name == "foundry"
        return FakeReport(
            {
                "overall_status": "no_finding",
                "analysis_metadata": {
                    "errors": ["foundry native build completed before Slither."]
                },
            }
        )

    summary = run_public_project_builds(
        manifest,
        workspace_dir=tmp_path / "workspace",
        reports_dir=tmp_path / "reports",
        min_analyzer_success_rate=1.0,
        min_native_build_success_rate=1.0,
        analyzer=fake_analyzer,
        tool_resolver=lambda name: f"/bin/{name}",
        dependency_preparer=lambda _: ["dependencies prepared"],
    )

    assert summary["analyzer_success_rate"] == 1.0
    assert summary["native_build_success_rate"] == 1.0
    assert summary["native_tool_availability"] == {"forge": True, "npx": True}
    assert summary["results"][0]["dependency_preparation"] == ["dependencies prepared"]
    assert (tmp_path / "reports" / "public_project_builds_summary.json").exists()


def test_public_project_builds_enforces_native_build_threshold(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """
        [
          {
            "case_id": "fixture_hardhat",
            "local_path": "tests/fixtures/solidity_projects/hardhat"
          }
        ]
        """,
        encoding="utf-8",
    )

    def fake_analyzer(_: Path, **__: Any) -> FakeReport:
        return FakeReport(
            {
                "overall_status": "no_finding",
                "analysis_metadata": {
                    "errors": [
                        "hardhat native build tool not found; "
                        "Slither will use solc fallback."
                    ]
                },
            }
        )

    with pytest.raises(PublicProjectBuildFailure, match="native_build_success_rate"):
        run_public_project_builds(
            manifest,
            workspace_dir=tmp_path / "workspace",
            reports_dir=tmp_path / "reports",
            min_native_build_success_rate=1.0,
            analyzer=fake_analyzer,
            dependency_preparer=lambda _: [],
        )


def test_public_project_builds_counts_native_build_blockers(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """
        [
          {
            "case_id": "fixture_hardhat",
            "local_path": "tests/fixtures/solidity_projects/hardhat"
          },
          {
            "case_id": "fixture_foundry",
            "local_path": "tests/fixtures/solidity_projects/foundry"
          }
        ]
        """,
        encoding="utf-8",
    )

    def fake_analyzer(project_path: Path, **__: Any) -> FakeReport:
        if project_path.name == "hardhat":
            error = "hardhat native build tool not found; Slither will use solc fallback."
        else:
            error = "foundry native build failed before Slither; using solc fallback."
        return FakeReport(
            {
                "overall_status": "no_finding",
                "analysis_metadata": {"errors": [error]},
            }
        )

    summary = run_public_project_builds(
        manifest,
        workspace_dir=tmp_path / "workspace",
        reports_dir=tmp_path / "reports",
        analyzer=fake_analyzer,
        tool_resolver=lambda name: "/bin/npx" if name == "npx" else None,
        dependency_preparer=lambda _: [],
    )

    assert summary["native_tool_availability"] == {"forge": False, "npx": True}
    assert summary["native_build_tool_missing_cases"] == 1
    assert summary["native_build_failed_cases"] == 1
    assert [result["native_build_blocker"] for result in summary["results"]] == [
        "tool_missing",
        "build_failed",
    ]


def test_public_project_builds_checks_out_commit_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit_ref = "094c1a1367b7d9183524a43ee080141f64ca9fb8"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        f"""
        [
          {{
            "case_id": "openzeppelin",
            "repo_url": "https://github.com/OpenZeppelin/openzeppelin-contracts.git",
            "ref": "{commit_ref}"
          }}
        ]
        """,
        encoding="utf-8",
    )
    commands: list[list[str]] = []

    def fake_run(
        command: list[str],
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> CompletedProcess[str]:
        commands.append(command)
        if command[:2] == ["git", "clone"]:
            Path(command[-1]).mkdir(parents=True)
        return CompletedProcess(command, 0, stdout="", stderr="")

    def fake_analyzer(_: Path, **__: Any) -> FakeReport:
        return FakeReport({"overall_status": "no_finding", "analysis_metadata": {"errors": []}})

    monkeypatch.setattr(
        "smart_contract_audit.evaluation.public_project_builds.subprocess.run",
        fake_run,
    )

    run_public_project_builds(
        manifest,
        workspace_dir=tmp_path / "workspace",
        reports_dir=tmp_path / "reports",
        analyzer=fake_analyzer,
        dependency_preparer=lambda _: [],
    )

    assert commands[0][:4] == ["git", "clone", "--filter=blob:none", "--no-checkout"]
    assert commands[1][:5] == [
        "git",
        "-C",
        str(tmp_path / "workspace" / "openzeppelin"),
        "fetch",
        "--depth",
    ]
    assert commands[1][-2:] == ["origin", commit_ref]
    assert commands[2][-2:] == ["--detach", commit_ref]


def test_prepare_project_dependencies_runs_submodules_and_npm_ci(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".gitmodules").write_text("", encoding="utf-8")
    (project / "package.json").write_text("{}", encoding="utf-8")
    (project / "package-lock.json").write_text("{}", encoding="utf-8")
    commands: list[tuple[list[str], Path]] = []

    def fake_run(
        command: list[str],
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> CompletedProcess[str]:
        commands.append((command, cwd))
        return CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(
        "smart_contract_audit.evaluation.public_project_builds.shutil.which",
        lambda name: "/bin/npm" if name == "npm" else None,
    )
    monkeypatch.setattr(
        "smart_contract_audit.evaluation.public_project_builds.subprocess.run",
        fake_run,
    )

    messages = prepare_project_dependencies(project)

    assert messages == [
        "git submodules initialized before native build.",
        "npm dependencies installed before native build.",
    ]
    assert commands[0][0][:5] == ["git", "submodule", "update", "--init", "--recursive"]
    assert commands[1][0][:2] == ["/bin/npm", "ci"]
    assert "--ignore-scripts" in commands[1][0]
    assert "--engine-strict=false" in commands[1][0]
    assert "--legacy-peer-deps" not in commands[1][0]
    assert commands[0][1] == project
    assert commands[1][1] == project


def test_prepare_project_dependencies_falls_back_to_legacy_peer_deps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text("{}", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_run(
        command: list[str],
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> CompletedProcess[str]:
        commands.append(command)
        returncode = 1 if len(commands) == 1 else 0
        return CompletedProcess(command, returncode, stdout="", stderr="peer conflict")

    monkeypatch.setattr(
        "smart_contract_audit.evaluation.public_project_builds.shutil.which",
        lambda name: "/bin/npm" if name == "npm" else None,
    )
    monkeypatch.setattr(
        "smart_contract_audit.evaluation.public_project_builds.subprocess.run",
        fake_run,
    )

    messages = prepare_project_dependencies(project)

    assert messages == ["npm dependencies installed before native build."]
    assert commands[0][:2] == ["/bin/npm", "install"]
    assert "--legacy-peer-deps" not in commands[0]
    assert commands[1][:2] == ["/bin/npm", "install"]
    assert "--legacy-peer-deps" in commands[1]
