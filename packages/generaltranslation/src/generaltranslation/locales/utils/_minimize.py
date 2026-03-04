"""Minimize BCP 47 locale tags using CLDR likely-subtags.

Babel provides no built-in ``minimize()`` (JS has
``Intl.Locale.minimize()``).  This module implements it using the CLDR
``likely_subtags`` table shipped with Babel.

Algorithm
---------
Find the shortest tag (language, language-script, or
language-territory) whose maximized form equals the fully maximized
input.  This is the inverse of maximize.

Examples
--------
>>> minimize_locale("en-US")
'en'
>>> minimize_locale("en-GB")
'en-GB'
>>> minimize_locale("zh-Hans-CN")
'zh'
>>> minimize_locale("zh-Hant-TW")
'zh-Hant'
"""

from __future__ import annotations

import logging

from babel import Locale
from babel.core import get_global

logger = logging.getLogger(__name__)

# CLDR likely-subtags table: maps partial locale tags to their most
# likely fully-qualified form.
# e.g. "en" → "en_Latn_US", "zh_Hant" → "zh_Hant_TW"
_likely_subtags: dict[str, str] = get_global("likely_subtags")


def _parse_locale(
    locale: str,
) -> tuple[str, str | None, str | None]:
    """Parse a BCP 47 tag into (language, script, territory).

    Accepts both hyphen-separated (BCP 47) and underscore-separated
    (CLDR/Babel) formats.
    """
    parsed = Locale.parse(locale, sep="-" if "-" in locale else "_")
    return parsed.language, parsed.script, parsed.territory


def _lookup_likely(
    lang: str,
    script: str | None = None,
    terr: str | None = None,
) -> tuple[str, str | None, str | None]:
    """Find the most likely fully-qualified subtags from CLDR.

    Tries progressively broader keys until a match is found:
    ``lang_script_terr`` -> ``lang_script`` -> ``lang_terr`` -> ``lang``.
    """
    candidates: list[str] = []
    if script and terr:
        candidates.append(f"{lang}_{script}_{terr}")
    if script:
        candidates.append(f"{lang}_{script}")
    if terr:
        candidates.append(f"{lang}_{terr}")
    candidates.append(lang)

    for key in candidates:
        if key in _likely_subtags:
            parts = _likely_subtags[key].split("_")
            return (
                parts[0],
                parts[1] if len(parts) > 1 else None,
                parts[2] if len(parts) > 2 else None,
            )
    return lang, script, terr


def _maximize(
    lang: str,
    script: str | None,
    terr: str | None,
) -> tuple[str, str | None, str | None]:
    """Maximize parsed components, preserving original values."""
    _, likely_script, likely_terr = _lookup_likely(lang, script, terr)
    return (lang, script or likely_script, terr or likely_terr)


def minimize_locale(locale: str) -> str:
    """Remove likely subtags to produce the shortest equivalent tag.

    Finds the shortest tag (language-only, language-script, or
    language-territory) whose maximized form equals the fully
    maximized input.

    This mirrors ``Intl.Locale.prototype.minimize()`` in JavaScript.

    Args:
        locale: A BCP 47 locale tag (e.g. ``"en-US"``,
            ``"zh-Hans-CN"``).

    Returns:
        The minimized tag with hyphens (e.g. ``"en"``, ``"zh"``).
        Returns the original string on parse failure.

    Examples:
        >>> minimize_locale("en-US")
        'en'
        >>> minimize_locale("en-GB")
        'en-GB'
        >>> minimize_locale("de-AT")
        'de-AT'
        >>> minimize_locale("zh-Hans-CN")
        'zh'
        >>> minimize_locale("zh-Hant-TW")
        'zh-Hant'
    """
    try:
        lang, script, terr = _parse_locale(locale)
        full = _maximize(lang, script, terr)

        # Try language only
        if _maximize(lang, None, None) == full:
            return lang

        # Try language + script
        if script and _maximize(lang, script, None) == full:
            return f"{lang}-{script}"

        # Try language + territory
        if terr and _maximize(lang, None, terr) == full:
            return f"{lang}-{terr}"

        # Cannot reduce — return all original parts
        parts = [lang]
        if script:
            parts.append(script)
        if terr:
            parts.append(terr)
        return "-".join(parts)
    except Exception:
        logger.debug("Failed to minimize locale '%s'", locale)
        return locale
