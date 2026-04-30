from __future__ import annotations

import re
from typing import Any


def compute_explanation_confidence(
    llm_output: dict[str, str],
    schema_valid: bool,
    rag_chunks: list[dict[str, Any]],
) -> float:
    score = 0.0

    if schema_valid:
        score += 0.3
    if _references_line_numbers(llm_output.get("explanation", "")):
        score += 0.2
    if _has_code_level_fix(llm_output.get("fix_suggestion", "")):
        score += 0.2

    cited = _count_cited_sources(llm_output.get("explanation", ""), rag_chunks)
    score += min(cited / 3, 1.0) * 0.2

    if _count_steps(llm_output.get("attack_path", "")) >= 3:
        score += 0.1

    return min(score, 1.0)


def _references_line_numbers(text: str) -> bool:
    return bool(re.search(r"\bline\s+\d+\b|\bL\d+\b|\b\d+\s*-\s*\d+\b", text, re.IGNORECASE))


def _has_code_level_fix(text: str) -> bool:
    fix_markers = ("modifier", "require(", "nonReentrant", "onlyOwner", "checks-effects")
    return any(marker in text for marker in fix_markers)


def _count_cited_sources(text: str, rag_chunks: list[dict[str, Any]]) -> int:
    return sum(
        1 for chunk in rag_chunks if chunk.get("source_id") and str(chunk["source_id"]) in text
    )


def _count_steps(text: str) -> int:
    numbered = re.findall(r"(?:^|\n)\s*\d+[\.\)]", text)
    if numbered:
        return len(numbered)
    return len([part for part in re.split(r"\n+|;|\.", text) if part.strip()])
