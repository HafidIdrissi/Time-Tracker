#!/usr/bin/env python
"""Command-line entry point for the Windows background tracker."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from timetracker.database import ActivityDatabase
from timetracker.tracker import ActivityTracker
from timetracker.windows import WindowsActivityProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record the active Windows window locally."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/activity.db"),
        help="SQLite database (default: data/activity.db)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Sampling interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--idle-after",
        type=float,
        default=180.0,
        help="Idle threshold in seconds (default: 180)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    try:
        provider = WindowsActivityProvider()
        with ActivityDatabase(args.database) as database:
            tracker = ActivityTracker(
                database=database,
                provider=provider,
                poll_interval=args.interval,
                idle_threshold=args.idle_after,
            )
            try:
                tracker.run()
            except KeyboardInterrupt:
                tracker.stop()
    except (RuntimeError, ValueError) as exc:
        logging.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
