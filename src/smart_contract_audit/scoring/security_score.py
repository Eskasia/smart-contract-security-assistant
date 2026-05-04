from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from smart_contract_audit.models import Finding

FORMULA_VERSION = "security_score_v2"
SEVERITY_WEIGHTS = {1: 4.0, 2: 12.0, 3: 30.0}
PARTIAL_ANALYSIS_PENALTY = 10.0
BUSINESS_LOGIC_REVIEW_PENALTY = 5.0
REVIEW_STATUS_MULTIPLIERS = {
    "pending_human_review": 1.0,
    "blocked": 1.0,
    "rejected": 1.0,
    "approved": 0.8,
}
FINDING_REVIEW_MULTIPLIERS = {
    "unreviewed": 1.0,
    "true_positive": 1.0,
    "accepted_risk": 1.0,
    "false_positive": 0.0,
    "fixed": 0.2,
}
FindingInput = Finding | Mapping[str, Any]


@dataclass(frozen=True)
class SecurityScoreResult:
    score: float
    formula_version: str
    factors: dict[str, Any]


def compute_security_score(
    findings: Sequence[FindingInput],
    review_status: str,
    partial_analysis: bool,
    business_logic_review_required: bool,
    benchmark_weight: float = 1.0,
) -> SecurityScoreResult:
    review_multiplier = REVIEW_STATUS_MULTIPLIERS.get(review_status, 1.0)
    severity_counts = {"1": 0, "2": 0, "3": 0}
    finding_penalties = []

    for finding in findings:
        severity = max(1, min(3, int(_finding_field(finding, "severity", 1))))
        severity_counts[str(severity)] += 1
        confidence = max(
            0.2,
            min(1.0, float(_finding_field(finding, "finding_confidence", 1.0))),
        )
        finding_review_status = str(
            _finding_field(finding, "review_status", "unreviewed")
        )
        finding_review_multiplier = FINDING_REVIEW_MULTIPLIERS.get(
            finding_review_status,
            1.0,
        )
        penalty = round(
            SEVERITY_WEIGHTS[severity]
            * confidence
            * review_multiplier
            * finding_review_multiplier,
            2,
        )
        finding_penalties.append(
            {
                "finding_id": _finding_field(finding, "finding_id", ""),
                "severity": severity,
                "confidence": round(confidence, 2),
                "finding_review_status": finding_review_status,
                "finding_review_multiplier": finding_review_multiplier,
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


def _finding_field(finding: FindingInput, key: str, default: Any) -> Any:
    if isinstance(finding, Mapping):
        return finding.get(key, default)
    return getattr(finding, key, default)
