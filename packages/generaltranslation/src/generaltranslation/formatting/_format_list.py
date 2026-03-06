"""List formatting using Babel.

Ports ``_formatList`` and ``_formatListToParts`` from the JS core library.
"""

from __future__ import annotations

from typing import Any, TypeVar

from babel.lists import format_list as babel_format_list

from generaltranslation.formatting._helpers import _resolve_babel_locale

T = TypeVar("T")

# Map JS ListFormat {type, style} to Babel style parameter.
# Babel 2.18+ supports: "standard", "standard-short", "standard-narrow",
# "or", "or-short", "or-narrow", "unit", "unit-short", "unit-narrow"
_STYLE_MAP: dict[tuple[str, str], str] = {
    ("conjunction", "long"): "standard",
    ("conjunction", "short"): "standard-short",
    ("conjunction", "narrow"): "standard-narrow",
    ("disjunction", "long"): "or",
    ("disjunction", "short"): "or-short",
    ("disjunction", "narrow"): "or-narrow",
    ("unit", "long"): "unit",
    ("unit", "short"): "unit-short",
    ("unit", "narrow"): "unit-narrow",
}


def format_list(
    value: list[Any],
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> str:
    """Format a list of items according to the given locale and options.

    Args:
        value: The list of items to format. Items are converted to strings.
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options (snake_case).

            - ``type``: ``"conjunction"`` (default), ``"disjunction"``, ``"unit"``.
            - ``style``: ``"long"`` (default), ``"short"``, ``"narrow"``.

    Returns:
        The formatted list string.
    """
    if options is None:
        options = {}

    locale = _resolve_babel_locale(locales)
    list_type = options.get("type", "conjunction")
    list_style = options.get("style", "long")

    babel_style = _STYLE_MAP.get((list_type, list_style), "standard")

    str_items = [str(item) for item in value]
    return babel_format_list(str_items, style=babel_style, locale=locale)  # type: ignore[arg-type]


def format_list_to_parts(
    value: list[T],
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> list[T | str]:
    """Format a list and return interleaved parts with separators.

    Uses placeholder-based splitting to extract separators from Babel's
    formatted output, then interleaves them with the original typed values.

    This mirrors the JS ``_formatListToParts`` which uses
    ``Intl.ListFormat.formatToParts()``.

    Args:
        value: The list of items to format.
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options (same as :func:`format_list`).

    Returns:
        A list alternating between original values and separator strings.
    """
    if not value:
        return []
    if len(value) == 1:
        return list(value)

    if options is None:
        options = {}

    locale = _resolve_babel_locale(locales)
    list_type = options.get("type", "conjunction")
    list_style = options.get("style", "long")
    babel_style = _STYLE_MAP.get((list_type, list_style), "standard")

    # Use unique placeholders to identify element positions
    placeholder = "\x00"
    placeholders = [f"{placeholder}{i}{placeholder}" for i in range(len(value))]
    formatted = babel_format_list(placeholders, style=babel_style, locale=locale)  # type: ignore[arg-type]

    # Split by placeholders to extract separators
    parts: list[T | str] = []
    remaining = formatted
    for i, val in enumerate(value):
        ph = f"{placeholder}{i}{placeholder}"
        idx = remaining.find(ph)
        if idx > 0:
            # There's a separator before this element
            parts.append(remaining[:idx])
        parts.append(val)
        remaining = remaining[idx + len(ph) :]

    # Any trailing text after the last placeholder
    if remaining:
        parts.append(remaining)

    return parts
