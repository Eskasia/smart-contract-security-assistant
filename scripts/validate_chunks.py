from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.rag.indexer import load_chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("chunks_jsonl", type=Path)
    args = parser.parse_args()

    chunks = load_chunks(args.chunks_jsonl)
    total = len(chunks)
    complete = sum(
        1
        for chunk in chunks
        if chunk.chunk_id and chunk.source_id and chunk.report_id and chunk.sha256 and chunk.content
    )
    length_outliers = sum(
        1 for chunk in chunks if chunk.token_count < 300 or chunk.token_count > 450
    )
    result = {
        "total_chunks": total,
        "metadata_complete_rate": complete / total if total else 0,
        "length_outlier_rate": length_outliers / total if total else 0,
        "valid": bool(total) and complete / total >= 0.95 and length_outliers / total < 0.05,
    }
    print(json.dumps(result, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
