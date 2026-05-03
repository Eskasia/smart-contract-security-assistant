from __future__ import annotations

import json

from smart_contract_audit.models import Finding, RagChunk


def pack_finding_prompt(finding: Finding, chunks: list[RagChunk]) -> str:
    related = "\n\n".join(
        (
            f"[{chunk.source_id}] [severity={chunk.severity}] "
            f"[vuln_type={chunk.vuln_type}]\n{chunk.content}"
        )
        for chunk in chunks
    )
    return "\n".join(
        [
            "[System]",
            "You are a smart contract security analyst.",
            (
                "Given one static analysis finding and related audit knowledge, "
                "provide explanation, attack path, fix suggestion, and remediation_code."
            ),
            "",
            "[Finding]",
            json.dumps(finding.to_dict(), ensure_ascii=False),
            "",
            "[Related Knowledge]",
            related or "No related knowledge chunks were retrieved.",
            "",
            "[Instructions]",
            "- Output valid JSON with explanation, attack_path, fix_suggestion, remediation_code.",
            "- Reference specific code lines from the static finding.",
            "- Do not invent vulnerabilities not present in the static finding.",
        ]
    )
