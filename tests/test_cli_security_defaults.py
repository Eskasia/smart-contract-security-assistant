from __future__ import annotations

import json
from pathlib import Path

import pytest

from smart_contract_audit.cli import main


def test_cli_analyze_defaults_native_build_policy_to_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    contract = tmp_path / "Vault.sol"
    contract.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")
    calls: list[dict[str, object]] = []

    class _Report:
        def to_dict(self) -> dict[str, object]:
            return {"contract_id": "contract"}

    def fake_analyze_contract(**kwargs: object) -> _Report:
        calls.append(kwargs)
        return _Report()

    monkeypatch.setattr("smart_contract_audit.cli.analyze_contract", fake_analyze_contract)

    main(["analyze", str(contract), "--out-dir", str(tmp_path / "reports")])

    assert json.loads(capsys.readouterr().out)["contract_id"] == "contract"
    assert calls[0]["native_build_policy"] == "disabled"


def test_cli_api_rejects_external_host_without_api_token(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["api", "--host", "0.0.0.0", "--out-dir", str(tmp_path / "reports")])

    assert "--api-token" in str(exc.value)


def test_cli_api_passes_explicit_demo_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_run_api_server(**kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr("smart_contract_audit.http_api.run_api_server", fake_run_api_server)

    main(
        [
            "api",
            "--out-dir",
            str(tmp_path / "reports"),
            "--allow-tokenless-local-demo",
            "--allow-any-input-root",
        ]
    )

    assert calls[0]["allow_tokenless_local_demo"] is True
    assert calls[0]["allow_any_input_root"] is True
    assert calls[0]["native_build_policy"] == "disabled"
