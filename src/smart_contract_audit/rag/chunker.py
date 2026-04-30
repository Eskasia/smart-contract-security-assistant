from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from smart_contract_audit.models import RagChunk

VULN_KEYWORDS = {
    "reentrancy": "reentrancy",
    "access control": "access_control",
    "unchecked": "unchecked_external_call",
    "delegatecall": "dangerous_delegatecall",
    "array length": "array_length_manipulation",
}


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
            chunks.append(
                _build_chunk(
                    source, path.stem, "\n\n".join(buffer), len(chunks), unsupported_visual_content
                )
            )
            carry = _tail_tokens("\n\n".join(buffer), overlap)
            buffer = [carry] if carry else []
            token_total = _token_count(carry) if carry else 0

        buffer.append(block)
        token_total += count

    if buffer:
        chunks.append(
            _build_chunk(
                source, path.stem, "\n\n".join(buffer), len(chunks), unsupported_visual_content
            )
        )

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
    )


def _guess_vuln_type(text: str) -> str:
    lowered = text.lower()
    for keyword, vuln_type in VULN_KEYWORDS.items():
        if keyword in lowered:
            return vuln_type
    return "unknown"


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
