#!/usr/bin/env python
"""Preview the category chosen for one synthetic application and title."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from timetracker import __version__
from timetracker.categories import CategoryConfigError, load_categorizer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Show which local category matches a synthetic application and title."
    )
    parser.add_argument("--config", type=Path, required=True, help="Category configuration JSON")
    parser.add_argument("--application", required=True, help="Synthetic executable name")
    parser.add_argument("--title", default="", help="Synthetic window title")
    parser.add_argument(
        "--idle",
        action="store_true",
        help="Preview the idle category instead of keyword matching",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        categorizer = load_categorizer(args.config)
    except CategoryConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    name, _color = categorizer.categorize(args.application, args.title, args.idle)
    print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
