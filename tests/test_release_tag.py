import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_release_tag.py"
SPEC = importlib.util.spec_from_file_location("check_release_tag", SCRIPT_PATH)
assert SPEC is not None
release_tag = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = release_tag
SPEC.loader.exec_module(release_tag)


def test_release_tag_matches_project_version() -> None:
    assert release_tag.require_matching_release_tag("v0.2.1", ROOT / "pyproject.toml") == "0.2.1"


@pytest.mark.parametrize("tag", ["v0.2.0", "v0.2.1-rc1"])
def test_release_tag_rejects_wrong_or_prerelease_version(tag: str) -> None:
    with pytest.raises(ValueError, match="must match project version"):
        release_tag.require_matching_release_tag(tag, ROOT / "pyproject.toml")


def test_publish_workflow_gates_publish_after_validation() -> None:
    workflow = (ROOT / ".github/workflows/publish-pypi.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" not in workflow
    assert "github.event.release.prerelease == false" in workflow
    assert "ref: ${{ github.event.release.tag_name }}" in workflow
    assert workflow.index("scripts/check_release_tag.py") < workflow.index("uv publish")
    assert workflow.index("uv run pytest") < workflow.index("uv publish")
    assert workflow.index("npm run build") < workflow.index("uv publish")
