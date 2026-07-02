from __future__ import annotations

from typing import Any

from .defi import derive_defi_profit_signal
from .exploit_validation import default_exploit_validation
from .fuzz import suggest_fuzz_seeds
from .properties import suggest_formal_properties


def attach_advanced_evidence(
    findings: list[Any],
    trace_store: Any | None = None,
    trace_id: str | None = None,
) -> None:
    for finding in findings:
        if not finding.exploit_validation:
            finding.exploit_validation = default_exploit_validation(finding)
        if not finding.fuzz_seed_suggestions:
            finding.fuzz_seed_suggestions = suggest_fuzz_seeds(finding)
        if not finding.formal_property_suggestions:
            finding.formal_property_suggestions = suggest_formal_properties(finding)
        if not finding.defi_profit_signal:
            finding.defi_profit_signal = derive_defi_profit_signal(finding)
        if trace_store is not None:
            if trace_id is None:
                raise ValueError("trace_id is required when recording advanced evidence.")
            trace_store.record_exploit_validation(
                trace_id,
                finding.finding_id,
                finding.exploit_validation,
            )
