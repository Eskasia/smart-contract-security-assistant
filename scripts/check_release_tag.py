from __future__ import annotations

import argparse
import tomllib
from pathlib import Path


def require_matching_release_tag(tag: str, pyproject_path: Path) -> str:
    with pyproject_path.open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]
    expected = f"v{version}"
    if tag != expected:
        raise ValueError(f"release tag {tag!r} must match project version {expected!r}")
    return str(version)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    args = parser.parse_args()
    try:
        version = require_matching_release_tag(args.tag, args.pyproject)
    except (KeyError, OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"release tag matches project version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
