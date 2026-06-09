# DocRunner

**Give it a URL or a public Google Drive/Docs link — it downloads the document,
scrapes the content, and returns clean Markdown.**

DocRunner is a small Python library with two thin wrappers: a **CLI** and a **REST API**.

## Features

- Web pages → readable Markdown (main-content extraction, not the whole page chrome)
- Public **Google Docs** links → exported and converted to Markdown
- Public **Google Drive** files → downloaded (handles the large-file confirm step)
- **PDF** and **DOCX** → text extracted to Markdown
- Optionally follow **PDF/DOCX links** found on a web page
- Content-type sniffing so a `.pdf` URL that's really HTML (or vice-versa) still works

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[api,dev]"     # api + dev extras; drop them for the core only
```

## CLI

```bash
docrunner https://example.com                       # markdown to stdout
docrunner https://example.com -o page.md            # write to a file
docrunner https://docs.google.com/document/d/ID/edit
docrunner https://example.com/report.pdf
docrunner https://example.com --include-linked-docs # also pull linked PDFs/DOCX
docrunner https://example.com --json                # markdown + metadata as JSON
```

Exit code is non-zero on error; warnings go to stderr.

## REST API

```bash
uvicorn docrunner.api:app --reload
```

```bash
curl -s localhost:8000/scrape \
  -H 'content-type: application/json' \
  -d '{"url": "https://example.com", "include_linked_docs": false}'
```

Response:

```json
{
  "markdown": "# Example Domain\n\n...",
  "title": "Example Domain",
  "source_url": "https://example.com",
  "source_kind": "webpage",
  "links": ["https://iana.org/domains/example"],
  "warnings": []
}
```

- `GET /health` → `{"status": "ok"}`
- `POST /scrape` → `422` for unsupported/unscrapeable input, `502` for network failures.

## Library

```python
from docrunner import scrape

result = scrape("https://example.com", include_linked_docs=False)
print(result.title)
print(result.markdown)
```

## How it works

```
URL ─► detect_source ─► fetch (bytes + content-type) ─► pick extractor ─► Markdown
                            │                               │
                     Drive/Docs resolver          html / pdf / docx / text
```

See [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for the design and
[docs/diagrams/system.md](docs/diagrams/system.md) for the component / sequence / state diagrams.

## Development

```bash
pytest          # 22 tests, fully offline (fixtures + mocked transport)
```

## Scope (v1)

Single page per website (no crawling); public Drive/Docs links only (no OAuth). A headless-browser
fetcher for JS-heavy pages and OAuth for private files are the documented extension points.

## License

MIT — see [LICENSE](LICENSE).
