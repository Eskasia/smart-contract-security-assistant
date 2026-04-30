from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.rag.indexer import load_chunks
from smart_contract_audit.rag.retriever import retrieve_chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "rag_recall_test",
        type=Path,
        nargs="?",
        default=Path("eval/rag_recall_test.json"),
    )
    parser.add_argument(
        "chunks_jsonl",
        type=Path,
        nargs="?",
        default=Path("data/dataset_v1.0/chunks/chunks.jsonl"),
    )
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    cases = json.loads(args.rag_recall_test.read_text(encoding="utf-8"))
    chunks = load_chunks(args.chunks_jsonl)
    hits = 0
    for case in cases:
        retrieved = retrieve_chunks(case["query"], chunks, "quality")[: args.top_k]
        retrieved_ids = {chunk.chunk_id for chunk in retrieved}
        if set(case["expected_chunk_ids"]) & retrieved_ids:
            hits += 1
    recall = hits / len(cases) if cases else 0
    print(json.dumps({"cases": len(cases), "recall_at_k": recall}, indent=2))
    if cases and recall < 0.75:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
