from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from smart_contract_audit.models import RagChunk


def write_chunks(chunks: Iterable[RagChunk], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in deduplicate_chunks(chunks):
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")


def load_chunks(path: Path) -> list[RagChunk]:
    if not path.exists():
        return []
    chunks: list[RagChunk] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            data = json.loads(line)
            chunks.append(RagChunk(**data))
    return chunks


def deduplicate_chunks(chunks: Iterable[RagChunk]) -> list[RagChunk]:
    deduped: list[RagChunk] = []
    seen: set[str] = set()
    for chunk in chunks:
        key = chunk.sha256
        if key in seen:
            continue
        deduped.append(chunk)
        seen.add(key)
    return deduped
