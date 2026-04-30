from __future__ import annotations

from smart_contract_audit.models import RagChunk


def rerank_chunks(chunks: list[RagChunk], top_k: int) -> list[RagChunk]:
    return sorted(chunks, key=lambda chunk: chunk.score, reverse=True)[:top_k]
