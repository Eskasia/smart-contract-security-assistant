"""Update source-backed adoption metrics without inventing adoption claims."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = "Eskasia/smart-contract-security-assistant"
PACKAGE = "smart-contract-security-assistant"
RELEASE_TAG = "v0.2.1"
GITHUB_REPO_API = f"https://api.github.com/repos/{REPO}"
GITHUB_RELEASE_API = f"{GITHUB_REPO_API}/releases/tags/{RELEASE_TAG}"
PYPI_JSON_API = f"https://pypi.org/pypi/{PACKAGE}/json"
DEFAULT_METRICS_PATH = Path("docs/adoption/metrics.md")


class MetricsSourceError(RuntimeError):
    """Raised when a required public source cannot be collected."""


@dataclass(frozen=True)
class DistributionSnapshot:
    collection_date: date
    stars: int
    forks: int
    package_version: str
    release_asset_downloads: int


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "scsa-metrics"})
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise MetricsSourceError(f"failed to fetch {url}: {exc}") from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise MetricsSourceError(f"failed to parse JSON from {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MetricsSourceError(f"expected JSON object from {url}")
    return payload


def require_int(payload: dict[str, Any], field: str, url: str) -> int:
    value = payload.get(field)
    if not isinstance(value, int):
        raise MetricsSourceError(f"expected integer field {field!r} from {url}")
    return value


def collect_snapshot(today: date | None = None) -> DistributionSnapshot:
    repo_payload = fetch_json(GITHUB_REPO_API)
    release_payload = fetch_json(GITHUB_RELEASE_API)
    pypi_payload = fetch_json(PYPI_JSON_API)

    package_info = pypi_payload.get("info")
    if not isinstance(package_info, dict) or not isinstance(package_info.get("version"), str):
        raise MetricsSourceError(f"expected package info.version from {PYPI_JSON_API}")

    assets = release_payload.get("assets")
    if not isinstance(assets, list):
        raise MetricsSourceError(f"expected release assets list from {GITHUB_RELEASE_API}")
    release_asset_downloads = 0
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("download_count"), int):
            raise MetricsSourceError(
                f"expected integer asset download_count from {GITHUB_RELEASE_API}"
            )
        release_asset_downloads += asset["download_count"]

    return DistributionSnapshot(
        collection_date=today or datetime.now(UTC).date(),
        stars=require_int(repo_payload, "stargazers_count", GITHUB_REPO_API),
        forks=require_int(repo_payload, "forks_count", GITHUB_REPO_API),
        package_version=package_info["version"],
        release_asset_downloads=release_asset_downloads,
    )


def replace_line(lines: list[str], prefix: str, replacement: str) -> None:
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise MetricsSourceError(f"expected exactly one line starting with {prefix!r}")
    lines[matches[0]] = replacement


def render_metrics_document(original: str, snapshot: DistributionSnapshot) -> str:
    collected = snapshot.collection_date.isoformat()
    lines = original.splitlines()
    replace_line(lines, "Updated:", f"Updated: {collected}")
    replace_line(
        lines,
        "| GitHub stars |",
        "| GitHub stars | "
        f"{snapshot.stars} | 100 | GitHub repo API snapshot on {collected}: "
        f"`stargazers_count={snapshot.stars}` |",
    )
    replace_line(
        lines,
        "| GitHub forks |",
        "| GitHub forks | "
        f"{snapshot.forks} | 30 | GitHub repo API snapshot on {collected}: "
        f"`forks_count={snapshot.forks}` |",
    )
    replace_line(
        lines,
        "| Monthly downloads |",
        "| Monthly downloads | 0 | 1000 | "
        f"PyPI package `{PACKAGE}` is published at version `{snapshot.package_version}`, "
        "but PyPI JSON does not provide a package-hosted monthly download counter; "
        f"GitHub `{RELEASE_TAG}` release asset download total was "
        f"`{snapshot.release_asset_downloads}` on {collected} |",
    )
    return "\n".join(lines) + "\n"


def update_metrics_file(metrics_path: Path, write: bool) -> bool:
    snapshot = collect_snapshot()
    original = metrics_path.read_text(encoding="utf-8")
    updated = render_metrics_document(original, snapshot)
    changed = updated != original
    if write and changed:
        metrics_path.write_text(updated, encoding="utf-8")
    elif not write:
        sys.stdout.write(updated)
    return changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update source-backed adoption metrics from official public APIs."
    )
    parser.add_argument(
        "--metrics-path",
        type=Path,
        default=DEFAULT_METRICS_PATH,
        help="Path to docs/adoption/metrics.md.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write updates in place. Without this flag, render the updated document to stdout.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        changed = update_metrics_file(args.metrics_path, args.write)
    except MetricsSourceError as exc:
        print(f"metrics update failed: {exc}", file=sys.stderr)
        return 1
    if args.write:
        print("metrics document updated" if changed else "metrics document already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
