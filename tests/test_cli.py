import docrunner.cli as cli_mod
from docrunner.models import ScrapeResult, SourceKind, FetchError


def _fake_result():
    return ScrapeResult(
        markdown="# Hello\n\nbody",
        title="Hello",
        source_url="https://example.com",
        source_kind=SourceKind.WEBPAGE,
        links=[],
        warnings=[],
    )


def test_cli_stdout(monkeypatch, capsys):
    monkeypatch.setattr(cli_mod, "scrape", lambda *a, **k: _fake_result())
    rc = cli_mod.main(["https://example.com"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "# Hello" in out


def test_cli_writes_file(monkeypatch, tmp_path):
    monkeypatch.setattr(cli_mod, "scrape", lambda *a, **k: _fake_result())
    target = tmp_path / "out.md"
    rc = cli_mod.main(["https://example.com", "-o", str(target)])
    assert rc == 0
    assert "# Hello" in target.read_text()


def test_cli_error_exit_code(monkeypatch, capsys):
    def boom(*a, **k):
        raise FetchError("boom")

    monkeypatch.setattr(cli_mod, "scrape", boom)
    rc = cli_mod.main(["https://example.com"])
    assert rc == 1
    assert "error" in capsys.readouterr().err
