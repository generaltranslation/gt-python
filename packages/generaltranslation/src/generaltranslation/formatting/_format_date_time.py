"""Date/time formatting using Babel.

Ports ``_formatDateTime`` from the JS core library.
"""

from __future__ import annotations

from datetime import datetime

from babel.dates import format_date, format_datetime, format_time

from generaltranslation.formatting._helpers import _resolve_babel_locale


def format_date_time(
    value: datetime | str,
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> str:
    """Format a date/time value according to the given locale and options.

    Args:
        value: A :class:`datetime` object or an ISO 8601 string.
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options (snake_case).

            - ``date_style``: ``"full"``, ``"long"``, ``"medium"``, ``"short"``.
            - ``time_style``: ``"full"``, ``"long"``, ``"medium"``, ``"short"``.

            If both are provided, ``format_datetime`` is used.
            If only ``date_style``, ``format_date`` is used.
            If only ``time_style``, ``format_time`` is used.
            If neither, ``format_datetime`` with ``"medium"`` is used.

    Returns:
        The formatted date/time string.
    """
    if options is None:
        options = {}

    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    locale = _resolve_babel_locale(locales)
    date_style = options.get("date_style")
    time_style = options.get("time_style")

    if date_style and time_style:
        return (
            format_datetime(value, format=date_style, locale=locale)
            + " "
            + format_time(value, format=time_style, locale=locale)
        )

    if date_style:
        return format_date(value, format=date_style, locale=locale)

    if time_style:
        return format_time(value, format=time_style, locale=locale)

    # Default: medium datetime
    return format_datetime(value, format="medium", locale=locale)
