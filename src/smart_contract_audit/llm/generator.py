from __future__ import annotations

import json

from smart_contract_audit.llm.mlx_runtime import MLXRuntimeConfig, generate_with_mlx
from smart_contract_audit.llm.prompt_template import pack_finding_prompt
from smart_contract_audit.models import Finding, RagChunk


def generate_finding_details(
    finding: Finding,
    chunks: list[RagChunk],
    config: MLXRuntimeConfig | None = None,
) -> dict[str, str]:
    runtime_config = config or MLXRuntimeConfig()
    prompt = pack_finding_prompt(finding, chunks)
    generated = generate_with_mlx(prompt, runtime_config)
    if generated:
        parsed = _parse_json_object(generated)
        if parsed:
            return {
                "explanation": str(parsed.get("explanation", "")),
                "attack_path": str(parsed.get("attack_path", "")),
                "fix_suggestion": str(parsed.get("fix_suggestion", "")),
            }

    return _deterministic_details(finding, chunks)


def _parse_json_object(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _deterministic_details(finding: Finding, chunks: list[RagChunk]) -> dict[str, str]:
    location = f"{finding.location.file} line {finding.location.line_start}"
    source_note = (
        f" Related chunks: {', '.join(chunk.source_id for chunk in chunks)}." if chunks else ""
    )
    return {
        "explanation": (
            f"Slither reported `{finding.detector_name}` at {location}, mapped to "
            f"`{finding.vulnerability_type}` with severity {finding.severity}.{source_note}"
        ),
        "attack_path": (
            "1. An attacker reaches the affected function. "
            "2. The vulnerable control flow or external call condition is triggered. "
            "3. The contract state or asset flow is affected according to the Slither evidence."
        ),
        "fix_suggestion": _fix_for_type(finding.vulnerability_type),
    }


def _fix_for_type(vulnerability_type: str) -> str:
    fixes = {
        "reentrancy": (
            "Apply checks-effects-interactions and add a nonReentrant modifier "
            "around the affected function."
        ),
        "access_control": (
            "Protect the function with an explicit onlyOwner or role-based modifier "
            "and test unauthorized calls."
        ),
        "unchecked_external_call": (
            'Check the returned success boolean with require(success, "call failed") '
            "and handle revert data."
        ),
        "dangerous_delegatecall": (
            "Remove user-controlled delegatecall targets or restrict them through "
            "an allowlist."
        ),
        "array_length_manipulation": (
            "Avoid direct array length manipulation and guard index/length updates "
            "with require checks."
        ),
    }
    return fixes.get(
        vulnerability_type,
        "Apply a minimal code-level guard matching the Slither detector evidence.",
    )
