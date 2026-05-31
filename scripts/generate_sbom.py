from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    tool_matrix = json.loads((ROOT / "tool_matrix.yml").read_text(encoding="utf-8"))
    tools = tool_matrix.get("tools", [])
    if not isinstance(tools, list):
        raise ValueError("tool_matrix.yml `tools` must be a list")

    sbom_dir = ROOT / "reports" / "sbom"
    licenses_dir = ROOT / "reports" / "licenses"
    sbom_dir.mkdir(parents=True, exist_ok=True)
    licenses_dir.mkdir(parents=True, exist_ok=True)

    components = [_component_for(tool) for tool in tools if isinstance(tool, dict)]
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": "urn:uuid:00000000-0000-4000-8000-000000000001",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "component": {
                "type": "application",
                "name": "smart-contract-security-assistant",
                "version": "0.1.0",
            },
        },
        "components": components,
    }

    (sbom_dir / "tool-matrix.cdx.json").write_text(
        json.dumps(bom, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (licenses_dir / "tool-matrix-licenses.txt").write_text(
        _license_inventory(tools),
        encoding="utf-8",
    )
    print("wrote reports/sbom/tool-matrix.cdx.json")
    print("wrote reports/licenses/tool-matrix-licenses.txt")
    return 0


def _component_for(tool: dict) -> dict:
    license_name = str(tool.get("license", "UNKNOWN"))
    return {
        "type": "application",
        "name": str(tool.get("name", tool.get("id", "unknown"))),
        "bom-ref": f"tool:{tool.get('id', 'unknown')}",
        "licenses": [{"license": {"name": license_name}}],
        "externalReferences": [
            {
                "type": "vcs",
                "url": str(tool.get("source_url", "")),
            }
        ],
        "properties": [
            {"name": "scsa:category", "value": str(tool.get("category", ""))},
            {"name": "scsa:bundled", "value": str(tool.get("bundled", ""))},
            {"name": "scsa:required", "value": str(tool.get("required", ""))},
            {"name": "scsa:role", "value": str(tool.get("scsa_role", ""))},
        ],
    }


def _license_inventory(tools: list) -> str:
    lines = [
        "# Tool Matrix License Inventory",
        "",
        "Generated from `tool_matrix.yml`.",
        "",
        "| Tool | License | Bundled | Source |",
        "|---|---|---:|---|",
    ]
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        lines.append(
            "| {name} | {license} | {bundled} | {source_url} |".format(
                name=tool.get("name", ""),
                license=tool.get("license", ""),
                bundled=str(tool.get("bundled", "")),
                source_url=tool.get("source_url", ""),
            )
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
