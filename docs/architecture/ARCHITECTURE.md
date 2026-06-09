# DocRunner — Architecture

## Overview
DocRunner is a small Python library with two thin wrappers (CLI, REST API) over a shared core.
The core is a **pipeline**: classify → fetch → extract → render markdown.

```
URL ──► detect_source ──► fetch (bytes + content-type) ──► pick extractor ──► Markdown
                              │                                  │
                       Drive/Docs resolver              html / pdf / docx / text
```

## Layers

### 1. Core models (`models.py`)
- `SourceKind` enum: `WEBPAGE | GDOCS | GDRIVE_FILE | PDF | DOCX | TEXT | UNKNOWN`
- `FetchedContent`: `url, final_url, content_type, data: bytes, filename`
- `ScrapeResult`: `markdown, title, source_url, source_kind, links, warnings`
- `DocRunnerError` (+ `UnsupportedSourceError`, `FetchError`, `ExtractError`)

### 2. Source detection (`classify.py`)
`detect_source(url) -> SourceKind` using host + path + extension heuristics.
Google hosts get special routing so we can rewrite to export/download URLs.

### 3. Fetch layer (`fetchers/`)
- `http.py` — `fetch(url)` via `httpx` with redirects, UA header, size cap, content-type.
- `gdrive.py` — resolves Drive/Docs share links:
  - Docs: `https://docs.google.com/document/d/<id>/export?format=html`
  - Drive file: `https://drive.google.com/uc?export=download&id=<id>` (handles the
    "virus scan" confirm-token interstitial for large files).

### 4. Extractors (`extractors/`)
Each exposes `to_markdown(content: FetchedContent) -> ScrapeResult`.
- `html.py` — `readability-lxml` to isolate main content, `markdownify` to convert,
  collects outbound links (for optional linked-doc following).
- `pdf.py` — `pypdf` text extraction, paragraph reflow.
- `docx.py` — `python-docx` walking paragraphs/headings/tables.
- `text.py` — passthrough / minimal cleanup.

### 5. Orchestrator (`core.py`)
`scrape(url, *, include_linked_docs=False, max_bytes=...) -> ScrapeResult`
1. `detect_source` → choose fetch strategy (gdrive resolver vs plain http).
2. Fetch bytes + content-type. If content-type disagrees with URL guess, re-classify.
3. Dispatch to extractor by effective kind.
4. If `include_linked_docs` and source is a webpage: find PDF/DOCX links, fetch+extract
   each, append under `## Linked documents` (best-effort, failures become warnings).
5. Return `ScrapeResult`.

### 6. Interfaces
- `cli.py` — `argparse`; prints markdown to stdout or `-o file`; non-zero exit on error.
- `api.py` — FastAPI app: `POST /scrape` (body `{url, include_linked_docs?}`), `GET /health`.
  Maps `DocRunnerError` → HTTP 422; network failures → 502.

## Dependencies
| Purpose            | Library            |
|--------------------|--------------------|
| HTTP client        | `httpx`            |
| HTML main content  | `readability-lxml` |
| HTML → Markdown    | `markdownify`      |
| HTML parsing       | `beautifulsoup4`   |
| PDF text           | `pypdf`            |
| DOCX               | `python-docx`      |
| API                | `fastapi`,`uvicorn`|

## Error & resilience strategy
- Single fetch timeout + max-bytes guard (avoid downloading huge files).
- Extractors never raise into the API; they attach `warnings` and degrade.
- Linked-doc fetching is best-effort and isolated per-link.

## Design rationale
- **Library-first**: CLI and API are ~30 lines each; all logic is testable without I/O via
  injecting `FetchedContent`.
- **Content-type over extension**: servers lie in URLs; we re-classify after fetch.
- **No headless browser in v1**: keeps the footprint small; a `playwright` fetcher is the
  documented extension point for JS-heavy pages.
