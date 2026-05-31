from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def suggest_fuzz_seeds(finding: Any) -> list[dict[str, Any]]:
    target_function = finding.location.function or "target"
    supported_by = _support_nodes(finding)
    vuln_type = finding.vulnerability_type
    if vuln_type == "reentrancy":
        return [
            {
                "finding_id": finding.finding_id,
                "seed_id": f"seed:{finding.finding_id}:001",
                "target_function": target_function,
                "preconditions": [
                    "attacker has a positive recorded balance",
                    "vault has enough local fixture ETH to pay more than one withdrawal",
                ],
                "sequence": [
                    {"call": "deposit", "sender": "attacker", "value": "1 ETH"},
                    {"call": target_function, "sender": "attacker", "value": "0"},
                ],
                "expected_signal": "external_call_before_state_update",
                "status": "suggestion",
                "supported_by": supported_by,
            }
        ]
    if vuln_type in {"access_control", "privilege_escalation"}:
        return [
            {
                "finding_id": finding.finding_id,
                "seed_id": f"seed:{finding.finding_id}:001",
                "target_function": target_function,
                "preconditions": [
                    "exercise privileged path with authorized and unauthorized senders"
                ],
                "sequence": [
                    {"call": target_function, "sender": "owner", "value": "0"},
                    {"call": target_function, "sender": "attacker", "value": "0"},
                ],
                "expected_signal": "privileged_state_or_asset_flow_diff",
                "status": "suggestion",
                "supported_by": supported_by,
            }
        ]
    return [
        {
            "finding_id": finding.finding_id,
            "seed_id": f"seed:{finding.finding_id}:001",
            "target_function": target_function,
            "preconditions": ["initialize the local fixture state required by the finding"],
            "sequence": [{"call": target_function, "sender": "attacker", "value": "0"}],
            "expected_signal": f"{vuln_type}_path_reaches_reported_source_range",
            "status": "suggestion",
            "supported_by": supported_by,
        }
    ]


def write_fuzz_seed_outputs(findings: list[Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    seeds = [seed for finding in findings for seed in suggest_fuzz_seeds(finding)]
    payload = {"seed_count": len(seeds), "seeds": seeds}
    (output_dir / "fuzz_seed_suggestions.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_notes(output_dir / "echidna_seed_notes.md", "Echidna", seeds)
    _write_notes(output_dir / "medusa_seed_notes.md", "Medusa", seeds)
    _write_notes(output_dir / "foundry_fuzz_targets.md", "Foundry", seeds)
    return payload


def _write_notes(path: Path, tool_name: str, seeds: list[dict[str, Any]]) -> None:
    lines = [f"# {tool_name} Fuzz Seed Notes", ""]
    if not seeds:
        lines.append("No seed suggestions were generated.")
    for seed in seeds:
        lines.extend(
            [
                f"## {seed['seed_id']}",
                "",
                f"- Finding: `{seed['finding_id']}`",
                f"- Target: `{seed['target_function']}`",
                f"- Status: `{seed['status']}`",
                f"- Supported by: `{', '.join(seed['supported_by'])}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _support_nodes(finding: Any) -> list[str]:
    return [
        f"finding:{finding.finding_id}",
        (
            f"source:{str(finding.location.file).replace(' ', '_')}:"
            f"{finding.location.line_start}-{finding.location.line_end}"
        ),
    ]
