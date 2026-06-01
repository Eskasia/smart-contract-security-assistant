from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

from smart_contract_audit.validation.schema import REPORT_SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_sync_module() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "sync_report_schema.py"
    spec = importlib.util.spec_from_file_location("sync_report_schema", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_report_schema_matches_internal_schema() -> None:
    sync_report_schema = _load_sync_module()
    public_schema = json.loads(sync_report_schema.DEFAULT_SCHEMA_PATH.read_text())
    rendered_schema = json.loads(sync_report_schema.render_schema())

    assert rendered_schema == REPORT_SCHEMA
    assert public_schema == rendered_schema


def test_schema_sync_check_detects_stale_file(tmp_path: Path) -> None:
    sync_report_schema = _load_sync_module()
    stale_schema = tmp_path / "report.schema.json"
    stale_schema.write_text("{}\n", encoding="utf-8")

    assert sync_report_schema.sync_schema(stale_schema, check=True) == 1


def test_schema_sync_writes_generated_schema(tmp_path: Path) -> None:
    sync_report_schema = _load_sync_module()
    target = tmp_path / "schema" / "report.schema.json"

    assert sync_report_schema.sync_schema(target) == 0
    assert json.loads(target.read_text(encoding="utf-8")) == REPORT_SCHEMA
