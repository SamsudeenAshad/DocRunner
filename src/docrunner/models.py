"""Core data models and error types for DocRunner."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SourceKind(str, Enum):
    """The kind of source a URL points at, used to choose an extractor."""

    WEBPAGE = "webpage"
    GDOCS = "gdocs"
    GDRIVE_FILE = "gdrive_file"
    PDF = "pdf"
    DOCX = "docx"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class FetchedContent:
    """Raw bytes retrieved from a source plus the metadata needed to extract it."""

    url: str
    final_url: str
    content_type: str
    data: bytes
    filename: str = ""

    @property
    def text(self) -> str:
        """Best-effort decode of the payload as UTF-8 text."""
        return self.data.decode("utf-8", errors="replace")


@dataclass
class ScrapeResult:
    """The Markdown output plus provenance and any non-fatal warnings."""

    markdown: str
    title: str
    source_url: str
    source_kind: SourceKind
    links: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "markdown": self.markdown,
            "title": self.title,
            "source_url": self.source_url,
            "source_kind": self.source_kind.value,
            "links": self.links,
            "warnings": self.warnings,
        }


class DocRunnerError(Exception):
    """Base class for all DocRunner errors."""


class UnsupportedSourceError(DocRunnerError):
    """The URL points at something we cannot handle."""


class FetchError(DocRunnerError):
    """Network / HTTP failure while retrieving content."""


class ExtractError(DocRunnerError):
    """The content could not be converted to Markdown."""
