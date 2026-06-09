"""Extractors convert :class:`FetchedContent` into a :class:`ScrapeResult`."""

from ..models import ExtractError, FetchedContent, ScrapeResult, SourceKind
from . import docx as _docx
from . import html as _html
from . import pdf as _pdf
from . import text as _text


def to_markdown(content: FetchedContent, kind: SourceKind) -> ScrapeResult:
    """Dispatch to the extractor for ``kind``."""
    if kind in (SourceKind.WEBPAGE, SourceKind.GDOCS):
        return _html.to_markdown(content)
    if kind == SourceKind.PDF:
        return _pdf.to_markdown(content)
    if kind == SourceKind.DOCX:
        return _docx.to_markdown(content)
    if kind == SourceKind.TEXT:
        return _text.to_markdown(content)
    raise ExtractError(f"No extractor for source kind: {kind}")


__all__ = ["to_markdown"]
