from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from smart_contract_audit.validation.schema import REPORT_SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = REPO_ROOT / "schema" / "report.schema.json"


def render_schema() -> str:
    return json.dumps(REPORT_SCHEMA, indent=2, sort_keys=True) + "\n"


def sync_schema(path: Path = DEFAULT_SCHEMA_PATH, *, check: bool = False) -> int:
    rendered = render_schema()
    if check:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if existing != rendered:
            print(f"{path} is out of sync with REPORT_SCHEMA.", file=sys.stderr)
            return 1
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize the public JSON report schema from REPORT_SCHEMA."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--path", type=Path, default=DEFAULT_SCHEMA_PATH)
    args = parser.parse_args(argv)
    return sync_schema(args.path, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
