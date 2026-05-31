from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TOOL_FIELDS = {
    "id",
    "name",
    "category",
    "source_url",
    "license",
    "bundled",
    "invocation",
    "required",
    "output_used",
    "scsa_role",
}
README_TOOL_NAMES = {
    "Slither",
    "Aderyn",
    "Echidna",
    "Medusa",
    "Mythril",
    "Halmos",
}
EXTERNAL_REGISTRY_TOOLS = {"aderyn", "echidna", "medusa", "mythril", "halmos"}
EXTERNAL_FINDING_TYPES = {"invariant_violation", "formal_property_violation"}


def main() -> int:
    errors: list[str] = []
    tool_matrix = _read_json(ROOT / "tool_matrix.yml")
    standards_mapping = _read_json(ROOT / "standards_mapping.yml")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    tools = tool_matrix.get("tools", [])
    if not isinstance(tools, list):
        errors.append("tool_matrix.yml: `tools` must be a list")
        tools = []

    tool_ids: set[str] = set()
    tool_names: set[str] = set()
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            errors.append(f"tool_matrix.yml: tool at index {index} must be an object")
            continue
        missing = REQUIRED_TOOL_FIELDS - set(tool)
        if missing:
            errors.append(f"tool_matrix.yml: {tool.get('id', index)} missing {sorted(missing)}")
        tool_id = str(tool.get("id", ""))
        tool_name = str(tool.get("name", ""))
        tool_ids.add(tool_id)
        tool_names.add(tool_name)
        if tool.get("bundled") is not False:
            errors.append(f"tool_matrix.yml: {tool_id} must explicitly set bundled=false")
        if not tool.get("license"):
            errors.append(f"tool_matrix.yml: {tool_id} missing license")
        if not str(tool.get("source_url", "")).startswith("https://"):
            errors.append(f"tool_matrix.yml: {tool_id} source_url must be https")

    for name in README_TOOL_NAMES:
        if name in readme and name not in tool_names:
            errors.append(f"README mentions {name}, but tool_matrix.yml has no matching tool")

    missing_registry_tools = EXTERNAL_REGISTRY_TOOLS - tool_ids
    if missing_registry_tools:
        errors.append(
            "tool_matrix.yml missing external registry tools: "
            + ", ".join(sorted(missing_registry_tools))
        )

    _check_standards_mapping(standards_mapping, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("tool_matrix and standards_mapping checks passed")
    return 0


def _check_standards_mapping(payload: dict, errors: list[str]) -> None:
    mappings = payload.get("mappings", [])
    if not isinstance(mappings, list):
        errors.append("standards_mapping.yml: `mappings` must be a list")
        return

    by_type: dict[str, dict] = {}
    for item in mappings:
        if not isinstance(item, dict):
            errors.append("standards_mapping.yml: each mapping must be an object")
            continue
        internal_type = item.get("internal_type")
        if not isinstance(internal_type, str):
            errors.append("standards_mapping.yml: mapping missing internal_type")
            continue
        by_type[internal_type] = item
        refs = item.get("standard_refs", [])
        if not isinstance(refs, list):
            errors.append(f"standards_mapping.yml: {internal_type} standard_refs must be a list")
            continue
        for ref in refs:
            if not isinstance(ref, dict):
                errors.append(f"standards_mapping.yml: {internal_type} has non-object ref")
                continue
            for field in ("standard", "id", "label", "confidence"):
                if not ref.get(field):
                    errors.append(
                        f"standards_mapping.yml: {internal_type} ref missing {field}"
                    )

    from smart_contract_audit.config import DETECTOR_MAPPING

    normalized_types = {value[0] for value in DETECTOR_MAPPING.values()}
    normalized_types.update(EXTERNAL_FINDING_TYPES)
    missing = normalized_types - set(by_type)
    if missing:
        errors.append(
            "standards_mapping.yml missing normalized types: " + ", ".join(sorted(missing))
        )

    high_types = {
        value[0] for value in DETECTOR_MAPPING.values() if value[1] >= 3
    }
    for internal_type in sorted(high_types):
        refs = by_type.get(internal_type, {}).get("standard_refs", [])
        has_required_ref = any(
            isinstance(ref, dict)
            and str(ref.get("standard", "")).startswith(("OWASP", "SWC"))
            for ref in refs
        )
        if not has_required_ref:
            errors.append(
                f"standards_mapping.yml: high finding type {internal_type} "
                "needs OWASP or SWC ref"
            )


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{path} not found", file=sys.stderr)
        raise
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
