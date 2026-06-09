# DocRunner — Task Plan

## Goal
Given a **URL** (website page) or a **Google Drive / Google Docs link**, DocRunner downloads the
document, scrapes its content, and returns clean **Markdown**.

Two surfaces over one shared core:
- **CLI** — `docrunner <url> -o out.md`
- **REST API** — `POST /scrape` → `{ "markdown": "...", "title": "...", "source": "..." }`

## Scope (v1)
- Single page for websites (no crawling).
- Public Google Drive / Docs links only (no OAuth).
- Linked binary documents on a page (PDF / DOCX) are downloaded and converted too (opt-in flag).
- Output is GitHub-flavored Markdown.

## Out of scope (v1)
- Whole-site crawling.
- Authenticated / private Drive files (OAuth, service accounts).
- JavaScript-rendered SPAs requiring a headless browser (documented as a future fetcher).
- OCR of scanned PDFs.

## Source types & handling
| Source            | Detection                                  | Extractor                       |
|-------------------|--------------------------------------------|---------------------------------|
| HTML web page     | `text/html`                                | readability + html→md           |
| Google Docs       | `docs.google.com/document/...`             | export `?format=txt` / `html`   |
| Google Drive file | `drive.google.com/file/d/<id>` / `?id=`    | export download URL by mime     |
| PDF               | `application/pdf` or `.pdf`                | pdf text extraction → md        |
| DOCX              | docx mime / `.docx`                        | docx → md                       |
| Plain text / md   | `text/plain`, `text/markdown`              | passthrough                     |

## Milestones / TODO
- [x] Decide interface (CLI + API), Drive auth (public), depth (single page)
- [x] T1. Core data model: `ScrapeResult`, `SourceKind`, `DocRunnerError`
- [x] T2. URL classifier (`detect_source`) — website vs Drive vs Docs vs direct file
- [x] T3. Fetch layer — HTTP fetch w/ headers, redirects, content-type sniff
- [x] T4. Google Drive/Docs resolver — turn share links into download/export URLs
- [x] T5. Extractors — HTML→md, PDF→md, DOCX→md, text passthrough
- [x] T6. Orchestrator `scrape(url, opts)` ties it together
- [x] T7. CLI (`argparse`) — url, -o, --json, --include-linked-docs
- [x] T8. REST API (FastAPI) — POST /scrape, GET /health
- [x] T9. Tests — classifier, drive resolver, extractor units, e2e on local fixtures (22 passing)
- [x] T10. Packaging — pyproject, README usage

## Acceptance criteria
1. `docrunner https://example.com -o out.md` writes valid markdown with the page title.
2. A public Google Docs link returns its body as markdown.
3. A public Drive PDF link returns extracted text as markdown.
4. `POST /scrape {"url": ...}` returns the same markdown the CLI produces.
5. Unsupported / unreachable URLs return a clear error (CLI exit code ≠ 0; API 422/502).
6. `pytest` passes offline using fixtures.
