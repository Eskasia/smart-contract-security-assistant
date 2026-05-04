from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_contract_audit.models import Finding

FORMULA_VERSION = "security_score_v1"
SEVERITY_WEIGHTS = {1: 4.0, 2: 12.0, 3: 30.0}
PARTIAL_ANALYSIS_PENALTY = 10.0
BUSINESS_LOGIC_REVIEW_PENALTY = 5.0
REVIEW_STATUS_MULTIPLIERS = {
    "pending_human_review": 1.0,
    "blocked": 1.0,
    "rejected": 1.0,
    "approved": 0.8,
}


@dataclass(frozen=True)
class SecurityScoreResult:
    score: float
    formula_version: str
    factors: dict[str, Any]


def compute_security_score(
    findings: list[Finding],
    review_status: str,
    partial_analysis: bool,
    business_logic_review_required: bool,
    benchmark_weight: float = 1.0,
) -> SecurityScoreResult:
    review_multiplier = REVIEW_STATUS_MULTIPLIERS.get(review_status, 1.0)
    severity_counts = {"1": 0, "2": 0, "3": 0}
    finding_penalties = []

    for finding in findings:
        severity = max(1, min(3, int(finding.severity)))
        severity_counts[str(severity)] += 1
        confidence = max(0.2, min(1.0, float(finding.finding_confidence)))
        penalty = round(SEVERITY_WEIGHTS[severity] * confidence * review_multiplier, 2)
        finding_penalties.append(
            {
                "finding_id": finding.finding_id,
                "severity": severity,
                "confidence": round(confidence, 2),
                "penalty": penalty,
            }
        )

    total_finding_penalty = round(sum(item["penalty"] for item in finding_penalties), 2)
    partial_penalty = PARTIAL_ANALYSIS_PENALTY if partial_analysis else 0.0
    business_logic_penalty = (
        BUSINESS_LOGIC_REVIEW_PENALTY if business_logic_review_required else 0.0
    )
    raw_score = 100.0 - (
        total_finding_penalty + partial_penalty + business_logic_penalty
    ) * benchmark_weight
    score = round(max(0.0, min(100.0, raw_score)), 2)

    return SecurityScoreResult(
        score=score,
        formula_version=FORMULA_VERSION,
        factors={
            "base_score": 100.0,
            "benchmark_weight": benchmark_weight,
            "review_status": review_status,
            "review_status_multiplier": review_multiplier,
            "severity_weights": SEVERITY_WEIGHTS,
            "severity_counts": severity_counts,
            "finding_penalties": finding_penalties,
            "total_finding_penalty": total_finding_penalty,
            "partial_analysis_penalty": partial_penalty,
            "business_logic_review_penalty": business_logic_penalty,
        },
    )
