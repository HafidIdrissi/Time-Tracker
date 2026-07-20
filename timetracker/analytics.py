"""Usage analytics shared by the graphical dashboard."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .reporting import ReportPeriod, local_midnight


BROWSER_APPLICATIONS = {
    "brave.exe",
    "chrome.exe",
    "firefox.exe",
    "msedge.exe",
    "opera.exe",
    "opera_gx.exe",
    "vivaldi.exe",
}

BROWSER_SUFFIXES = (
    " - Google Chrome",
    " – Google Chrome",
    " — Google Chrome",
    " - Mozilla Firefox",
    " – Mozilla Firefox",
    " — Mozilla Firefox",
    " - Microsoft Edge",
    " – Microsoft Edge",
    " — Microsoft Edge",
    " - Brave",
    " – Brave",
    " — Brave",
    " - Opera",
    " – Opera",
    " — Opera",
    " - Vivaldi",
    " – Vivaldi",
    " — Vivaldi",
)


@dataclass(frozen=True, slots=True)
class UsageBucket:
    label: str
    categories: tuple[tuple[str, str, float], ...]

    @property
    def total_seconds(self) -> float:
        return sum(seconds for _name, _color, seconds in self.categories)


@dataclass(frozen=True, slots=True)
class UsageAnalytics:
    active_seconds: float
    idle_seconds: float
    average_daily_seconds: float
    longest_session_seconds: float
    categories: tuple[tuple[str, str, float], ...]
    applications: tuple[tuple[str, float], ...]
    browser_tabs: tuple[tuple[str, str, float], ...]
    buckets: tuple[UsageBucket, ...]


def browser_tab_title(application: str, window_title: str) -> str | None:
    """Return a cleaned browser tab title, or ``None`` for non-browsers."""

    if application.casefold() not in BROWSER_APPLICATIONS:
        return None
    title = window_title.strip()
    for suffix in BROWSER_SUFFIXES:
        if title.casefold().endswith(suffix.casefold()):
            title = title[: -len(suffix)].strip()
            break
    return title or "(Onglet sans titre)"


def _longest_active_session(periods: list[ReportPeriod]) -> float:
    """Measure uninterrupted active usage, allowing normal polling-sized gaps."""

    longest = 0.0
    session_start: datetime | None = None
    session_end: datetime | None = None

    def finish_session() -> None:
        nonlocal longest, session_start, session_end
        if session_start is not None and session_end is not None:
            longest = max(longest, (session_end - session_start).total_seconds())
        session_start = None
        session_end = None

    for period in sorted(periods, key=lambda item: item.started_at):
        if period.is_idle:
            finish_session()
            continue
        if session_end is None or (period.started_at - session_end).total_seconds() > 30:
            finish_session()
            session_start = period.started_at
            session_end = period.ended_at
        else:
            session_end = max(session_end, period.ended_at)
    finish_session()
    return longest


def _bucket_boundaries(
    start_day: date, end_day: date
) -> list[tuple[str, datetime, datetime]]:
    if start_day == end_day:
        day_start = local_midnight(start_day)
        return [
            (
                f"{hour:02d} h",
                day_start + timedelta(hours=hour),
                day_start + timedelta(hours=hour + 1),
            )
            for hour in range(24)
        ]

    day_count = (end_day - start_day).days + 1
    boundaries: list[tuple[str, datetime, datetime]] = []
    for offset in range(day_count):
        day = start_day + timedelta(days=offset)
        boundaries.append(
            (
                day.strftime("%a %d").capitalize(),
                local_midnight(day),
                local_midnight(day + timedelta(days=1)),
            )
        )
    return boundaries


def _usage_buckets(
    periods: list[ReportPeriod], start_day: date, end_day: date
) -> tuple[UsageBucket, ...]:
    buckets: list[UsageBucket] = []
    active_periods = [period for period in periods if not period.is_idle]
    for label, bucket_start, bucket_end in _bucket_boundaries(start_day, end_day):
        totals: dict[tuple[str, str], float] = defaultdict(float)
        for period in active_periods:
            start = max(period.started_at, bucket_start)
            end = min(period.ended_at, bucket_end)
            if end > start:
                totals[(period.category, period.color)] += (end - start).total_seconds()
        categories = tuple(
            (name, color, seconds)
            for (name, color), seconds in sorted(
                totals.items(), key=lambda item: -item[1]
            )
        )
        buckets.append(UsageBucket(label=label, categories=categories))
    return tuple(buckets)


def analyze_usage(
    periods: list[ReportPeriod], start_day: date, end_day: date
) -> UsageAnalytics:
    """Aggregate report periods into Screen Time-style usage statistics."""

    active_periods = [period for period in periods if not period.is_idle]
    active_seconds = sum(period.duration_seconds for period in active_periods)
    idle_seconds = sum(
        period.duration_seconds for period in periods if period.is_idle
    )
    category_totals: dict[tuple[str, str], float] = defaultdict(float)
    application_totals: dict[str, float] = defaultdict(float)
    tab_totals: dict[tuple[str, str], float] = defaultdict(float)

    for period in active_periods:
        category_totals[(period.category, period.color)] += period.duration_seconds
        application_totals[period.application] += period.duration_seconds
        tab_title = browser_tab_title(period.application, period.window_title)
        if tab_title is not None:
            tab_totals[(period.application, tab_title)] += period.duration_seconds

    categories = tuple(
        (name, color, seconds)
        for (name, color), seconds in sorted(
            category_totals.items(), key=lambda item: -item[1]
        )
    )
    applications = tuple(
        sorted(application_totals.items(), key=lambda item: -item[1])
    )
    browser_tabs = tuple(
        (application, title, seconds)
        for (application, title), seconds in sorted(
            tab_totals.items(), key=lambda item: -item[1]
        )
    )
    day_count = max(1, (end_day - start_day).days + 1)
    return UsageAnalytics(
        active_seconds=active_seconds,
        idle_seconds=idle_seconds,
        average_daily_seconds=active_seconds / day_count,
        longest_session_seconds=_longest_active_session(periods),
        categories=categories,
        applications=applications,
        browser_tabs=browser_tabs,
        buckets=_usage_buckets(periods, start_day, end_day),
    )
