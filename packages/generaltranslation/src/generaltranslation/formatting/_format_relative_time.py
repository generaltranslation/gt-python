"""Relative time formatting using Babel.

Ports ``_formatRelativeTime`` from the JS core library.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from babel.dates import format_timedelta

from generaltranslation.formatting._helpers import _resolve_babel_locale

# Map JS RelativeTimeFormat units to timedelta kwargs
_UNIT_TO_TIMEDELTA: dict[str, str] = {
    "second": "seconds",
    "seconds": "seconds",
    "minute": "minutes",
    "minutes": "minutes",
    "hour": "hours",
    "hours": "hours",
    "day": "days",
    "days": "days",
    "week": "weeks",
    "weeks": "weeks",
    "month": "days",  # approximate: 30 days per month
    "months": "days",
    "year": "days",  # approximate: 365 days per year
    "years": "days",
    "quarter": "days",  # approximate: 91 days per quarter
    "quarters": "days",
}

# Multipliers for units that need conversion to days
_UNIT_MULTIPLIER: dict[str, int] = {
    "month": 30,
    "months": 30,
    "year": 365,
    "years": 365,
    "quarter": 91,
    "quarters": 91,
}

# Map JS style names to Babel granularity
_STYLE_MAP: dict[str, str] = {
    "long": "long",
    "short": "short",
    "narrow": "narrow",
}


def format_relative_time(
    value: int | float,
    unit: str,
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> str:
    """Format a relative time value (e.g. "3 days ago", "in 2 hours").

    Args:
        value: The numeric value (positive = future, negative = past).
        unit: The time unit: ``"second"``, ``"minute"``, ``"hour"``,
            ``"day"``, ``"week"``, ``"month"``, ``"quarter"``, ``"year"``.
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options (snake_case).

            - ``style``: ``"long"`` (default), ``"short"``, ``"narrow"``.
            - ``numeric``: ``"auto"`` (default), ``"always"``.

    Returns:
        The formatted relative time string.
    """
    if options is None:
        options = {}

    locale = _resolve_babel_locale(locales)
    style = options.get("style", "long")
    babel_format = _STYLE_MAP.get(style, "long")

    # Build timedelta
    td_key = _UNIT_TO_TIMEDELTA.get(unit, "seconds")
    multiplier = _UNIT_MULTIPLIER.get(unit, 1)
    delta = timedelta(**{td_key: value * multiplier})

    # Use threshold=999 to prevent Babel from auto-rounding units
    # (match JS literal behavior where "5 seconds" stays as seconds)
    return format_timedelta(
        delta,
        granularity=_singular_unit(unit),  # type: ignore[arg-type]
        threshold=999,
        add_direction=True,
        format=babel_format,  # type: ignore[arg-type]
        locale=locale,
    )


def select_relative_time_unit(date: "datetime") -> tuple[int, str]:
    """Select the best unit and compute the value for relative time formatting.

    Mirrors ``_selectRelativeTimeUnit`` from the JS core library.

    Args:
        date: A :class:`~datetime.datetime` (timezone-aware or naive).

    Returns:
        A ``(value, unit)`` tuple where *value* is signed (negative = past)
        and *unit* is one of ``"second"``, ``"minute"``, ``"hour"``,
        ``"day"``, ``"week"``, ``"month"``, ``"year"``.
    """
    now = datetime.now(timezone.utc)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    diff_ms = (date - now).total_seconds() * 1000
    abs_diff_ms = abs(diff_ms)
    sign = -1 if diff_ms < 0 else 1

    seconds = int(abs_diff_ms // 1000)
    minutes = int(abs_diff_ms // (1000 * 60))
    hours = int(abs_diff_ms // (1000 * 60 * 60))
    days = int(abs_diff_ms // (1000 * 60 * 60 * 24))
    weeks = int(abs_diff_ms // (1000 * 60 * 60 * 24 * 7))
    months = int(abs_diff_ms // (1000 * 60 * 60 * 24 * 30))
    years = int(abs_diff_ms // (1000 * 60 * 60 * 24 * 365))

    if seconds < 60:
        return (sign * seconds, "second")
    if minutes < 60:
        return (sign * minutes, "minute")
    if hours < 24:
        return (sign * hours, "hour")
    if days < 7:
        return (sign * days, "day")
    if days < 28:
        return (sign * weeks, "week")
    if months < 12:
        return (sign * months, "month")
    return (sign * years, "year")


def format_relative_time_from_date(
    date: "datetime",
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> str:
    """Format a relative time string from a datetime, auto-selecting the best unit.

    Mirrors ``_formatRelativeTimeFromDate`` from the JS core library.

    Args:
        date: A :class:`~datetime.datetime` (timezone-aware or naive).
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options passed to :func:`format_relative_time`.

    Returns:
        The formatted relative time string (e.g. ``"3 days ago"``).
    """
    value, unit = select_relative_time_unit(date)
    return format_relative_time(value, unit, locales=locales, options=options)


def _singular_unit(unit: str) -> str:
    """Normalize unit to singular form for Babel granularity param."""
    singular_map = {
        "seconds": "second",
        "minutes": "minute",
        "hours": "hour",
        "days": "day",
        "weeks": "week",
        "months": "month",
        "quarters": "quarter",
        "years": "year",
    }
    return singular_map.get(unit, unit)
