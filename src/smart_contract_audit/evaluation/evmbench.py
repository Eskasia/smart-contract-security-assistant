from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_evmbench_adapter_reports(
    *,
    detect_result: dict[str, Any],
    exploit_result: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    detect = {
        "adapter": "evmbench_detect",
        "source": "scsa_phase2_public_benchmark",
        "finding_alignment": "finding_id_and_vulnerability_type",
        "result": detect_result,
    }
    exploit = {
        "adapter": "evmbench_exploit_sandbox",
        "source": "scsa_phase3_local_fixture",
        "policy": "sandbox_only",
        "result": exploit_result,
    }
    summary = {
        "detect_adapter": "present",
        "patch_adapter": "patch_suggestion_only",
        "exploit_adapter": "sandbox_only",
        "exploit_status": exploit_result.get("status"),
        "unauthorized_targets_blocked": True,
    }
    (output_dir / "evmbench_detect.json").write_text(
        json.dumps(detect, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "evmbench_exploit_sandbox.json").write_text(
        json.dumps(exploit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "evmbench_summary.md").write_text(
        _render_summary(summary),
        encoding="utf-8",
    )
    return summary


def _render_summary(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# EVMbench Adapter Summary",
            "",
            f"- Detect adapter: `{summary['detect_adapter']}`",
            f"- Patch adapter: `{summary['patch_adapter']}`",
            f"- Exploit adapter: `{summary['exploit_adapter']}`",
            f"- Exploit status: `{summary['exploit_status']}`",
            f"- Unauthorized targets blocked: `{summary['unauthorized_targets_blocked']}`",
        ]
    )
