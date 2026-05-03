from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from smart_contract_audit.models import RagChunk

VULN_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "reentrancy",
        (
            "reentrancy",
            "checks-effects-interaction",
            "checks effects interaction",
            "external call before",
            "call before state",
        ),
    ),
    (
        "unchecked_external_call",
        (
            "unchecked",
            "low-level call",
            "call failed",
            "send failed",
            "transfer failed",
            "success boolean",
        ),
    ),
    ("dangerous_delegatecall", ("delegatecall", "arbitrary call", "arbitrary external call")),
    ("array_length_manipulation", ("array length", "length manipulation")),
    (
        "oracle",
        (
            "oracle",
            "chainlink",
            "price feed",
            "stale price",
            "twap",
            "price manipulation",
            "manipulate price",
            "manipulation attack",
        ),
    ),
    (
        "price_manipulation",
        (
            "slippage",
            "sandwich",
            "front-run",
            "frontrun",
            "front run",
            "amm",
            "pool price",
            "liquidity pool",
            "swap",
            "dex",
            "flash loan",
            "flashloan",
        ),
    ),
    (
        "privilege_escalation",
        (
            "centralization risk",
            "owner can",
            "admin can",
            "onlyowner",
            "access control",
            "missing access",
            "unauthorized",
            "privileged",
            "role",
            "ownership",
            "owner address",
            "setowner",
            "renounceownership",
        ),
    ),
    (
        "upgrade_risk",
        (
            "upgrade",
            "proxy",
            "initializer",
            "implementation contract",
            "uups",
            "transparent proxy",
            "storage gap",
            "storage collision",
            "initialize",
        ),
    ),
    (
        "input_validation",
        (
            "missing validation",
            "zero address",
            "zero amount",
            "input validation",
            "invalid address",
            "validate",
            "require(",
            "should be checked",
            "not validated",
        ),
    ),
    (
        "arithmetic",
        (
            "overflow",
            "underflow",
            "precision loss",
            "rounding",
            "division before multiplication",
            "integer",
            "calculation",
            "decimals",
        ),
    ),
    (
        "denial_of_service",
        (
            "denial of service",
            "dos",
            "unbounded loop",
            "gas limit",
            "out of gas",
            "blocked",
            "revert",
        ),
    ),
    ("timestamp_dependence", ("timestamp", "block.timestamp", "deadline", "time manipulation")),
    ("signature_replay", ("signature", "replay", "nonce", "permit", "eip-712", "ecrecover")),
    ("event_logging", ("missing event", "event emission", "emit event")),
    (
        "state_consistency",
        (
            "state update",
            "balance",
            "vesting",
            "claim",
            "deposit",
            "withdraw",
            "transfer",
            "burn",
            "mint",
        ),
    ),
)


def load_raw_report(path: Path) -> tuple[str, bool]:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8", errors="replace"), False
    if suffix in {".html", ".htm"}:
        return _html_to_text(path), False
    if suffix == ".pdf":
        return _pdf_to_text(path), False
    return path.read_text(encoding="utf-8", errors="replace"), False


def chunk_document(
    path: Path,
    source_id: str | None = None,
    chunk_size: int = 384,
    overlap: int = 64,
    include_unknown: bool = True,
) -> list[RagChunk]:
    text, unsupported_visual_content = load_raw_report(path)
    source = source_id or path.stem
    blocks = _split_preserving_code_blocks(text)
    chunks: list[RagChunk] = []
    buffer: list[str] = []
    token_total = 0

    for block in blocks:
        count = _token_count(block)
        if buffer and token_total + count > chunk_size:
            chunk = _build_chunk(
                source,
                path.stem,
                "\n\n".join(buffer),
                len(chunks),
                unsupported_visual_content,
                path,
            )
            if include_unknown or chunk.vuln_type != "unknown":
                chunks.append(chunk)
            carry = _tail_tokens("\n\n".join(buffer), overlap)
            buffer = [carry] if carry else []
            token_total = _token_count(carry) if carry else 0

        buffer.append(block)
        token_total += count

    if buffer:
        chunk = _build_chunk(
            source,
            path.stem,
            "\n\n".join(buffer),
            len(chunks),
            unsupported_visual_content,
            path,
        )
        if include_unknown or chunk.vuln_type != "unknown":
            chunks.append(chunk)

    return chunks


def _html_to_text(path: Path) -> str:
    html = path.read_text(encoding="utf-8", errors="replace")
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return re.sub(r"<[^>]+>", " ", html)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text("\n")


def _pdf_to_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF parsing requires `uv sync --extra docs`.") from exc

    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _split_preserving_code_blocks(text: str) -> list[str]:
    parts = re.split(r"(```[\s\S]*?```)", text)
    blocks: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        if stripped.startswith("```"):
            blocks.append(stripped)
            continue
        blocks.extend(
            paragraph.strip() for paragraph in re.split(r"\n\s*\n", stripped) if paragraph.strip()
        )
    return blocks


def _build_chunk(
    source_id: str,
    report_id: str,
    content: str,
    index: int,
    unsupported_visual_content: bool,
    source_path: Path,
) -> RagChunk:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    vuln_type = _guess_vuln_type(content)
    return RagChunk(
        chunk_id=f"{source_id}_{index:04d}",
        source_id=source_id,
        report_id=report_id,
        severity=_guess_severity(content),
        vuln_type=vuln_type,
        content=content,
        token_count=_token_count(content),
        created_at=datetime.now(UTC).date().isoformat(),
        sha256=digest,
        unsupported_visual_content=unsupported_visual_content,
        label_source="rule_based" if vuln_type != "unknown" else "unknown",
        label_confidence=0.9 if vuln_type != "unknown" else 0.0,
        eligible_for_eval=vuln_type != "unknown",
        source_path=str(source_path),
        section_title=_section_title(content),
        chunk_index=index,
    )


def _guess_vuln_type(text: str) -> str:
    lowered = text.lower()
    for vuln_type, keywords in VULN_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return vuln_type
    return "unknown"


def _section_title(text: str) -> str:
    for line in text.splitlines():
        stripped = re.sub(r"\s+", " ", line).strip(" #\t")
        if not stripped:
            continue
        if len(stripped) <= 120:
            return stripped
        return stripped[:117] + "..."
    return ""


def _guess_severity(text: str) -> int:
    lowered = text.lower()
    if "critical" in lowered or "high" in lowered:
        return 3
    if "medium" in lowered:
        return 2
    return 1


def _token_count(text: str) -> int:
    try:
        import tiktoken
    except ImportError:
        return max(1, len(re.findall(r"\S+", text)))

    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def _tail_tokens(text: str, count: int) -> str:
    words = re.findall(r"\S+", text)
    return " ".join(words[-count:])
