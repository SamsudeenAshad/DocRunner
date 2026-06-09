"""HTML → Markdown: isolate main content, convert, collect outbound links."""

from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as md
from readability import Document

from ..models import FetchedContent, ScrapeResult, SourceKind


def _title(html: str, soup: BeautifulSoup) -> str:
    try:
        t = Document(html).short_title()
        if t:
            return t.strip()
    except Exception:
        pass
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else ""


def _collect_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"].strip())
        if href.startswith(("http://", "https://")) and href not in seen:
            seen.add(href)
            links.append(href)
    return links


def to_markdown(content: FetchedContent) -> ScrapeResult:
    html = content.text
    warnings: list[str] = []
    full_soup = BeautifulSoup(html, "lxml")
    title = _title(html, full_soup)
    links = _collect_links(full_soup, content.final_url)

    # Readability narrows to the main article; fall back to the whole body.
    try:
        main_html = Document(html).summary(html_partial=True)
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"readability failed, using full body: {exc}")
        main_html = str(full_soup.body or full_soup)

    markdown = md(main_html, heading_style="ATX", strip=["script", "style"]).strip()
    if not markdown:
        warnings.append("no extractable text content")

    return ScrapeResult(
        markdown=markdown,
        title=title,
        source_url=content.url,
        source_kind=SourceKind.WEBPAGE,
        links=links,
        warnings=warnings,
    )
