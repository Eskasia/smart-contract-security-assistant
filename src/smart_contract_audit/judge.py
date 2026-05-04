from __future__ import annotations

import json
import os
import re
import subprocess

from .models import Finding, RagChunk


def score_finding_output(finding: Finding, chunks: list[RagChunk]) -> tuple[float, float]:
    """Score generated finding report completeness, not contract security posture."""
    local_score = _score(finding, chunks)
    external_score = _external_score(finding, chunks)
    return local_score, external_score


def _score(finding: Finding, chunks: list[RagChunk]) -> float:
    score = 0.0
    if finding.vulnerability_type in finding.explanation:
        score += 1.0
    if finding.fix_suggestion:
        score += 1.0
    if finding.attack_path and _count_steps(finding.attack_path) >= 3:
        score += 1.0
    if re.search(r"line\s+\d+|L\d+", finding.explanation, re.IGNORECASE):
        score += 1.0
    if chunks and any(chunk.source_id in finding.explanation for chunk in chunks):
        score += 1.0
    if finding.remediation_code:
        score += 1.0
    return min(score, 5.0)


def _external_score(finding: Finding, chunks: list[RagChunk]) -> float:
    command = os.getenv("EXTERNAL_JUDGE_COMMAND")
    if not command:
        return _score(finding, chunks)
    payload = {
        "finding": finding.to_dict(),
        "rag_chunks": [chunk.to_dict() for chunk in chunks],
    }
    result = subprocess.run(
        command.split(),
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        return 0.0
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        return 0.0
    score = output.get("score", 0.0)
    return float(score) if isinstance(score, int | float) else 0.0


def _count_steps(text: str) -> int:
    numbered = re.findall(r"(?:^|\s)\d+[\.\)]", text)
    if numbered:
        return len(numbered)
    return len([part for part in re.split(r"\n+|;|\.", text) if part.strip()])
