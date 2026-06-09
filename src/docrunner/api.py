"""FastAPI wrapper exposing DocRunner over HTTP.

Run with: ``uvicorn docrunner.api:app --reload``
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
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
