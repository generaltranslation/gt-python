"""Number formatting using Babel.

Ports ``_formatNum`` from the JS core library.
"""

from __future__ import annotations

from babel.numbers import format_compact_decimal, format_decimal, format_percent

from generaltranslation.formatting._helpers import _resolve_babel_locale


def format_num(
    value: int | float,
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> str:
    """Format a number according to the given locale and options.

    Args:
        value: The number to format.
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options (snake_case).

            - ``style``: ``"decimal"`` (default), ``"percent"``.
            - ``notation``: ``"standard"`` (default), ``"compact"``.
            - ``use_grouping``: Whether to use grouping separators (default ``True``).
            - ``minimum_fraction_digits``: Minimum number of fraction digits.
            - ``maximum_fraction_digits``: Maximum number of fraction digits.
            - ``minimum_integer_digits``: Minimum number of integer digits.

    Returns:
        The formatted number string.
    """
    if options is None:
        options = {}

    locale = _resolve_babel_locale(locales)
    style = options.get("style", "decimal")
    notation = options.get("notation", "standard")

    # Compact notation
    if notation == "compact":
        try:
            result = format_compact_decimal(value, locale=locale)
            return str(result)
        except Exception:
            pass

    # Percent style
    if style == "percent":
        fmt = _build_format_string(options)
        return format_percent(value, format=fmt or None, locale=locale)

    # Default: decimal
    fmt = _build_format_string(options)
    use_grouping = options.get("use_grouping", True)
    return format_decimal(
        value,
        format=fmt or None,
        locale=locale,
        group_separator=use_grouping,
    )


def _build_format_string(options: dict) -> str | None:
    """Build a Babel number format pattern string from options.

    Maps ``minimum_fraction_digits``, ``maximum_fraction_digits``, and
    ``minimum_integer_digits`` to a Babel-compatible format pattern.

    Returns:
        A pattern string like ``"#,##0.00"`` or ``None`` to use defaults.
    """
    min_frac = options.get("minimum_fraction_digits")
    max_frac = options.get("maximum_fraction_digits")
    min_int = options.get("minimum_integer_digits")

    if min_frac is None and max_frac is None and min_int is None:
        return None

    # Integer part
    int_digits = min_int or 1
    if options.get("use_grouping", True):
        # Build grouped pattern: e.g. #,##0, #,##00
        if int_digits <= 1:
            int_part = "#,##0"
        else:
            int_part = "#,##" + "0" * int_digits
    else:
        int_part = "0" * int_digits

    # Fraction part
    if min_frac is not None or max_frac is not None:
        required = min_frac or 0
        optional = (max_frac or required) - required
        frac_part = "0" * required + "#" * optional
        return f"{int_part}.{frac_part}" if frac_part else int_part

    return int_part
