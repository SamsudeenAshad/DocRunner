"""Plain text / Markdown passthrough with minimal cleanup."""

from __future__ import annotations

import re

from ..models import FetchedContent, ScrapeResult, SourceKind


def to_markdown(content: FetchedContent) -> ScrapeResult:
    text = content.text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    title = content.filename or ""
    if not title:
        for line in text.splitlines():
            if line.strip():
                title = line.strip().lstrip("# ").strip()[:120]
                break

    return ScrapeResult(
        markdown=text,
        title=title,
        source_url=content.url,
        source_kind=SourceKind.TEXT,
        warnings=[] if text else ["empty document"],
    )
