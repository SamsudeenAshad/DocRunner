from docrunner.fetchers.gdrive import (
    docs_export_url,
    drive_download_url,
    extract_file_id,
)

FID = "1AbCdEfGhIjKlMnOpQ"


def test_extract_id_from_docs_path():
    assert extract_file_id(f"https://docs.google.com/document/d/{FID}/edit") == FID


def test_extract_id_from_file_path():
    assert extract_file_id(f"https://drive.google.com/file/d/{FID}/view") == FID


def test_extract_id_from_query():
    assert extract_file_id(f"https://drive.google.com/uc?id={FID}&export=download") == FID


def test_extract_id_none():
    assert extract_file_id("https://drive.google.com/drive/my-drive") is None


def test_docs_export_url():
    assert docs_export_url(FID, "html") == (
        f"https://docs.google.com/document/d/{FID}/export?format=html"
    )


def test_drive_download_url():
    assert drive_download_url(FID) == (
        f"https://drive.google.com/uc?export=download&id={FID}"
    )
