from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.trace.lookup import lookup_trace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_db", type=Path)
    parser.add_argument("trace_id")
    parser.add_argument("--finding-id")
    args = parser.parse_args()

    print(json.dumps(lookup_trace(args.trace_db, args.trace_id, args.finding_id), indent=2))


if __name__ == "__main__":
    main()
