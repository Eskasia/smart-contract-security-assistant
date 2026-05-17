from __future__ import annotations

import base64
import binascii
import io
import json
import re
import stat
import urllib.parse
import urllib.request
import uuid
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

PROJECT_MARKER_FILES = {
    "foundry.toml",
    "remappings.txt",
    "package.json",
    "hardhat.config.js",
    "hardhat.config.ts",
    "hardhat.config.cjs",
    "hardhat.config.mjs",
}
EXCLUDED_PATH_PARTS = {
    ".git",
    ".venv",
    "artifacts",
    "broadcast",
    "cache",
    "dist",
    "node_modules",
    "out",
}
DEFAULT_GITHUB_ZIP_URL_TEMPLATE = "https://codeload.github.com/{owner}/{repo}/zip/{ref}"
URL_SCHEMES = {"https"}
GITHUB_ALLOWED_HOSTS = {"github.com", "www.github.com", "codeload.github.com"}
ETHERSCAN_ALLOWED_HOSTS = {"api.etherscan.io", "api-sepolia.etherscan.io"}
NESTED_ARCHIVE_SUFFIXES = {".zip", ".tar", ".tgz", ".tar.gz", ".7z", ".rar"}
HEX_ADDRESS = re.compile(r"^0x[a-fA-F0-9]{40}$")
GITHUB_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")
REMOTE_RESPONSE_OVERHEAD_BYTES = 65_536

Downloader = Callable[[str], bytes]
Opener = Callable[[urllib.request.Request], Any]


@dataclass(frozen=True)
class ImportLimits:
    max_files: int = 128
    max_total_bytes: int = 5_000_000
    max_single_file_bytes: int = 1_000_000


@dataclass(frozen=True)
class ImportedSource:
    import_id: str
    source_kind: str
    input_path: Path
    staging_dir: Path
    extracted_files: tuple[str, ...]
    total_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "import_id": self.import_id,
            "source_kind": self.source_kind,
            "input_path": str(self.input_path),
            "staging_dir": str(self.staging_dir),
            "extracted_files": list(self.extracted_files),
            "total_bytes": self.total_bytes,
            "imported": True,
            "trust_level": "untrusted",
        }


@dataclass(frozen=True)
class GitHubArchiveRequest:
    owner: str
    repo: str
    ref: str
    subpath: str | None


def decode_archive_base64(value: str) -> bytes:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("archive_base64 must be a non-empty base64 string.")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise ValueError("archive_base64 must be valid base64.") from exc


def import_local_archive(
    *,
    archive_path: Path,
    destination_root: Path,
    limits: ImportLimits | None = None,
) -> ImportedSource:
    resolved = archive_path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"zip_file does not exist: {resolved}")
    return stage_zip_archive(
        resolved.read_bytes(),
        destination_root,
        import_name=resolved.stem,
        source_kind="zip_base64",
        limits=limits,
    )


def stage_zip_archive(
    archive_bytes: bytes,
    destination_root: Path,
    *,
    import_name: str,
    source_kind: str = "zip_base64",
    limits: ImportLimits | None = None,
    requested_subpath: str | None = None,
) -> ImportedSource:
    resolved_limits = limits or ImportLimits()
    if not archive_bytes:
        raise ValueError("archive_bytes must be non-empty.")

    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("archive payload must be a valid ZIP archive.") from exc

    extracted: dict[str, bytes] = {}
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            _validate_archive_member(info, resolved_limits)
            archive_path = _normalize_archive_path(info.filename)
            if _is_nested_archive_path(archive_path):
                raise ValueError("ZIP archive contains a nested archive member.")
            if not _is_useful_archive_member(archive_path):
                continue
            content = archive.read(info)
            if len(content) > resolved_limits.max_single_file_bytes:
                raise ValueError(
                    "Import exceeds max_single_file_bytes of "
                    f"{resolved_limits.max_single_file_bytes}."
                )
            if archive_path in extracted:
                raise ValueError("ZIP archive contains duplicate normalized paths.")
            extracted[archive_path] = content

    if not extracted:
        raise ValueError("ZIP archive does not contain supported Solidity source files.")

    stripped = _strip_single_root_directory(extracted)
    return _stage_bytes(
        stripped,
        destination_root=destination_root,
        import_name=import_name,
        source_kind=source_kind,
        requested_subpath=requested_subpath,
        limits=resolved_limits,
    )


def import_github_source(
    github_url: str,
    destination_root: Path,
    *,
    downloader: Downloader | None = None,
    limits: ImportLimits | None = None,
) -> ImportedSource:
    resolved_limits = limits or ImportLimits()
    request = parse_github_archive_request(github_url)
    url = DEFAULT_GITHUB_ZIP_URL_TEMPLATE.format(
        owner=request.owner,
        repo=request.repo,
        ref=request.ref,
    )
    data = (
        downloader(url)
        if downloader is not None
        else _download_bytes(
            url,
            max_bytes=_remote_response_max_bytes(resolved_limits),
            allowed_hosts=GITHUB_ALLOWED_HOSTS,
        )
    )
    return stage_zip_archive(
        data,
        destination_root,
        import_name=f"{request.owner}-{request.repo}",
        source_kind="github_archive",
        limits=resolved_limits,
        requested_subpath=request.subpath,
    )


def import_explorer_source(
    *,
    api_host: str,
    address: str,
    destination_root: Path,
    api_key: str | None = None,
    opener: Opener | None = None,
    limits: ImportLimits | None = None,
) -> ImportedSource:
    resolved_limits = limits or ImportLimits()
    normalized_api_host = _validate_allowlisted_host(
        api_host,
        field_name="api_host",
        allowed_hosts=ETHERSCAN_ALLOWED_HOSTS,
    )
    if not isinstance(address, str) or not HEX_ADDRESS.fullmatch(address):
        raise ValueError("address must be a 42-character hex string.")

    query = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
    }
    if api_key:
        query["apikey"] = api_key
    request = urllib.request.Request(
        f"https://{normalized_api_host}/api?{urllib.parse.urlencode(query)}",
        headers={"Accept": "application/json"},
    )
    payload = _open_json(
        request,
        opener
        or (
            lambda request: _urlopen_request(
                request,
                allowed_hosts=ETHERSCAN_ALLOWED_HOSTS,
            )
        ),
        max_bytes=_remote_response_max_bytes(resolved_limits),
        allowed_hosts=ETHERSCAN_ALLOWED_HOSTS if opener is None else None,
    )
    result = _extract_explorer_result(payload)
    contract_name = result.get("ContractName")
    source_code = result.get("SourceCode")
    if not isinstance(contract_name, str) or not contract_name.strip():
        contract_name = "Contract"
    if not isinstance(source_code, str) or not source_code.strip():
        raise ValueError("Explorer response did not include SourceCode.")

    parsed_sources = _parse_explorer_source_code(source_code, contract_name.strip())
    return _stage_text(
        parsed_sources,
        destination_root=destination_root,
        import_name=contract_name.strip(),
        source_kind="etherscan_api",
        limits=resolved_limits,
    )


def parse_github_archive_request(github_url: str) -> GitHubArchiveRequest:
    parsed = urllib.parse.urlparse(_validate_https_url(github_url, field_name="url"))
    host = parsed.netloc.lower()
    if host not in GITHUB_ALLOWED_HOSTS:
        raise ValueError("url must point to github.com.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError("url must include owner and repository.")
    owner = _validate_github_path_segment(parts[0], field_name="owner")
    repo = _validate_github_path_segment(parts[1], field_name="repo")
    ref = "HEAD"
    subpath: str | None = None
    if host == "codeload.github.com":
        if len(parts) >= 4 and parts[2] == "zip":
            ref = _validate_github_path_segment(parts[3], field_name="ref")
        return GitHubArchiveRequest(owner=owner, repo=repo, ref=ref, subpath=None)
    if len(parts) >= 4 and parts[2] in {"tree", "blob"}:
        ref = _validate_github_path_segment(parts[3], field_name="ref")
        remainder = parts[4:]
        if remainder:
            subpath = "/".join(remainder)

    return GitHubArchiveRequest(owner=owner, repo=repo, ref=ref, subpath=subpath)


def _open_json(
    request: urllib.request.Request,
    opener: Opener,
    *,
    max_bytes: int,
    allowed_hosts: set[str] | None = None,
) -> dict[str, Any]:
    with opener(request) as response:
        if allowed_hosts is not None:
            _validate_response_url(response, allowed_hosts=allowed_hosts)
        raw = _read_limited_response(response, max_bytes=max_bytes)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Remote source response must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Remote source response must be a JSON object.")
    return payload


def _extract_explorer_result(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    result = payload.get("result")
    if payload.get("status") not in {"1", 1, None}:
        message = result if isinstance(result, str) else payload.get("message", "Explorer error")
        raise ValueError(str(message))
    if not isinstance(result, list) or not result:
        raise ValueError("Explorer response result must contain at least one contract.")
    if not isinstance(result[0], Mapping):
        raise ValueError("Explorer response entry must be an object.")
    return result[0]


def _parse_explorer_source_code(source_code: str, contract_name: str) -> dict[str, str]:
    stripped = source_code.strip()
    if stripped.startswith("{{") and stripped.endswith("}}"):
        stripped = stripped[1:-1]

    parsed: object | None = None
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None

    if isinstance(parsed, Mapping):
        sources = parsed.get("sources")
        if isinstance(sources, Mapping):
            return _normalize_explorer_sources(sources)
        return _normalize_explorer_sources(parsed)

    filename = _safe_contract_filename(contract_name)
    return {filename: source_code}


def _normalize_explorer_sources(sources: Mapping[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for name, value in sources.items():
        if isinstance(value, Mapping):
            content = value.get("content")
        else:
            content = value
        if not isinstance(content, str):
            continue
        safe_name = _normalize_archive_path(str(name))
        if not safe_name.endswith(".sol"):
            continue
        if safe_name in normalized:
            raise ValueError("Explorer source bundle contains duplicate normalized paths.")
        normalized[safe_name] = content
    if not normalized:
        raise ValueError("Explorer source bundle did not contain Solidity files.")
    return normalized


def _stage_text(
    files: Mapping[str, str],
    *,
    destination_root: Path,
    import_name: str,
    source_kind: str,
    limits: ImportLimits,
    requested_subpath: str | None = None,
) -> ImportedSource:
    encoded = {name: content.encode("utf-8") for name, content in files.items()}
    return _stage_bytes(
        encoded,
        destination_root=destination_root,
        import_name=import_name,
        source_kind=source_kind,
        requested_subpath=requested_subpath,
        limits=limits,
    )


def _stage_bytes(
    files: Mapping[str, bytes],
    *,
    destination_root: Path,
    import_name: str,
    source_kind: str,
    limits: ImportLimits,
    requested_subpath: str | None,
) -> ImportedSource:
    safe_files = sorted(files.items())
    if len(safe_files) > limits.max_files:
        raise ValueError(f"Import exceeds max_files of {limits.max_files}.")

    total_bytes = 0
    for _, content in safe_files:
        if len(content) > limits.max_single_file_bytes:
            raise ValueError(
                f"Import exceeds max_single_file_bytes of {limits.max_single_file_bytes}."
            )
        total_bytes += len(content)
        if total_bytes > limits.max_total_bytes:
            raise ValueError(f"Import exceeds max_total_bytes of {limits.max_total_bytes}.")

    import_id = f"import_{uuid.uuid4().hex[:12]}"
    staging_dir = destination_root.expanduser().resolve() / f"{import_id}-{_slugify(import_name)}"
    staging_dir.mkdir(parents=True, exist_ok=False)

    extracted_files: list[str] = []
    for relative_name, content in safe_files:
        target = (staging_dir / relative_name).resolve()
        if not target.is_relative_to(staging_dir):
            raise ValueError("Import path resolved outside staging directory.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        extracted_files.append(relative_name)

    input_path = _resolve_input_path(staging_dir, extracted_files, requested_subpath)
    return ImportedSource(
        import_id=import_id,
        source_kind=source_kind,
        input_path=input_path,
        staging_dir=staging_dir,
        extracted_files=tuple(extracted_files),
        total_bytes=total_bytes,
    )


def _resolve_input_path(
    staging_dir: Path,
    extracted_files: list[str],
    requested_subpath: str | None,
) -> Path:
    if requested_subpath:
        safe_subpath = _normalize_archive_path(requested_subpath)
        candidate = (staging_dir / safe_subpath).resolve()
        if not candidate.exists() or not candidate.is_relative_to(staging_dir):
            raise ValueError("Requested import subpath was not present in the staged source.")
        if candidate.is_file() and candidate.suffix != ".sol":
            raise ValueError(
                "Requested import subpath must resolve to a Solidity file or directory."
            )
        return candidate

    sol_files = [name for name in extracted_files if name.endswith(".sol")]
    marker_files = [name for name in extracted_files if Path(name).name in PROJECT_MARKER_FILES]
    if len(sol_files) == 1 and not marker_files:
        return staging_dir / sol_files[0]
    return staging_dir


def _normalize_archive_path(raw_path: str) -> str:
    if "\\" in raw_path:
        raise ValueError("Archive entry path contains unsafe backslashes.")
    normalized = raw_path.strip("/")
    if not normalized:
        raise ValueError("Archive entry path must not be empty.")
    path = PurePosixPath(normalized)
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Archive entry path contains unsafe traversal.")
    if normalized.startswith("/") or ":" in parts[0]:
        raise ValueError("Archive entry path contains unsafe root components.")
    return str(path)


def _is_useful_archive_member(relative_path: str) -> bool:
    parts = PurePosixPath(relative_path).parts
    if any(part in EXCLUDED_PATH_PARTS for part in parts):
        return False
    filename = parts[-1]
    return filename.endswith(".sol") or filename in PROJECT_MARKER_FILES


def _strip_single_root_directory(files: Mapping[str, bytes]) -> dict[str, bytes]:
    parts_list = [PurePosixPath(path).parts for path in files]
    if not parts_list:
        return {}
    first_parts = {parts[0] for parts in parts_list if len(parts) > 1}
    if len(first_parts) != 1 or any(len(parts) == 1 for parts in parts_list):
        return dict(files)

    stripped: dict[str, bytes] = {}
    for path, content in files.items():
        parts = PurePosixPath(path).parts
        stripped_path = "/".join(parts[1:])
        if stripped_path in stripped:
            raise ValueError("ZIP archive contains duplicate normalized paths.")
        stripped[stripped_path] = content
    return stripped


def _safe_contract_filename(contract_name: str) -> str:
    slug = _slugify(contract_name)
    if not slug.endswith(".sol"):
        slug = f"{slug}.sol"
    return slug


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-._")
    return normalized or "import"


def _validate_https_url(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty URL.")
    parsed = urllib.parse.urlparse(value.strip())
    if parsed.scheme not in URL_SCHEMES:
        raise ValueError(f"{field_name} must use https.")
    if not parsed.netloc:
        raise ValueError(f"{field_name} must include a host.")
    return value.strip()


def _validate_github_path_segment(value: str, *, field_name: str) -> str:
    if not GITHUB_PATH_SEGMENT.fullmatch(value) or value in {".", ".."}:
        raise ValueError(f"GitHub {field_name} contains unsafe characters.")
    return value


def _validate_allowlisted_host(
    value: str,
    *,
    field_name: str,
    allowed_hosts: set[str],
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty host.")
    host = value.strip().lower()
    if host not in allowed_hosts:
        allowed = ", ".join(sorted(allowed_hosts))
        raise ValueError(f"{field_name} must be in the allowlist: {allowed}.")
    return host


def _validate_archive_member(info: zipfile.ZipInfo, limits: ImportLimits) -> None:
    if info.file_size > limits.max_single_file_bytes:
        raise ValueError(
            f"Import exceeds max_single_file_bytes of {limits.max_single_file_bytes}."
        )
    mode = (info.external_attr >> 16) & 0o170000
    if mode == stat.S_IFLNK:
        raise ValueError("ZIP archive contains a symlink entry.")
    if mode not in {0, stat.S_IFREG}:
        raise ValueError("ZIP archive contains an unsupported special file entry.")


def _is_nested_archive_path(relative_path: str) -> bool:
    lowered = relative_path.lower()
    return any(lowered.endswith(suffix) for suffix in NESTED_ARCHIVE_SUFFIXES)


class _AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str]) -> None:
        self._allowed_hosts = allowed_hosts
        super().__init__()

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Mapping[str, str],
        newurl: str,
    ) -> urllib.request.Request | None:
        _validate_remote_url(newurl, field_name="redirect_url", allowed_hosts=self._allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _validate_request_url(
    request: urllib.request.Request,
    *,
    allowed_hosts: set[str],
) -> None:
    _validate_remote_url(request.full_url, field_name="url", allowed_hosts=allowed_hosts)


def _validate_response_url(response: Any, *, allowed_hosts: set[str]) -> None:
    geturl = getattr(response, "geturl", None)
    final_url = geturl() if callable(geturl) else getattr(response, "url", None)
    if final_url:
        _validate_remote_url(str(final_url), field_name="response_url", allowed_hosts=allowed_hosts)


def _validate_remote_url(value: str, *, field_name: str, allowed_hosts: set[str]) -> None:
    parsed = urllib.parse.urlparse(_validate_https_url(value, field_name=field_name))
    host = parsed.hostname.lower() if parsed.hostname else ""
    if host not in allowed_hosts:
        allowed = ", ".join(sorted(allowed_hosts))
        raise ValueError(f"{field_name} must stay inside the allowlist: {allowed}.")


def _remote_response_max_bytes(limits: ImportLimits) -> int:
    return limits.max_total_bytes + REMOTE_RESPONSE_OVERHEAD_BYTES


def _read_limited_response(response: Any, *, max_bytes: int) -> bytes:
    raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError(
            "Remote source response exceeds max_total_bytes of "
            f"{max_bytes - REMOTE_RESPONSE_OVERHEAD_BYTES}."
        )
    return raw


def _download_bytes(url: str, *, max_bytes: int, allowed_hosts: set[str]) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "application/zip"})
    with _urlopen_request(request, allowed_hosts=allowed_hosts) as response:
        _validate_response_url(response, allowed_hosts=allowed_hosts)
        return _read_limited_response(response, max_bytes=max_bytes)


def _urlopen_request(request: urllib.request.Request, *, allowed_hosts: set[str]) -> Any:
    _validate_request_url(request, allowed_hosts=allowed_hosts)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _AllowlistedRedirectHandler(allowed_hosts),
    )
    return opener.open(request, timeout=30)
