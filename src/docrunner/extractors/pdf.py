"""PDF → Markdown via pypdf text extraction with light paragraph reflow."""

from __future__ import annotations

import io
import re

from pypdf import PdfReader

from ..models import ExtractError, FetchedContent, ScrapeResult, SourceKind


def _reflow(raw: str) -> str:
    # Join lines that were hard-wrapped mid-sentence; keep blank-line paragraphs.
    lines = [ln.rstrip() for ln in raw.splitlines()]
    out: list[str] = []
    buf: list[str] = []
    for ln in lines:
        if not ln.strip():
            if buf:
                out.append(" ".join(buf))
                buf = []
            out.append("")
        else:
            buf.append(ln.strip())
    if buf:
        out.append(" ".join(buf))
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def to_markdown(content: FetchedContent) -> ScrapeResult:
    warnings: list[str] = []
    try:
        reader = PdfReader(io.BytesIO(content.data))
    except Exception as exc:
        raise ExtractError(f"Could not open PDF: {exc}") from exc

    title = ""
    if reader.metadata and reader.metadata.title:
        title = str(reader.metadata.title).strip()
    if not title and content.filename:
        title = content.filename

    parts: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:
            warnings.append(f"page {i}: extraction failed ({exc})")
            continue
        page_text = _reflow(page_text)
        if page_text:
            parts.append(page_text)

    body = "\n\n---\n\n".join(parts)
    if not body:
        warnings.append("no extractable text (possibly a scanned/image PDF)")

    markdown = (f"# {title}\n\n{body}" if title else body).strip()
    return ScrapeResult(
        markdown=markdown,
        title=title,
        source_url=content.url,
        source_kind=SourceKind.PDF,
        warnings=warnings,
    )
