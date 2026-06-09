"""Map a URL (and later a content-type) to a :class:`SourceKind`."""

from __future__ import annotations

from urllib.parse import urlparse

from .models import SourceKind

_PDF_CT = ("application/pdf",)
_DOCX_CT = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)
_TEXT_CT = ("text/plain", "text/markdown", "text/x-markdown")
_HTML_CT = ("text/html", "application/xhtml+xml")


def detect_source(url: str) -> SourceKind:
    """Classify a URL by host + path heuristics, before anything is fetched."""
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()

    if not parsed.scheme or not host:
        return SourceKind.UNKNOWN

    if "docs.google.com" in host:
        # /document/, /spreadsheets/, /presentation/ — treat document as gdocs.
        if "/document/" in path:
            return SourceKind.GDOCS
        return SourceKind.GDOCS  # other google-docs editors export as text/html too

    if "drive.google.com" in host:
        return SourceKind.GDRIVE_FILE

    if path.endswith(".pdf"):
        return SourceKind.PDF
    if path.endswith(".docx"):
        return SourceKind.DOCX
    if path.endswith((".txt", ".md", ".markdown")):
        return SourceKind.TEXT

    return SourceKind.WEBPAGE


def kind_from_content_type(content_type: str) -> SourceKind | None:
    """Re-classify after fetch, since servers often lie in the URL.

    Returns ``None`` when the content-type is inconclusive (caller keeps the
    URL-based guess).
    """
    ct = (content_type or "").split(";", 1)[0].strip().lower()
    if not ct:
        return None
    if ct in _PDF_CT:
        return SourceKind.PDF
    if ct in _DOCX_CT:
        return SourceKind.DOCX
    if ct in _HTML_CT:
        return SourceKind.WEBPAGE
    if ct in _TEXT_CT:
        return SourceKind.TEXT
    return None
