"""Orchestrator: classify → fetch → extract → render markdown."""

from __future__ import annotations

from urllib.parse import urlparse

from . import extractors
from .classify import detect_source, kind_from_content_type
from .fetchers import http
from .fetchers import gdrive
from .models import (
    DocRunnerError,
    FetchedContent,
    ScrapeResult,
    SourceKind,
    UnsupportedSourceError,
)

# Linked documents we will follow when include_linked_docs=True.
_LINKED_EXT = (".pdf", ".docx")
_MAX_LINKED = 10


def _fetch_for_kind(url: str, kind: SourceKind, **fetch_kwargs) -> FetchedContent:
    if kind == SourceKind.GDOCS:
        return gdrive.fetch_gdocs(url, **fetch_kwargs)
    if kind == SourceKind.GDRIVE_FILE:
        return gdrive.fetch_gdrive_file(url, **fetch_kwargs)
    return http.fetch(url, **fetch_kwargs)


def _effective_kind(url_kind: SourceKind, content: FetchedContent) -> SourceKind:
    """Trust the fetched content-type over the URL guess when it's conclusive."""
    ct_kind = kind_from_content_type(content.content_type)
    if ct_kind is None:
        # Drive files have no useful URL extension; rely on content-type only.
        if url_kind == SourceKind.GDRIVE_FILE:
            return SourceKind.TEXT
        return url_kind
    # A Drive/Docs link that turned out to be a PDF/DOCX should use that extractor.
    if url_kind in (SourceKind.GDOCS, SourceKind.GDRIVE_FILE):
        return ct_kind
    return ct_kind


def scrape(
    url: str,
    *,
    include_linked_docs: bool = False,
    timeout: float = http.DEFAULT_TIMEOUT,
    max_bytes: int = http.DEFAULT_MAX_BYTES,
) -> ScrapeResult:
    """Fetch ``url`` and return its content as a :class:`ScrapeResult`.

    Set ``include_linked_docs`` to also follow PDF/DOCX links found on a web
    page and append them under a "Linked documents" section (best-effort).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsupportedSourceError(
            f"Only http(s) URLs are supported, got: {url!r}"
        )

    url_kind = detect_source(url)
    if url_kind == SourceKind.UNKNOWN:
        raise UnsupportedSourceError(f"Could not classify URL: {url}")

    fetch_kwargs = {"timeout": timeout, "max_bytes": max_bytes}
    content = _fetch_for_kind(url, url_kind, **fetch_kwargs)
    kind = _effective_kind(url_kind, content)
    result = extractors.to_markdown(content, kind)

    if include_linked_docs and kind == SourceKind.WEBPAGE:
        _append_linked_docs(result, fetch_kwargs)

    return result


def _append_linked_docs(result: ScrapeResult, fetch_kwargs: dict) -> None:
    targets = [u for u in result.links
               if urlparse(u).path.lower().endswith(_LINKED_EXT)][:_MAX_LINKED]
    if not targets:
        return

    sections: list[str] = []
    for link in targets:
        try:
            kind = detect_source(link)
            content = _fetch_for_kind(link, kind, **fetch_kwargs)
            kind = _effective_kind(kind, content)
            sub = extractors.to_markdown(content, kind)
            heading = sub.title or link
            sections.append(f"### {heading}\n\n_Source: {link}_\n\n{sub.markdown}")
            result.warnings.extend(sub.warnings)
        except DocRunnerError as exc:
            result.warnings.append(f"linked doc {link}: {exc}")

    if sections:
        result.markdown += "\n\n## Linked documents\n\n" + "\n\n---\n\n".join(sections)
