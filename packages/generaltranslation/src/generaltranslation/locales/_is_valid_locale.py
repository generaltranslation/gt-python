"""BCP 47 locale validation and standardisation.

Ports ``isValidLocale.ts`` from the JS core library.
Uses the ``babel`` library instead of the browser ``Intl.Locale`` API.
"""

from __future__ import annotations

from babel import Locale
from babel.core import UnknownLocaleError

from generaltranslation.locales._types import CustomMapping

# Scripts that are valid but may not be recognised by all display-name APIs.
SCRIPT_EXCEPTIONS: set[str] = {"Cham", "Jamo", "Kawi", "Lisu", "Toto", "Thai"}


def _is_custom_language(language: str) -> bool:
    """Check if *language* is in the BCP 47 private-use range (qaa-qtz).

    Per BCP 47, codes in this range are reserved for private use and are
    always considered valid.

    Args:
        language: A 2- or 3-letter ISO 639 language code (lowercase).

    Returns:
        ``True`` if the code is in the private-use range.
    """
    lang = language.lower()
    return len(lang) == 3 and lang >= "qaa" and lang <= "qtz"


def is_valid_locale(
    locale: str,
    custom_mapping: CustomMapping | None = None,
) -> bool:
    """Validate a BCP 47 language tag.

    Checks that *locale* can be parsed into valid language, region, and
    script components.  Custom mapping entries whose ``"code"`` key points
    to a valid locale are also accepted.  Private-use language codes
    (``qaa``-``qtz``) are always valid.

    Args:
        locale: The BCP 47 language tag to validate (e.g. ``"en-US"``,
            ``"zh-Hans-CN"``).
        custom_mapping: Optional custom mapping that may redirect
            *locale* to a canonical code before validation.

    Returns:
        ``True`` if the locale is valid, ``False`` otherwise.

    Examples:
        >>> is_valid_locale("en-US")
        True
        >>> is_valid_locale("not-a-locale")
        False
        >>> is_valid_locale("qaa")  # private-use range
        True
    """
    if not locale or not isinstance(locale, str):
        return False

    # Check custom mapping redirect
    if custom_mapping is not None:
        from generaltranslation.locales._custom_locale_mapping import (
            should_use_canonical_locale,
        )

        if should_use_canonical_locale(locale, custom_mapping):
            entry = custom_mapping[locale]
            if isinstance(entry, dict):
                return is_valid_locale(entry["code"])

    # Split using hyphen separator
    sep = "-"
    parts = locale.split(sep)
    if len(parts) > 3:
        return False

    language = parts[0].lower()

    # Private-use range is always valid
    if _is_custom_language(language):
        return True

    try:
        parsed = Locale.parse(locale, sep=sep)
    except (UnknownLocaleError, ValueError):
        return False

    # Validate that parsed components look reasonable
    lang = parsed.language
    if not lang or len(lang) < 2:
        return False

    # Verify Babel didn't silently drop input parts (e.g. "en-FAKE")
    # Babel may ADD parts via likely subtag resolution (zh-CN → zh-Hans-CN)
    # but should never have fewer recognized parts than the input
    parsed_part_count = 1  # language always present
    if parsed.script:
        parsed_part_count += 1
    if parsed.territory:
        parsed_part_count += 1
    if parsed_part_count < len(parts):
        return False

    # For region codes, verify they're known
    if parsed.territory:
        try:
            display_locale = Locale("en")
            if parsed.territory not in display_locale.territories:
                return False
        except Exception:
            pass

    # For script codes, verify they're known (with exceptions)
    if parsed.script:
        if parsed.script not in SCRIPT_EXCEPTIONS:
            try:
                display_locale = Locale("en")
                if parsed.script not in display_locale.scripts:
                    return False
            except Exception:
                pass

    return True


def standardize_locale(locale: str) -> str:
    """Normalise a BCP 47 locale tag to its canonical form.

    Converts underscores to hyphens, fixes casing (e.g. ``"en_us"``
    -> ``"en-US"``), and applies IANA subtag registry canonicalisation.

    Note: Tags containing underscores are returned unchanged (matching
    JS ``Intl.getCanonicalLocales()`` behavior which rejects them).

    Args:
        locale: The locale tag to standardise.

    Returns:
        The canonical form of the locale, or the original string
        unchanged if parsing fails.

    Examples:
        >>> standardize_locale("en_us")
        'en_us'
        >>> standardize_locale("zh-hans-cn")
        'zh-Hans-CN'
    """
    if not locale or not isinstance(locale, str):
        return locale

    # Underscore inputs stay unchanged (matching JS behavior)
    if "_" in locale:
        return locale

    try:
        parsed = Locale.parse(locale, sep="-")
        # Reconstruct with hyphens
        result = parsed.language
        if parsed.script:
            result += f"-{parsed.script}"
        if parsed.territory:
            result += f"-{parsed.territory}"
        return result
    except Exception:
        return locale
