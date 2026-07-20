#!/usr/bin/env python
"""Generate a local HTML activity report from SQLite."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from timetracker.categories import CategoryConfigError, load_categorizer
from timetracker.reporting import generate_report


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("format attendu : AAAA-MM-JJ") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Génère un rapport HTML local depuis la base d'activité."
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--date", type=parse_date, help="Jour à analyser (AAAA-MM-JJ)")
    selection.add_argument("--from", dest="start_date", type=parse_date, help="Premier jour")
    parser.add_argument("--to", dest="end_date", type=parse_date, help="Dernier jour inclus")
    parser.add_argument("--database", type=Path, default=Path("data/activity.db"))
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.end_date and not args.start_date:
        parser.error("--to doit être utilisé avec --from")

    today = date.today()
    start_day = args.date or args.start_date or today
    end_day = args.date or args.end_date or start_day
    if end_day < start_day:
        parser.error("--to doit être postérieur ou égal à --from")

    config_path = args.config
    if config_path is None:
        config_path = Path("config.json")
        if not config_path.exists():
            config_path = Path("config.example.json")

    suffix = start_day.isoformat()
    if end_day != start_day:
        suffix += f"_{end_day.isoformat()}"
    output_path = args.output or Path(f"reports/report-{suffix}.html")

    try:
        categorizer = load_categorizer(config_path)
        result = generate_report(
            database_path=args.database,
            output_path=output_path,
            start_day=start_day,
            end_day=end_day,
            categorizer=categorizer,
        )
    except (CategoryConfigError, OSError) as exc:
        parser.exit(1, f"Erreur : {exc}\n")

    print(f"Rapport généré : {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
