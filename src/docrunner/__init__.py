"""DocRunner — download documents from a URL or Google Drive link, return Markdown."""

from .core import scrape
from .models import (
    DocRunnerError,
    ExtractError,
    FetchError,
    FetchedContent,
    ScrapeResult,
    SourceKind,
    UnsupportedSourceError,
)

__version__ = "0.1.0"

__all__ = [
    "scrape",
    "ScrapeResult",
    "SourceKind",
    "FetchedContent",
    "DocRunnerError",
    "UnsupportedSourceError",
    "FetchError",
    "ExtractError",
]
