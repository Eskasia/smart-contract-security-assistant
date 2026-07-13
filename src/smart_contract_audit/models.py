from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

FINDING_REVIEW_STATUSES = frozenset(
    {"unreviewed", "true_positive", "false_positive", "accepted_risk", "fixed"}
)


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
    source_path: str = ""
    section_title: str = ""
    page_start: int | None = None
    page_end: int | None = None
    chunk_index: int = 0

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
    remediation_code: str
    vulnerable_code: str
    static_tool_source: str
    detector_name: str
    partial: bool = False
    local_judge_score: float = 0.0
    external_judge_score: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    review_status: str = "unreviewed"
    review_note: str = ""
    standard_refs: list[dict[str, Any]] = field(default_factory=list)
    evidence_graph: dict[str, Any] = field(default_factory=dict)
    native_rule_results: list[dict[str, Any]] = field(default_factory=list)
    exploit_validation: dict[str, Any] = field(default_factory=dict)
    fuzz_seed_suggestions: list[dict[str, Any]] = field(default_factory=list)
    formal_property_suggestions: list[dict[str, Any]] = field(default_factory=list)
    defi_profit_signal: dict[str, Any] = field(default_factory=dict)
    falsification_pack: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from .exploit_validation import default_exploit_validation
        from .falsification import build_falsification_pack
        from .fuzz import suggest_fuzz_seeds
        from .properties import suggest_formal_properties
        from .standards import standard_refs_for

        data = asdict(self)
        data["location"] = self.location.to_dict()
        data["standard_refs"] = self.standard_refs or standard_refs_for(
            self.vulnerability_type
        )
        data["exploit_validation"] = self.exploit_validation or default_exploit_validation(
            self
        )
        data["fuzz_seed_suggestions"] = (
            self.fuzz_seed_suggestions or suggest_fuzz_seeds(self)
        )
        data["formal_property_suggestions"] = (
            self.formal_property_suggestions or suggest_formal_properties(self)
        )
        data["defi_profit_signal"] = self.defi_profit_signal or {
            "status": "not_observed",
            "asset_flow": [],
            "oracle_dependency": None,
            "flash_loan_dependency": False,
            "profitability_status": "not_assessed",
            "supported_by": [],
        }
        data["falsification_pack"] = self.falsification_pack or build_falsification_pack(
            self
        )
        return data


@dataclass
class ExternalToolResult:
    tool_name: str
    command: list[str]
    status: str
    findings_count: int
    summary: str
    execution_mode: str = ""
    binary_path: str = ""
    timeout_seconds: int = 0
    output_path: str = ""
    artifact_paths: dict[str, str] = field(default_factory=dict)
    error: str = ""
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisMetadata:
    dataset_version: str
    model_version: str
    solc_version: str | None
    slither_version: str | None
    partial_analysis: bool
    analysis_trace_id: str
    context_tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    local_average_judge_score: float
    external_average_judge_score: float
    rag_mode: str
    total_duration_ms: int
    input_kind: str = "single_file"
    project_type: str = "single_file"
    entry_path: str = ""
    project_root: str = ""
    source_files_count: int = 1
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisReport:
    report_version: str
    overall_status: str
    contract_id: str
    review_status: str
    requires_human_review: bool
    business_logic_review_required: bool
    review_reason: str
    findings: list[Finding]
    analysis_metadata: AnalysisMetadata
    security_score: float = 100.0
    score_formula_version: str = "security_score_v2"
    score_factors: dict[str, Any] = field(default_factory=dict)
    external_tool_results: list[ExternalToolResult] = field(default_factory=list)
    evidence_graph_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "overall_status": self.overall_status,
            "contract_id": self.contract_id,
            "review_status": self.review_status,
            "requires_human_review": self.requires_human_review,
            "business_logic_review_required": self.business_logic_review_required,
            "review_reason": self.review_reason,
            "findings": [finding.to_dict() for finding in self.findings],
            "analysis_metadata": self.analysis_metadata.to_dict(),
            "security_score": self.security_score,
            "score_formula_version": self.score_formula_version,
            "score_factors": self.score_factors,
            "external_tool_results": [result.to_dict() for result in self.external_tool_results],
            "evidence_graph_summary": self.evidence_graph_summary,
        }
