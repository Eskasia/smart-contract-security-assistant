from __future__ import annotations

import io
import json
import os
import stat
import urllib.request
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from smart_contract_audit.cli import main
from smart_contract_audit.source_import import (
    ImportLimits,
    _AllowlistedRedirectHandler,
    cleanup_import_staging,
    import_explorer_source,
    import_github_source,
    stage_zip_archive,
)


def test_stage_zip_archive_keeps_solidity_and_project_markers(tmp_path: Path) -> None:
    archive = _zip_bytes(
        {
            "repo-main/contracts/Vault.sol": "pragma solidity ^0.8.19; contract Vault {}",
            "repo-main/foundry.toml": "[profile.default]\nsrc = 'contracts'\n",
            "repo-main/README.md": "# ignored\n",
            "repo-main/node_modules/pkg/Ignored.sol": "pragma solidity ^0.8.19;",
        }
    )

    result = stage_zip_archive(
        archive,
        tmp_path,
        import_name="fixture",
        limits=ImportLimits(max_files=8, max_total_bytes=4_096, max_single_file_bytes=1_024),
    )

    assert result.input_path == result.staging_dir
    assert result.to_dict()["trust_level"] == "untrusted"
    assert (result.staging_dir / "contracts" / "Vault.sol").exists()
    assert (result.staging_dir / "foundry.toml").exists()
    assert not (result.staging_dir / "README.md").exists()
    assert not (result.staging_dir / "node_modules").exists()


def test_stage_zip_archive_rejects_zip_slip(tmp_path: Path) -> None:
    archive = _zip_bytes({"../../escape.sol": "pragma solidity ^0.8.19; contract Escape {}"})

    with pytest.raises(ValueError, match="unsafe"):
        stage_zip_archive(archive, tmp_path, import_name="fixture")


def test_stage_zip_archive_rejects_nested_archive_and_duplicate_paths(tmp_path: Path) -> None:
    archive = _zip_bytes(
        {
            "repo-main/contracts/Vault.sol": "pragma solidity ^0.8.19; contract Vault {}",
            "repo-main/contracts/inner.zip": "nested",
        }
    )
    with pytest.raises(ValueError, match="nested archive"):
        stage_zip_archive(archive, tmp_path, import_name="fixture")

    duplicate = _zip_with_entries(
        [
            ("repo-main/contracts/Vault.sol", "pragma solidity ^0.8.19; contract Vault {}"),
            ("repo-main/contracts/./Vault.sol", "pragma solidity ^0.8.19; contract Vault {}"),
        ]
    )
    with pytest.raises(ValueError, match="duplicate"):
        stage_zip_archive(duplicate, tmp_path, import_name="fixture")


def test_stage_zip_archive_rejects_symlink_members(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        info = zipfile.ZipInfo("repo-main/contracts/Vault.sol")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "contracts/RealVault.sol")

    with pytest.raises(ValueError, match="symlink"):
        stage_zip_archive(buffer.getvalue(), tmp_path, import_name="fixture")


def test_import_github_source_downloads_repository_archive(tmp_path: Path) -> None:
    calls: list[str] = []
    archive = _zip_bytes(
        {
            "owner-repo-main/contracts/Vault.sol": "pragma solidity ^0.8.19; contract Vault {}",
            "owner-repo-main/foundry.toml": "[profile.default]\nsrc = 'contracts'\n",
        }
    )

    result = import_github_source(
        "https://github.com/example/repo/tree/main/contracts",
        tmp_path,
        downloader=lambda url: calls.append(url) or archive,
    )

    assert calls == ["https://codeload.github.com/example/repo/zip/main"]
    assert result.input_path == result.staging_dir / "contracts"
    assert (result.input_path / "Vault.sol").exists()


def test_import_github_source_rejects_non_allowlisted_host(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="github.com"):
        import_github_source("https://gitlab.com/example/repo", tmp_path)


def test_import_github_source_rejects_oversized_remote_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "smart_contract_audit.source_import._urlopen_request",
        lambda request, *, allowed_hosts: _oversized_response(),
    )

    with pytest.raises(ValueError, match="Remote source response exceeds"):
        import_github_source(
            "https://github.com/example/repo",
            tmp_path,
            limits=ImportLimits(
                max_files=8,
                max_total_bytes=32,
                max_single_file_bytes=32,
            ),
        )


def test_remote_import_redirect_handler_rejects_non_allowlisted_target() -> None:
    handler = _AllowlistedRedirectHandler({"codeload.github.com"})
    request = urllib.request.Request("https://codeload.github.com/example/repo/zip/main")

    with pytest.raises(ValueError, match="allowlist"):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://169.254.169.254/latest/meta-data",
        )


def test_import_explorer_source_parses_single_file_response(tmp_path: Path) -> None:
    payload = {
        "status": "1",
        "message": "OK",
        "result": [
            {
                "ContractName": "Vault",
                "SourceCode": "pragma solidity ^0.8.19; contract Vault {}",
            }
        ],
    }

    result = import_explorer_source(
        api_host="api.etherscan.io",
        address="0x" + "12" * 20,
        destination_root=tmp_path,
        opener=lambda request: _fake_response(payload, request.full_url),
    )

    assert result.input_path.name == "Vault.sol"
    assert result.input_path.read_text(encoding="utf-8").startswith("pragma solidity")


def test_import_explorer_source_parses_multi_file_sourcecode(tmp_path: Path) -> None:
    payload = {
        "status": "1",
        "message": "OK",
        "result": [
            {
                "ContractName": "Vault",
                "SourceCode": (
                    "{{"
                    '"language":"Solidity",'
                    '"sources":{'
                    '"contracts/Vault.sol":{"content":"pragma solidity ^0.8.19; '
                    'contract Vault {}"},'
                    '"contracts/lib/Base.sol":{"content":"pragma solidity ^0.8.19; '
                    'contract Base {}"}'
                    "}"
                    "}}"
                ),
            }
        ],
    }

    result = import_explorer_source(
        api_host="api-sepolia.etherscan.io",
        address="0x" + "34" * 20,
        destination_root=tmp_path,
        opener=lambda request: _fake_response(payload, request.full_url),
    )

    assert result.input_path == result.staging_dir
    assert (result.staging_dir / "contracts" / "Vault.sol").exists()
    assert (result.staging_dir / "contracts" / "lib" / "Base.sol").exists()


def test_import_explorer_source_rejects_error_payload(tmp_path: Path) -> None:
    payload = {"status": "0", "message": "NOTOK", "result": "Contract source code not verified"}

    with pytest.raises(ValueError, match="verified"):
        import_explorer_source(
            api_host="api.etherscan.io",
            address="0x" + "56" * 20,
            destination_root=tmp_path,
            opener=lambda request: _fake_response(payload, request.full_url),
        )


def test_import_explorer_source_rejects_oversized_remote_response(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Remote source response exceeds"):
        import_explorer_source(
            api_host="api.etherscan.io",
            address="0x" + "56" * 20,
            destination_root=tmp_path,
            limits=ImportLimits(
                max_files=8,
                max_total_bytes=32,
                max_single_file_bytes=32,
            ),
            opener=lambda request: _oversized_response(),
        )


def test_import_explorer_source_rejects_non_allowlisted_host(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="allowlist"):
        import_explorer_source(
            api_host="api.basescan.org",
            address="0x" + "78" * 20,
            destination_root=tmp_path,
            opener=lambda request: _fake_response({}, request.full_url),
        )


def test_cli_analyze_passes_external_tool_configuration(
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

    main(
        [
            "analyze",
            str(contract),
            "--external-tool",
            "echidna",
            "--external-timeout-seconds",
            "99",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["contract_id"] == "contract"
    assert calls == [
        {
            "contract_path": contract,
            "output_dir": Path("reports"),
            "trace_db": None,
            "dataset_chunks": Path("data/dataset_v1.0/chunks/chunks.jsonl"),
            "rag_mode": "balanced",
            "model_path": None,
            "external_tools": ("echidna",),
            "external_timeout_seconds": 99,
            "native_build_policy": "disabled",
        }
    ]


def test_cli_import_source_prints_staged_input_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    archive_path = tmp_path / "fixture.zip"
    archive_path.write_bytes(
        _zip_bytes({"repo-main/Vault.sol": "pragma solidity ^0.8.19; contract Vault {}"})
    )
    staged = tmp_path / "imports" / "fixture"
    staged.mkdir(parents=True)
    staged_file = staged / "Vault.sol"
    staged_file.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")

    monkeypatch.setattr(
        "smart_contract_audit.cli.import_local_archive",
        lambda **kwargs: SimpleNamespace(
            import_id="import_123",
            source_kind="zip",
            input_path=staged_file,
            staging_dir=staged,
            extracted_files=("Vault.sol",),
            total_bytes=42,
            to_dict=lambda: {
                "import_id": "import_123",
                "source_kind": "zip_base64",
                "input_path": str(staged_file),
                "staging_dir": str(staged),
                "extracted_files": ["Vault.sol"],
                "total_bytes": 42,
                "imported": True,
                "trust_level": "untrusted",
            },
        ),
    )

    main(
        [
            "import-source",
            "--zip-file",
            str(archive_path),
            "--out-dir",
            str(tmp_path / "imports"),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["source_kind"] == "zip_base64"
    assert payload["input_path"] == str(staged_file)
    assert payload["trust_level"] == "untrusted"


def test_clean_import_staging_removes_only_expired_import_dirs(tmp_path: Path) -> None:
    imports_dir = tmp_path / "imports"
    expired = imports_dir / "import_111111111111-old"
    fresh = imports_dir / "import_222222222222-fresh"
    unrelated = imports_dir / "manual"
    expired.mkdir(parents=True)
    fresh.mkdir()
    unrelated.mkdir()
    old_time = 1_000.0
    fresh_time = 2_000.0
    for path, timestamp in ((expired, old_time), (fresh, fresh_time), (unrelated, old_time)):
        path.touch()
        path.chmod(0o755)
        os.utime(path, (timestamp, timestamp))

    removed = cleanup_import_staging(imports_dir, ttl_seconds=500, now=1_600.0)

    assert removed == [expired.resolve()]
    assert not expired.exists()
    assert fresh.exists()
    assert unrelated.exists()


def _zip_bytes(files: dict[str, str]) -> bytes:
    return _zip_with_entries(list(files.items()))


def _zip_with_entries(entries: list[tuple[str, str]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return buffer.getvalue()


def _fake_response(payload: dict[str, object], url: str) -> object:
    body = json.dumps(payload).encode("utf-8")

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        def read(self, size: int = -1) -> bytes:
            if size >= 0:
                return body[:size]
            return body

        @property
        def url(self) -> str:
            return url

    return _Response()


def _oversized_response() -> object:
    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        def read(self, size: int = -1) -> bytes:
            length = (size if size >= 0 else 1) + 1
            return b"x" * length

    return _Response()
