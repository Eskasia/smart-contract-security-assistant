from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import URLError

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_adoption_metrics.py"
SPEC = importlib.util.spec_from_file_location("update_adoption_metrics", SCRIPT_PATH)
assert SPEC is not None
metrics = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = metrics
SPEC.loader.exec_module(metrics)


BASE_METRICS = """# Adoption Metrics

Status: current manual tracker
Updated: 2026-06-02

## Current metrics

| Metric | Current | Target | Evidence |
|---|---:|---:|---|
| GitHub stars | 0 | 100 | old stars |
| GitHub forks | 0 | 30 | old forks |
| External testers | 0 | 10 | keep testers unchanged |
| Public triage cases | 0 | 3 | keep triage unchanged |
| Feedback issues | 0 | 5 | keep feedback unchanged |
| Testimonials | 0 | 10 | keep testimonials unchanged |
| Monthly downloads | 0 | 1000 | old downloads |
| External OSS adoptions | 0 | 2 | keep external adoption unchanged |
"""


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def fake_urlopen_for(payloads: dict[str, dict[str, Any]]):
    def fake_urlopen(request: Any, timeout: int) -> FakeResponse:
        assert timeout == 20
        return FakeResponse(payloads[request.full_url])

    return fake_urlopen


def test_render_metrics_document_updates_only_source_backed_rows() -> None:
    snapshot = metrics.DistributionSnapshot(
        collection_date=date(2026, 6, 17),
        stars=7,
        forks=3,
        package_version="0.2.1",
        release_asset_downloads=12,
    )

    updated = metrics.render_metrics_document(BASE_METRICS, snapshot)

    assert "Updated: 2026-06-17" in updated
    assert "| GitHub stars | 7 | 100 | GitHub repo API snapshot on 2026-06-17" in updated
    assert "| GitHub forks | 3 | 30 | GitHub repo API snapshot on 2026-06-17" in updated
    assert "| Monthly downloads | 0 | 1000 | PyPI package" in updated
    assert "GitHub `v0.2.1` release asset download total was `12`" in updated
    assert "| External testers | 0 | 10 | keep testers unchanged |" in updated
    assert "| Public triage cases | 0 | 3 | keep triage unchanged |" in updated
    assert "| Testimonials | 0 | 10 | keep testimonials unchanged |" in updated
    assert "| External OSS adoptions | 0 | 2 | keep external adoption unchanged |" in updated


def test_collect_snapshot_uses_official_public_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    payloads = {
        metrics.GITHUB_REPO_API: {"stargazers_count": 4, "forks_count": 2},
        metrics.GITHUB_RELEASE_API: {
            "assets": [{"download_count": 5}, {"download_count": 6}],
        },
        metrics.PYPI_JSON_API: {"info": {"version": "0.2.1"}},
    }
    monkeypatch.setattr(metrics, "urlopen", fake_urlopen_for(payloads))

    snapshot = metrics.collect_snapshot(today=date(2026, 6, 17))

    assert snapshot.stars == 4
    assert snapshot.forks == 2
    assert snapshot.package_version == "0.2.1"
    assert snapshot.release_asset_downloads == 11


def test_source_failure_leaves_metrics_file_unchanged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    metrics_path = tmp_path / "metrics.md"
    metrics_path.write_text(BASE_METRICS, encoding="utf-8")

    def failing_urlopen(_request: Any, timeout: int) -> FakeResponse:
        assert timeout == 20
        raise URLError("rate limited")

    monkeypatch.setattr(metrics, "urlopen", failing_urlopen)

    with pytest.raises(metrics.MetricsSourceError):
        metrics.update_metrics_file(metrics_path, write=True)

    assert metrics_path.read_text(encoding="utf-8") == BASE_METRICS
