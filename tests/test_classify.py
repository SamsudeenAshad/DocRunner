from docrunner.classify import detect_source, kind_from_content_type
from docrunner.models import SourceKind


def test_detect_webpage():
    assert detect_source("https://example.com/article") == SourceKind.WEBPAGE


def test_detect_gdocs():
    url = "https://docs.google.com/document/d/1AbCdEfGhIjK/edit"
    assert detect_source(url) == SourceKind.GDOCS


def test_detect_gdrive_file():
    url = "https://drive.google.com/file/d/1AbCdEfGhIjK/view"
    assert detect_source(url) == SourceKind.GDRIVE_FILE


def test_detect_pdf_by_extension():
    assert detect_source("https://example.com/report.pdf") == SourceKind.PDF


def test_detect_docx_by_extension():
    assert detect_source("https://example.com/spec.docx") == SourceKind.DOCX


def test_detect_unknown_without_scheme():
    assert detect_source("not a url") == SourceKind.UNKNOWN


def test_content_type_overrides():
    assert kind_from_content_type("application/pdf") == SourceKind.PDF
    assert kind_from_content_type("text/html; charset=utf-8") == SourceKind.WEBPAGE
    assert kind_from_content_type("application/octet-stream") is None
