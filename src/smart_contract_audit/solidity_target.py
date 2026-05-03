from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_MARKERS = (
    "foundry.toml",
    "hardhat.config.js",
    "hardhat.config.ts",
    "hardhat.config.cjs",
    "hardhat.config.mjs",
    "remappings.txt",
)
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "artifacts",
    "broadcast",
    "cache",
    "node_modules",
    "out",
}


@dataclass(frozen=True)
class SolidityTarget:
    input_path: Path
    analysis_path: Path
    entry_path: Path
    project_root: Path
    input_kind: str
    project_type: str
    source_files: tuple[Path, ...]
    remappings: tuple[str, ...]

    @property
    def combined_source(self) -> str:
        parts = []
        for path in self.source_files:
            parts.append(f"// FILE: {path.relative_to(self.project_root)}")
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(parts)

    @property
    def total_source_lines(self) -> int:
        return sum(
            len(path.read_text(encoding="utf-8", errors="replace").splitlines())
            for path in self.source_files
        )


def resolve_solidity_target(input_path: Path) -> SolidityTarget:
    resolved = input_path.resolve()
    if not resolved.exists():
        raise ValueError(f"Input path does not exist: {resolved}")

    if resolved.is_file():
        if resolved.suffix != ".sol":
            raise ValueError("Input must be a `.sol` file or a Solidity project directory.")
        project_root = _find_project_root(resolved.parent) or resolved.parent
        project_type = _detect_project_type(project_root, single_file=True)
        return SolidityTarget(
            input_path=resolved,
            analysis_path=resolved,
            entry_path=resolved,
            project_root=project_root,
            input_kind="single_file",
            project_type=project_type,
            source_files=(resolved,),
            remappings=_load_remappings(project_root),
        )

    if not resolved.is_dir():
        raise ValueError("Input must be a `.sol` file or a Solidity project directory.")

    project_root = resolved
    project_type = _detect_project_type(project_root, single_file=False)
    source_files = _project_source_files(project_root, project_type)
    if not source_files:
        raise ValueError("Project directory does not contain Solidity source files.")

    entry_path = _select_entry_file(project_root, project_type, source_files)
    return SolidityTarget(
        input_path=resolved,
        analysis_path=project_root,
        entry_path=entry_path,
        project_root=project_root,
        input_kind="project_directory",
        project_type=project_type,
        source_files=source_files,
        remappings=_load_remappings(project_root),
    )


def slither_command_args_for_target(
    target: SolidityTarget,
    execution_root: Path | None = None,
) -> list[str]:
    args: list[str] = []
    execution_root = (execution_root or target.project_root).resolve()
    for remapping in target.remappings:
        args.extend(
            ["--solc-remaps", _remapping_for_execution_root(remapping, target, execution_root)]
        )
    if target.project_type in {"foundry", "hardhat"}:
        args.extend(["--compile-force-framework", "solc"])
    return args


def _find_project_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate
    return None


def _detect_project_type(project_root: Path, single_file: bool) -> str:
    if (project_root / "foundry.toml").exists():
        return "foundry"
    if any(
        (project_root / name).exists() for name in PROJECT_MARKERS if name.startswith("hardhat")
    ):
        return "hardhat"
    if _package_json_mentions_hardhat(project_root / "package.json"):
        return "hardhat"
    if (project_root / "remappings.txt").exists():
        return "solc_remapped"
    return "single_file" if single_file else "generic_project"


def _package_json_mentions_hardhat(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        package = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    dependency_sections = (
        package.get("dependencies", {}),
        package.get("devDependencies", {}),
        package.get("peerDependencies", {}),
    )
    return any("hardhat" in section for section in dependency_sections if isinstance(section, dict))


def _project_source_files(
    project_root: Path,
    project_type: str,
    preferred: Path | None = None,
) -> tuple[Path, ...]:
    source_roots = _source_roots(project_root, project_type)
    files: list[Path] = []
    for source_root in source_roots:
        if source_root.exists():
            files.extend(_iter_solidity_files(source_root))

    if preferred is not None and preferred not in files:
        files.insert(0, preferred)

    if not files:
        files.extend(_iter_solidity_files(project_root))

    unique = sorted({path.resolve() for path in files}, key=lambda path: str(path))
    if preferred is not None:
        preferred = preferred.resolve()
        unique = [preferred, *[path for path in unique if path != preferred]]
    return tuple(unique)


def _source_roots(project_root: Path, project_type: str) -> tuple[Path, ...]:
    if project_type == "foundry":
        return (project_root / _foundry_source_dir(project_root),)
    if project_type == "hardhat":
        return (project_root / "contracts",)
    return (project_root,)


def _foundry_source_dir(project_root: Path) -> str:
    config_path = project_root / "foundry.toml"
    if not config_path.exists():
        return "src"
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return "src"
    profile_default = config.get("profile", {}).get("default", {})
    src = profile_default.get("src", config.get("src", "src"))
    return str(src or "src")


def _iter_solidity_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.sol"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        files.append(path.resolve())
    return files


def _select_entry_file(
    project_root: Path,
    project_type: str,
    source_files: tuple[Path, ...],
) -> Path:
    preferred_roots = _source_roots(project_root, project_type)
    for root in preferred_roots:
        root = root.resolve()
        candidates = [path for path in source_files if path.is_relative_to(root)]
        if candidates:
            return sorted(candidates, key=lambda path: str(path))[0]
    return sorted(source_files, key=lambda path: str(path))[0]


def _load_remappings(project_root: Path) -> tuple[str, ...]:
    remappings = list(_load_remappings_txt(project_root / "remappings.txt", project_root))
    remappings.extend(_load_foundry_remappings(project_root / "foundry.toml", project_root))
    unique = []
    seen: set[str] = set()
    for remapping in remappings:
        if remapping in seen:
            continue
        unique.append(remapping)
        seen.add(remapping)
    return tuple(unique)


def _load_remappings_txt(path: Path, project_root: Path) -> list[str]:
    if not path.exists():
        return []
    remappings = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        remappings.append(_normalize_remapping(line, project_root))
    return remappings


def _load_foundry_remappings(path: Path, project_root: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        config = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return []
    values = []
    profile_default = config.get("profile", {}).get("default", {})
    for remapping in config.get("remappings", []) or []:
        values.append(str(remapping))
    for remapping in profile_default.get("remappings", []) or []:
        values.append(str(remapping))
    return [_normalize_remapping(value, project_root) for value in values if "=" in value]


def _normalize_remapping(remapping: str, project_root: Path) -> str:
    prefix, target = remapping.split("=", 1)
    target_path = Path(target)
    if target_path.is_absolute():
        normalized_target = str(target_path)
    else:
        normalized_target = str((project_root / target_path).resolve().relative_to(project_root))
    if target.endswith("/") and not normalized_target.endswith("/"):
        normalized_target += "/"
    return f"{prefix}={normalized_target}"


def _remapping_for_execution_root(
    remapping: str,
    target: SolidityTarget,
    execution_root: Path,
) -> str:
    prefix, remap_target = remapping.split("=", 1)
    target_path = Path(remap_target)
    if target_path.is_absolute():
        return remapping
    absolute_target = (target.project_root / target_path).resolve()
    try:
        relative_target = absolute_target.relative_to(execution_root)
    except ValueError:
        return f"{prefix}={absolute_target}"
    normalized_target = str(relative_target)
    if remap_target.endswith("/") and not normalized_target.endswith("/"):
        normalized_target += "/"
    return f"{prefix}={normalized_target}"
