from __future__ import annotations

import argparse
from pathlib import Path

from smart_contract_audit.rag.chunker import chunk_document
from smart_contract_audit.rag.indexer import deduplicate_chunks, write_chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_reports_dir", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    parser.add_argument("--filter-unknown", action="store_true")
    args = parser.parse_args()

    chunks = []
    for path in sorted(args.raw_reports_dir.iterdir()):
        if path.is_file():
            chunks.extend(chunk_document(path, include_unknown=not args.filter_unknown))
    chunks = deduplicate_chunks(chunks)
    write_chunks(chunks, args.output_jsonl)
    print(f"Wrote {len(chunks)} chunks to {args.output_jsonl}")


if __name__ == "__main__":
    main()
