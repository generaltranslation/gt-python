"""Relative time formatting using Babel.

Ports ``_formatRelativeTime`` from the JS core library.
"""

from __future__ import annotations

from datetime import timedelta

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
    "month": "days",     # approximate: 30 days per month
    "months": "days",
    "year": "days",      # approximate: 365 days per year
    "years": "days",
    "quarter": "days",   # approximate: 91 days per quarter
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
        granularity=_singular_unit(unit),
        threshold=999,
        add_direction=True,
        format=babel_format,
        locale=locale,
    )


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
