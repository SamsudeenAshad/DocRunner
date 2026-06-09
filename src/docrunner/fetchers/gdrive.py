"""Resolve public Google Drive / Google Docs share links to download URLs."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

import httpx

from ..models import FetchedContent, FetchError
from .http import USER_AGENT, fetch

# /document/d/<id>/edit, /file/d/<id>/view, etc.
_ID_IN_PATH = re.compile(r"/d/([a-zA-Z0-9_-]{10,})")


def extract_file_id(url: str) -> str | None:
    """Pull the Drive/Docs file id from any common share-link shape."""
    m = _ID_IN_PATH.search(url)
    if m:
        return m.group(1)
    qs = parse_qs(urlparse(url).query)
    if "id" in qs and qs["id"]:
        return qs["id"][0]
    return None


def docs_export_url(file_id: str, fmt: str = "html") -> str:
    """Export URL for a Google Docs *document* (html keeps headings/links)."""
    return f"https://docs.google.com/document/d/{file_id}/export?format={fmt}"


def drive_download_url(file_id: str) -> str:
    """Direct-download URL for a Drive file."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def _confirm_token(resp: httpx.Response) -> str | None:
    """Large public files show a virus-scan interstitial with a confirm token."""
    for key, val in resp.cookies.items():
        if key.startswith("download_warning"):
            return val
    m = re.search(r"confirm=([0-9A-Za-z_-]+)", resp.text or "")
    return m.group(1) if m else None


def fetch_gdocs(url: str, **fetch_kwargs) -> FetchedContent:
    """Fetch a Google Docs document as exported HTML."""
    file_id = extract_file_id(url)
    if not file_id:
        raise FetchError(f"Could not find a Google Docs id in: {url}")
    return fetch(docs_export_url(file_id, "html"), **fetch_kwargs)


def fetch_gdrive_file(url: str, **fetch_kwargs) -> FetchedContent:
    """Fetch a public Drive file, handling the confirm-token interstitial."""
    file_id = extract_file_id(url)
    if not file_id:
        raise FetchError(f"Could not find a Google Drive id in: {url}")

    download = drive_download_url(file_id)
    timeout = fetch_kwargs.get("timeout", 30.0)
    with httpx.Client(
        follow_redirects=True,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        resp = client.get(download)
        ct = resp.headers.get("content-type", "")
        # If Drive returned the HTML interstitial instead of the file, retry
        # with the confirm token so we get the real bytes.
        if "text/html" in ct:
            token = _confirm_token(resp)
            if token:
                resp = client.get(download, params={"confirm": token})
        if resp.status_code >= 400:
            raise FetchError(f"HTTP {resp.status_code} fetching Drive file {file_id}")
        return FetchedContent(
            url=url,
            final_url=str(resp.url),
            content_type=resp.headers.get("content-type", ""),
            data=resp.content,
            filename=file_id,
        )
