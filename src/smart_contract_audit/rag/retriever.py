from __future__ import annotations

import math
import re
from collections import Counter

from smart_contract_audit.config import DEFAULT_RAG_MODE, RAG_MODES
from smart_contract_audit.models import RagChunk


def retrieve_chunks(
    query: str, chunks: list[RagChunk], mode: str = DEFAULT_RAG_MODE
) -> list[RagChunk]:
    if not chunks:
        return []

    mode_config = RAG_MODES.get(mode, RAG_MODES[DEFAULT_RAG_MODE])
    query_terms = _terms(query)
    scored: list[RagChunk] = []

    doc_freq = _document_frequency(chunks)
    total_docs = len(chunks)
    for chunk in chunks:
        terms = _terms(chunk.content)
        score = _bm25_score(query_terms, terms, doc_freq, total_docs)
        if query.lower() and query.lower() in chunk.content.lower():
            score += 1.0
        if score <= 0:
            continue
        copy = RagChunk(**{**chunk.to_dict(), "score": score})
        scored.append(copy)

    scored.sort(key=lambda chunk: chunk.score, reverse=True)
    return scored[: mode_config.output_top_k]


def _terms(text: str) -> list[str]:
    return [term.lower() for term in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text)]


def _document_frequency(chunks: list[RagChunk]) -> Counter[str]:
    freq: Counter[str] = Counter()
    for chunk in chunks:
        freq.update(set(_terms(chunk.content)))
    return freq


def _bm25_score(
    query_terms: list[str],
    document_terms: list[str],
    doc_freq: Counter[str],
    total_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_terms or not document_terms:
        return 0.0
    counts = Counter(document_terms)
    avgdl = max(1.0, len(document_terms))
    score = 0.0
    for term in query_terms:
        if term not in counts:
            continue
        idf = math.log(1 + (total_docs - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
        tf = counts[term]
        denom = tf + k1 * (1 - b + b * len(document_terms) / avgdl)
        score += idf * (tf * (k1 + 1)) / denom
    return score
