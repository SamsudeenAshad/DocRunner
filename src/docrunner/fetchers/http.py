"""HTTP fetching with redirects, a UA header, a timeout, and a size cap."""

from __future__ import annotations

from urllib.parse import unquote, urlparse

import httpx

from ..models import FetchedContent, FetchError

USER_AGENT = "DocRunner/0.1 (+https://github.com/SamsudeenAshad/DocRunner)"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_BYTES = 25 * 1024 * 1024  # 25 MiB


def _filename_from(final_url: str, headers: httpx.Headers) -> str:
    disp = headers.get("content-disposition", "")
    if "filename=" in disp:
        name = disp.split("filename=", 1)[1].strip().strip('";')
        if name:
            return unquote(name)
    path = urlparse(final_url).path
    return unquote(path.rsplit("/", 1)[-1]) if path else ""


def fetch(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    client: httpx.Client | None = None,
    extra_headers: dict[str, str] | None = None,
) -> FetchedContent:
    """GET ``url`` and return its bytes, following redirects.

    Raises :class:`FetchError` on network failure, non-2xx status, or when the
    body exceeds ``max_bytes``.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if extra_headers:
        headers.update(extra_headers)

    owns_client = client is None
    if owns_client:
        client = httpx.Client(
            follow_redirects=True, timeout=timeout, headers=headers
        )
    try:
        with client.stream("GET", url, headers=headers) as resp:
            if resp.status_code >= 400:
                raise FetchError(
                    f"HTTP {resp.status_code} fetching {url}"
                )
            chunks: list[bytes] = []
            total = 0
            for chunk in resp.iter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    raise FetchError(
                        f"Response exceeds max_bytes ({max_bytes}) for {url}"
                    )
                chunks.append(chunk)
            data = b"".join(chunks)
            return FetchedContent(
                url=url,
                final_url=str(resp.url),
                content_type=resp.headers.get("content-type", ""),
                data=data,
                filename=_filename_from(str(resp.url), resp.headers),
            )
    except httpx.HTTPError as exc:  # connect/timeout/etc.
        raise FetchError(f"Network error fetching {url}: {exc}") from exc
    finally:
        if owns_client:
            client.close()
