from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


def standard_refs_for(vulnerability_type: str) -> list[dict[str, Any]]:
    mapping = _mapping_by_type().get(vulnerability_type)
    if not mapping:
        return []
    refs = mapping.get("standard_refs", [])
    if not isinstance(refs, list):
        return []
    return [dict(ref) for ref in refs if isinstance(ref, dict)]


def report_tags_for(vulnerability_type: str) -> list[str]:
    mapping = _mapping_by_type().get(vulnerability_type)
    if not mapping:
        return []
    tags = mapping.get("report_tags", [])
    if not isinstance(tags, list):
        return []
    return [str(tag) for tag in tags]


def standards_mapping_path() -> Path:
    return Path(__file__).resolve().parents[2] / "standards_mapping.yml"


@lru_cache(maxsize=1)
def load_standards_mapping() -> dict[str, Any]:
    path = standards_mapping_path()
    if not path.exists():
        return {"version": 1, "mappings": []}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _mapping_by_type() -> dict[str, dict[str, Any]]:
    payload = load_standards_mapping()
    mappings = payload.get("mappings", [])
    if not isinstance(mappings, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in mappings:
        if not isinstance(item, dict):
            continue
        internal_type = item.get("internal_type")
        if isinstance(internal_type, str):
            result[internal_type] = item
    return result
