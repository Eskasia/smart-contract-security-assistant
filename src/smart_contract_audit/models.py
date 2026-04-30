from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Location:
    file: str
    function: str | None
    line_start: int
    line_end: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RagChunk:
    chunk_id: str
    source_id: str
    report_id: str
    severity: int
    vuln_type: str
    content: str
    token_count: int
    created_at: str
    sha256: str
    unsupported_visual_content: bool = False
    label_source: str = "rule_based"
    label_confidence: float = 1.0
    eligible_for_eval: bool = True
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Finding:
    finding_id: str
    vulnerability_type: str
    severity: int
    location: Location
    evidence: str
    reference: list[str]
    finding_confidence: float
    explanation_confidence: float
    explanation: str
    attack_path: str
    fix_suggestion: str
    static_tool_source: str
    detector_name: str
    partial: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["location"] = self.location.to_dict()
        return data


@dataclass
class AnalysisMetadata:
    dataset_version: str
    model_version: str
    solc_version: str | None
    slither_version: str | None
    partial_analysis: bool
    analysis_trace_id: str
    context_tokens_used: int
    rag_mode: str
    total_duration_ms: int
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisReport:
    overall_status: str
    contract_id: str
    requires_human_review: bool
    business_logic_review_required: bool
    review_reason: str
    findings: list[Finding]
    analysis_metadata: AnalysisMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "contract_id": self.contract_id,
            "requires_human_review": self.requires_human_review,
            "business_logic_review_required": self.business_logic_review_required,
            "review_reason": self.review_reason,
            "findings": [finding.to_dict() for finding in self.findings],
            "analysis_metadata": self.analysis_metadata.to_dict(),
        }
