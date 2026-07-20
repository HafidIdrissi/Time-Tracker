"""Local, dependency-free HTML report generation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from html import escape
from pathlib import Path

from .categories import Categorizer
from .database import ActivityDatabase


@dataclass(frozen=True, slots=True)
class ReportPeriod:
    application: str
    window_title: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    is_idle: bool
    category: str
    color: str


def local_midnight(day: date) -> datetime:
    """Create local midnight while respecting the offset for that specific date."""

    return datetime.combine(day, time.min).astimezone()


def format_duration(seconds: float) -> str:
    total_minutes = max(0, round(seconds / 60))
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    if minutes:
        return f"{minutes} min"
    return "< 1 min" if seconds > 0 else "0 min"


def collect_periods(
    database: ActivityDatabase,
    categorizer: Categorizer,
    range_start: datetime,
    range_end: datetime,
) -> list[ReportPeriod]:
    """Load, clip and categorize periods for a report interval."""

    report_periods: list[ReportPeriod] = []
    for period in database.periods_between(range_start, range_end):
        started_at = max(period.started_at, range_start.astimezone(period.started_at.tzinfo))
        ended_at = min(period.ended_at, range_end.astimezone(period.ended_at.tzinfo))
        duration = max(0.0, (ended_at - started_at).total_seconds())
        if duration <= 0:
            continue
        category, color = categorizer.categorize(
            period.application, period.window_title, period.is_idle
        )
        report_periods.append(
            ReportPeriod(
                application="Idle" if period.is_idle else period.application,
                window_title=(
                    "No keyboard or mouse activity"
                    if period.is_idle
                    else period.window_title
                ),
                started_at=started_at.astimezone(),
                ended_at=ended_at.astimezone(),
                duration_seconds=duration,
                is_idle=period.is_idle,
                category=category,
                color=color,
            )
        )
    return report_periods


def _date_range(start_day: date, end_day: date) -> list[date]:
    count = (end_day - start_day).days + 1
    return [start_day + timedelta(days=offset) for offset in range(count)]


def _render_timeline_chart(
    periods: list[ReportPeriod], start_day: date, end_day: date
) -> str:
    rows: list[str] = []
    for day in _date_range(start_day, end_day):
        day_start = local_midnight(day)
        day_end = local_midnight(day + timedelta(days=1))
        day_seconds = (day_end - day_start).total_seconds()
        segments: list[str] = []
        for period in periods:
            segment_start = max(period.started_at, day_start)
            segment_end = min(period.ended_at, day_end)
            if segment_end <= segment_start:
                continue
            left = 100 * (segment_start - day_start).total_seconds() / day_seconds
            width = 100 * (segment_end - segment_start).total_seconds() / day_seconds
            tooltip = escape(
                f"{segment_start:%H:%M}–{segment_end:%H:%M} · "
                f"{period.application} · {period.window_title}",
                quote=True,
            )
            segments.append(
                '<span class="segment" '
                f'style="left:{left:.4f}%;width:max({width:.4f}%, 2px);'
                f'background:{escape(period.color, quote=True)}" title="{tooltip}"></span>'
            )
        rows.append(
            '<div class="day-row">'
            f'<div class="day-label">{day:%d/%m}</div>'
            '<div class="day-track">'
            + "".join(segments)
            + "</div></div>"
        )
    return "".join(rows)


def _table_rows(rows: list[tuple[str, str, float]], empty_columns: int = 3) -> str:
    if not rows:
        return f'<tr><td colspan="{empty_columns}" class="empty">No activity</td></tr>'
    return "".join(
        "<tr>"
        f"<td>{escape(first)}</td><td>{escape(second)}</td>"
        f"<td class=\"duration\">{format_duration(duration)}</td>"
        "</tr>"
        for first, second, duration in rows
    )


def render_html(
    periods: list[ReportPeriod], start_day: date, end_day: date
) -> str:
    """Render a standalone HTML document with no external assets."""

    active_periods = [period for period in periods if not period.is_idle]
    active_seconds = sum(period.duration_seconds for period in active_periods)
    idle_seconds = sum(period.duration_seconds for period in periods if period.is_idle)

    category_totals: dict[tuple[str, str], float] = defaultdict(float)
    application_totals: dict[str, float] = defaultdict(float)
    title_totals: dict[tuple[str, str], float] = defaultdict(float)
    for period in active_periods:
        category_totals[(period.category, period.color)] += period.duration_seconds
        application_totals[period.application] += period.duration_seconds
        title_totals[(period.application, period.window_title)] += period.duration_seconds

    sorted_categories = sorted(category_totals.items(), key=lambda item: -item[1])
    category_cards = "".join(
        '<div class="category-card">'
        f'<span class="dot" style="background:{escape(color, quote=True)}"></span>'
        f'<span>{escape(name)}</span><strong>{format_duration(seconds)}</strong></div>'
        for (name, color), seconds in sorted_categories
    ) or '<p class="empty">No activity during this period.</p>'

    application_rows = [
        (
            application,
            f"{(100 * seconds / active_seconds):.0f} %" if active_seconds else "0 %",
            seconds,
        )
        for application, seconds in sorted(
            application_totals.items(), key=lambda item: -item[1]
        )
    ]
    title_rows = [
        (application, title, seconds)
        for (application, title), seconds in sorted(
            title_totals.items(), key=lambda item: -item[1]
        )
    ]
    timeline_rows = "".join(
        "<tr>"
        f"<td>{period.started_at:%d/%m %H:%M:%S}</td>"
        f"<td>{period.ended_at:%d/%m %H:%M:%S}</td>"
        f"<td><span class=\"tag\" style=\"--tag:{escape(period.color, quote=True)}\">"
        f"{escape(period.category)}</span></td>"
        f"<td>{escape(period.application)}</td>"
        f"<td class=\"window-title\" title=\"{escape(period.window_title, quote=True)}\">"
        f"{escape(period.window_title)}</td>"
        f"<td class=\"duration\">{format_duration(period.duration_seconds)}</td>"
        "</tr>"
        for period in periods
    ) or '<tr><td colspan="6" class="empty">No activity</td></tr>'

    period_label = (
        f"{start_day:%Y-%m-%d}"
        if start_day == end_day
        else f"from {start_day:%Y-%m-%d} to {end_day:%Y-%m-%d}"
    )
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d at %H:%M")
    timeline_chart = _render_timeline_chart(periods, start_day, end_day)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Activity Report — {escape(period_label)}</title>
  <style>
    :root {{ color-scheme: light; --ink:#162033; --muted:#64748b; --line:#e2e8f0;
      --paper:#ffffff; --wash:#f1f5f9; --accent:#4f46e5; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--wash); color:var(--ink); font:14px/1.5 Inter,Segoe UI,Arial,sans-serif; }}
    main {{ width:min(1180px, calc(100% - 32px)); margin:32px auto 56px; }}
    header {{ display:flex; justify-content:space-between; gap:24px; align-items:end; margin-bottom:24px; }}
    h1 {{ margin:0; font-size:30px; letter-spacing:-.03em; }}
    h2 {{ margin:0 0 16px; font-size:18px; }}
    .eyebrow {{ color:var(--accent); text-transform:uppercase; font-weight:700; letter-spacing:.12em; font-size:11px; }}
    .muted {{ color:var(--muted); }}
    .cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:16px; }}
    .card,.panel {{ background:var(--paper); border:1px solid var(--line); border-radius:14px; box-shadow:0 1px 2px #0f172a0a; }}
    .card {{ padding:20px; }} .card strong {{ display:block; font-size:27px; margin-top:5px; }}
    .panel {{ padding:22px; margin-bottom:16px; overflow:hidden; }}
    .categories {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; }}
    .category-card {{ display:grid; grid-template-columns:auto 1fr auto; align-items:center; gap:9px; padding:12px; border:1px solid var(--line); border-radius:10px; }}
    .dot {{ width:10px; height:10px; border-radius:50%; }}
    .day-row {{ display:grid; grid-template-columns:52px 1fr; gap:10px; align-items:center; margin:12px 0; }}
    .day-label {{ color:var(--muted); font-variant-numeric:tabular-nums; }}
    .day-track {{ position:relative; height:28px; overflow:hidden; border-radius:7px;
      background:repeating-linear-gradient(90deg,#f8fafc 0,#f8fafc calc(25% - 1px),#dbe3ed calc(25% - 1px),#dbe3ed 25%); }}
    .segment {{ position:absolute; top:3px; bottom:3px; border-radius:4px; opacity:.92; min-width:2px; }}
    .axis {{ display:grid; grid-template-columns:52px 1fr; gap:10px; color:var(--muted); font-size:11px; }}
    .ticks {{ display:flex; justify-content:space-between; }}
    .grid {{ display:grid; grid-template-columns:1fr 2fr; gap:16px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th {{ color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.06em; text-align:left; }}
    th,td {{ padding:11px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
    tbody tr:last-child td {{ border-bottom:0; }}
    .duration {{ white-space:nowrap; text-align:right; font-variant-numeric:tabular-nums; }}
    .window-title {{ max-width:400px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .tag {{ display:inline-block; border-radius:999px; padding:2px 8px; background:color-mix(in srgb,var(--tag) 14%,white); color:var(--tag); border:1px solid color-mix(in srgb,var(--tag) 30%,white); font-size:12px; font-weight:600; }}
    .empty {{ color:var(--muted); text-align:center; padding:20px; }}
    footer {{ color:var(--muted); text-align:center; margin-top:20px; font-size:12px; }}
    @media (max-width:760px) {{ .cards,.grid {{ grid-template-columns:1fr; }} header {{ align-items:start; flex-direction:column; }} .timeline-table {{ overflow:auto; }} }}
    @media print {{ body {{ background:white; }} main {{ width:100%; margin:0; }} .panel,.card {{ break-inside:avoid; box-shadow:none; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div><div class="eyebrow">Local Time Tracker</div><h1>Activity Report</h1><div class="muted">{escape(period_label)}</div></div>
    <div class="muted">Generated locally on {generated_at}</div>
  </header>
  <section class="cards">
    <div class="card"><span class="muted">Active time</span><strong>{format_duration(active_seconds)}</strong></div>
    <div class="card"><span class="muted">Idle time detected</span><strong>{format_duration(idle_seconds)}</strong></div>
    <div class="card"><span class="muted">Applications used</span><strong>{len(application_totals)}</strong></div>
  </section>
  <section class="panel"><h2>Totals by category</h2><div class="categories">{category_cards}</div></section>
  <section class="panel">
    <h2>Timeline overview</h2>
    <div class="axis"><span></span><div class="ticks"><span>00 h</span><span>06 h</span><span>12 h</span><span>18 h</span><span>24 h</span></div></div>
    {timeline_chart}
  </section>
  <div class="grid">
    <section class="panel"><h2>Applications</h2><table><thead><tr><th>Application</th><th>Share</th><th class="duration">Duration</th></tr></thead><tbody>{_table_rows(application_rows)}</tbody></table></section>
    <section class="panel"><h2>Window titles</h2><table><thead><tr><th>Application</th><th>Full title</th><th class="duration">Duration</th></tr></thead><tbody>{_table_rows(title_rows)}</tbody></table></section>
  </div>
  <section class="panel timeline-table"><h2>Detailed timeline</h2><table>
    <thead><tr><th>Start</th><th>End</th><th>Category</th><th>Application</th><th>Window</th><th class="duration">Duration</th></tr></thead>
    <tbody>{timeline_rows}</tbody></table></section>
  <footer>Data stored on this computer · Standalone report, no internet connection required</footer>
</main>
</body>
</html>"""


def generate_report(
    database_path: str | Path,
    output_path: str | Path,
    start_day: date,
    end_day: date,
    categorizer: Categorizer,
) -> Path:
    """Generate a report file and return its resolved path."""

    range_start = local_midnight(start_day)
    range_end = local_midnight(end_day + timedelta(days=1))
    with ActivityDatabase(database_path) as database:
        periods = collect_periods(database, categorizer, range_start, range_end)
    html = render_html(periods, start_day, end_day)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
    return destination.resolve()
