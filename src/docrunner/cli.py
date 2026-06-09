"""Command-line interface for DocRunner."""

from __future__ import annotations

import argparse
import json
import sys

from .core import scrape
from .models import DocRunnerError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="docrunner",
        description="Download a web page or Google Drive/Docs link and "
        "return its content as Markdown.",
    )
    p.add_argument("url", help="Web page URL or public Google Drive/Docs link")
    p.add_argument("-o", "--output", metavar="FILE",
                   help="Write markdown to FILE (default: stdout)")
    p.add_argument("--json", action="store_true",
                   help="Emit the full result (markdown + metadata) as JSON")
    p.add_argument("--include-linked-docs", action="store_true",
                   help="Also fetch PDF/DOCX links found on a web page")
    p.add_argument("--timeout", type=float, default=30.0,
                   help="Per-request timeout in seconds (default: 30)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = scrape(
            args.url,
            include_linked_docs=args.include_linked_docs,
            timeout=args.timeout,
        )
    except DocRunnerError as exc:
        print(f"docrunner: error: {exc}", file=sys.stderr)
        return 1

    output = json.dumps(result.to_dict(), indent=2) if args.json else result.markdown

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output + "\n")
        for w in result.warnings:
            print(f"docrunner: warning: {w}", file=sys.stderr)
        print(f"Wrote {args.output} ({len(result.markdown)} chars)", file=sys.stderr)
    else:
        for w in result.warnings:
            print(f"docrunner: warning: {w}", file=sys.stderr)
        print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
