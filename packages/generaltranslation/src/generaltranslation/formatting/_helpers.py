"""Shared helpers for the formatting module.

Provides locale resolution and option mapping utilities used by
multiple formatting functions.
"""

from __future__ import annotations

from babel import Locale
from babel.core import UnknownLocaleError

from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE


def _resolve_babel_locale(locales: str | list[str] | None = None) -> Locale:
    """Convert BCP 47 locale(s) to a Babel :class:`Locale` instance.

    Tries each candidate in order and falls back to ``en`` if none parse.

    Args:
        locales: A single BCP 47 tag, a list of tags, or ``None``.

    Returns:
        A :class:`babel.Locale` instance.
    """
    if locales is None:
        return Locale(LIBRARY_DEFAULT_LOCALE)
    if isinstance(locales, str):
        locales = [locales]
    for tag in locales:
        try:
            return Locale.parse(tag, sep="-")
        except (UnknownLocaleError, ValueError):
            continue
    return Locale(LIBRARY_DEFAULT_LOCALE)


def _get_language_code(locales: str | list[str] | None = None) -> str:
    """Extract the language code from a locale specification.

    Args:
        locales: A single BCP 47 tag, a list of tags, or ``None``.

    Returns:
        A 2- or 3-letter language code string.
    """
    return _resolve_babel_locale(locales).language
