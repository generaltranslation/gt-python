"""Text direction lookup for BCP 47 locales.

Ports ``getLocaleDirection.ts`` from the JS core library.
Uses ``langcodes`` script metadata to determine whether a locale's
writing system is left-to-right or right-to-left.
"""

from __future__ import annotations

from babel import Locale


def get_locale_direction(locale: str) -> str:
    """Return the text direction for *locale*.

    Determines whether the script used by *locale* is written
    left-to-right or right-to-left.  Uses ``langcodes`` to resolve the
    likely script and checks it against a known set of RTL scripts
    (Arabic, Hebrew, Thaana, Syriac, etc.).

    Args:
        locale: A BCP 47 locale tag (e.g. ``"ar"``, ``"en-US"``).

    Returns:
        ``"rtl"`` if the locale uses a right-to-left script, otherwise
        ``"ltr"``.  Defaults to ``"ltr"`` if the locale cannot be parsed.

    Examples:
        >>> get_locale_direction("ar")
        'rtl'
        >>> get_locale_direction("en-US")
        'ltr'
        >>> get_locale_direction("he")
        'rtl'
    """
    try:
        parsed = Locale.parse(locale, sep="-")
        return parsed.text_direction
    except Exception:
        return "ltr"
