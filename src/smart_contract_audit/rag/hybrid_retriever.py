from __future__ import annotations

from .retriever import retrieve_chunks


def retrieve_hybrid_chunks(
    query: str,
    chunks,
    *,
    rag_mode: str,
    vulnerability_type: str = "",
    standard_refs: list[dict] | None = None,
):
    boosted_query = " ".join(
        part
        for part in (
            query,
            vulnerability_type,
            " ".join(ref.get("id", "") for ref in (standard_refs or []) if isinstance(ref, dict)),
        )
        if part
    )
    return retrieve_chunks(boosted_query, chunks, rag_mode)
