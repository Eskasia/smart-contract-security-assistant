from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_pyproject() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_project_metadata_is_distribution_ready() -> None:
    project = load_pyproject()["project"]

    assert project["name"] == "smart-contract-security-assistant"
    assert project["readme"] == "README.md"
    assert project["requires-python"] == ">=3.11"
    assert project["license"] == "MIT"
    assert set(project["keywords"]) >= {
        "solidity",
        "security",
        "slither",
        "smart-contracts",
        "audit",
    }
    assert "License :: OSI Approved :: MIT License" in project["classifiers"]
    assert "Programming Language :: Python :: 3.11" in project["classifiers"]


def test_cli_entry_point_is_packaged() -> None:
    pyproject = load_pyproject()

    assert pyproject["project"]["scripts"]["scsa"] == "smart_contract_audit.cli:main"
    assert pyproject["project"]["urls"]["Repository"].endswith(
        "/Eskasia/smart-contract-security-assistant"
    )
