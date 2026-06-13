"""FastAPI wrapper exposing DocRunner over HTTP.

Run with: ``uvicorn docrunner.api:app --reload``
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .core import scrape
from .models import FetchError, UnsupportedSourceError, ExtractError

app = FastAPI(
    title="DocRunner",
    version="0.1.0",
    description="Download a web page or Google Drive/Docs link and return Markdown.",
)


class ScrapeRequest(BaseModel):
    url: str = Field(..., description="Web page URL or public Google Drive/Docs link")
    include_linked_docs: bool = Field(
        False, description="Also fetch PDF/DOCX links found on a web page"
    )
    timeout: float = Field(30.0, gt=0, le=120)


class ScrapeResponse(BaseModel):
    markdown: str
    title: str
    source_url: str
    source_kind: str
    links: list[str]
    warnings: list[str]


@app.get("/", response_class=HTMLResponse)
def ui():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>DocRunner</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f4f6f9; color: #1a1a2e; min-height: 100vh; }
  header { background: #1a1a2e; color: white; padding: 1rem 2rem; display: flex; align-items: center; gap: 0.75rem; }
  header h1 { font-size: 1.4rem; font-weight: 600; }
  header span { font-size: 0.85rem; opacity: 0.6; }
  .container { max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
  .card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
  .input-row { display: flex; gap: 0.75rem; flex-wrap: wrap; }
  input[type=url] { flex: 1; min-width: 200px; padding: 0.65rem 1rem; border: 1.5px solid #d0d5dd; border-radius: 8px; font-size: 0.95rem; outline: none; transition: border 0.2s; }
  input[type=url]:focus { border-color: #4f46e5; }
  .options { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem; font-size: 0.9rem; color: #555; }
  button { background: #4f46e5; color: white; border: none; padding: 0.65rem 1.4rem; border-radius: 8px; font-size: 0.95rem; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
  button:hover { background: #4338ca; }
  button:disabled { background: #a5b4fc; cursor: not-allowed; }
  #status { margin-top: 1rem; font-size: 0.9rem; color: #6b7280; }
  #result { margin-top: 1.5rem; display: none; }
  #result h2 { font-size: 1.1rem; color: #374151; margin-bottom: 0.75rem; }
  #meta { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
  .badge { background: #ede9fe; color: #4f46e5; padding: 0.2rem 0.65rem; border-radius: 20px; font-size: 0.8rem; font-weight: 500; }
  #markdown-output { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.25rem; overflow-x: auto; line-height: 1.7; }
  #markdown-output h1,h2,h3 { margin: 1rem 0 0.4rem; }
  #markdown-output table { border-collapse: collapse; width: 100%; margin: 0.75rem 0; }
  #markdown-output th, #markdown-output td { border: 1px solid #d1d5db; padding: 0.4rem 0.75rem; text-align: left; }
  #markdown-output th { background: #f3f4f6; }
  #markdown-output p { margin: 0.4rem 0; }
  #markdown-output a { color: #4f46e5; }
  #error { margin-top: 1rem; background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 0.75rem 1rem; border-radius: 8px; display: none; }
</style>
</head>
<body>
<header>
  <h1>DocRunner</h1>
  <span>URL → Markdown</span>
</header>
<div class="container">
  <div class="card">
    <div class="input-row">
      <input type="url" id="url" placeholder="https://example.com or Google Drive link" />
      <button id="btn" onclick="run()">Scrape</button>
    </div>
    <div class="options">
      <input type="checkbox" id="linked" />
      <label for="linked">Include linked PDFs / DOCX</label>
    </div>
    <div id="status"></div>
    <div id="error"></div>
  </div>

  <div id="result" class="card" style="margin-top:1.25rem">
    <h2 id="title"></h2>
    <div id="meta"></div>
    <div id="markdown-output"></div>
  </div>
</div>

<script>
async function run() {
  const url = document.getElementById('url').value.trim();
  if (!url) return;
  const btn = document.getElementById('btn');
  const status = document.getElementById('status');
  const errBox = document.getElementById('error');
  const result = document.getElementById('result');
  errBox.style.display = 'none';
  result.style.display = 'none';
  btn.disabled = true;
  status.textContent = 'Scraping…';

  try {
    const res = await fetch('/scrape', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, include_linked_docs: document.getElementById('linked').checked})
    });
    const data = await res.json();
    if (!res.ok) { throw new Error(data.detail || 'Request failed'); }

    document.getElementById('title').textContent = data.title || 'Result';
    document.getElementById('meta').innerHTML =
      `<span class="badge">${data.source_kind}</span>` +
      `<span class="badge">${data.links.length} links</span>` +
      (data.warnings.length ? `<span class="badge" style="background:#fef3c7;color:#92400e">${data.warnings.length} warning(s)</span>` : '');
    document.getElementById('markdown-output').innerHTML = marked.parse(data.markdown);
    result.style.display = 'block';
    status.textContent = '';
  } catch(e) {
    errBox.textContent = e.message;
    errBox.style.display = 'block';
    status.textContent = '';
  } finally {
    btn.disabled = false;
  }
}

document.getElementById('url').addEventListener('keydown', e => { if (e.key === 'Enter') run(); });
</script>
</body>
</html>"""


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/scrape", response_model=ScrapeResponse)
def scrape_endpoint(req: ScrapeRequest) -> ScrapeResponse:
    try:
        result = scrape(
            req.url,
            include_linked_docs=req.include_linked_docs,
            timeout=req.timeout,
        )
    except UnsupportedSourceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ExtractError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ScrapeResponse(**result.to_dict())
