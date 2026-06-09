"""End-to-end orchestrator tests using a mocked httpx transport (offline)."""

import httpx
import pytest

import docrunner.fetchers.http as http_mod
from docrunner.core import scrape
from docrunner.models import UnsupportedSourceError

PAGE_HTML = b"""<html><head><title>Mock Article</title></head>
<body><article><h1>Mock Article</h1>
<p>Paragraph one with enough text to survive readability extraction.</p>
<p>Paragraph two, also reasonably long so the article body is detected.</p>
</article></body></html>"""


@pytest.fixture
def mock_client(monkeypatch):
    """Patch http.fetch to use a MockTransport-backed client."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(".pdf"):
            return httpx.Response(200, content=b"%PDF-1.4 not-real",
                                  headers={"content-type": "application/pdf"})
        return httpx.Response(200, content=PAGE_HTML,
                              headers={"content-type": "text/html; charset=utf-8"})

    transport = httpx.MockTransport(handler)
    real_fetch = http_mod.fetch

    def patched_fetch(url, **kwargs):
        kwargs.pop("client", None)
        client = httpx.Client(transport=transport, follow_redirects=True)
        try:
            return real_fetch(url, client=client, **{
                k: v for k, v in kwargs.items() if k in ("timeout", "max_bytes")
            })
        finally:
            client.close()

    monkeypatch.setattr(http_mod, "fetch", patched_fetch)
    # core.py imported http module, so patching the module attr is enough.
    return patched_fetch


def test_scrape_webpage(mock_client):
    res = scrape("https://example.com/article")
    assert res.title == "Mock Article"
    assert "Paragraph one" in res.markdown


def test_scrape_rejects_non_http():
    with pytest.raises(UnsupportedSourceError):
        scrape("ftp://example.com/file")
