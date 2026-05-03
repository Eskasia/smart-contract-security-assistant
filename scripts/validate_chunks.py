from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.rag.indexer import load_chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("chunks_jsonl", type=Path)
    parser.add_argument("--max-unknown-rate", type=float, default=1.0)
    parser.add_argument("--min-eligible", type=int, default=1)
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
    unknown = sum(1 for chunk in chunks if chunk.vuln_type == "unknown")
    eligible = sum(1 for chunk in chunks if chunk.eligible_for_eval)
    metadata_complete = sum(
        1
        for chunk in chunks
        if chunk.source_path and chunk.section_title and chunk.chunk_index >= 0
    )
    unknown_rate = unknown / total if total else 0
    result = {
        "total_chunks": total,
        "metadata_complete_rate": complete / total if total else 0,
        "pdf_metadata_complete_rate": metadata_complete / total if total else 0,
        "length_outlier_rate": length_outliers / total if total else 0,
        "unknown_chunks": unknown,
        "unknown_rate": unknown_rate,
        "eligible_chunks": eligible,
        "valid": (
            bool(total)
            and complete / total >= 0.95
            and metadata_complete / total >= 0.95
            and unknown_rate <= args.max_unknown_rate
            and eligible >= args.min_eligible
        ),
    }
    print(json.dumps(result, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
