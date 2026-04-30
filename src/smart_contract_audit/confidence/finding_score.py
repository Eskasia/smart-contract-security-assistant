from __future__ import annotations

from typing import Any


def compute_finding_confidence(
    severity: int,
    vulnerability_type: str,
    rag_chunks: list[dict[str, Any]],
) -> float:
    base = {3: 0.85, 2: 0.70, 1: 0.50}.get(severity, 0.50)
    if not rag_chunks:
        return base

    matching = sum(1 for chunk in rag_chunks if chunk.get("vuln_type") == vulnerability_type)
    rag_boost = matching / len(rag_chunks) * 0.15
    return min(base + rag_boost, 1.0)
