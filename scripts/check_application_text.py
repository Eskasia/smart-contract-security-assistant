from __future__ import annotations

import re
import sys
from pathlib import Path

DOC_PATH = Path("docs/adoption/codex-for-oss-application.md")
LIMIT = 500
REQUIRED_FIELDS = {
    "qualification",
    "api_credits_use",
    "codex_security_use",
    "additional_information",
}
FIELD_RE = re.compile(
    r"<!-- app-field: (?P<name>[a-z0-9_-]+) -->\s*```text\s*(?P<text>.*?)\s*```",
    re.DOTALL,
)


def main() -> int:
    if not DOC_PATH.exists():
        print(f"missing document: {DOC_PATH}", file=sys.stderr)
        return 1

    content = DOC_PATH.read_text(encoding="utf-8")
    fields = {
        match.group("name"): match.group("text").strip()
        for match in FIELD_RE.finditer(content)
    }
    missing = sorted(REQUIRED_FIELDS - set(fields))
    if missing:
        print(f"missing fields: {', '.join(missing)}", file=sys.stderr)
        return 1

    failed = False
    for name in sorted(REQUIRED_FIELDS):
        text = fields[name]
        count = len(text)
        print(f"{name}: {count}/{LIMIT}")
        if count > LIMIT:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
