"""Get the human-readable display name for a BCP 47 locale.

Ports ``getLocaleName.ts`` from the JS core library.
Uses ``babel`` display-name methods instead of ``Intl.DisplayNames``.
"""

from __future__ import annotations

from babel import Locale

from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE
from generaltranslation.locales._types import CustomMapping


def get_locale_name(
    locale: str,
    default_locale: str | None = LIBRARY_DEFAULT_LOCALE,
    custom_mapping: CustomMapping | None = None,
) -> str:
    """Return the display name of *locale* rendered in *default_locale*.

    Resolution order:

    1. Check *custom_mapping* for a ``"name"`` override (trying the
       aliased code, standardised code, and base language code in turn).
    2. Use ``babel`` to produce a display name in *default_locale*.
    3. Fall back to an empty string if all lookups fail.

    Args:
        locale: A BCP 47 locale tag (e.g. ``"de"``, ``"zh-Hans-CN"``).
        default_locale: The language in which the name should be
            rendered (defaults to ``"en"``).
        custom_mapping: Optional custom mapping that may override the
            display name or redirect to a canonical code.

    Returns:
        The localised display name, or ``""`` on failure.

    Examples:
        >>> get_locale_name("de")
        'German'
        >>> get_locale_name("de", default_locale="fr")
        'allemand'
    """
    from generaltranslation.locales._custom_locale_mapping import (
        get_custom_property,
        should_use_canonical_locale,
    )
    from generaltranslation.locales._is_valid_locale import standardize_locale

    if not locale:
        return ""

    # Check custom mapping
    if custom_mapping is not None:
        # Try locale as-is
        custom_name = get_custom_property(custom_mapping, locale, "name")
        if custom_name:
            return custom_name

        # If it redirects to canonical, resolve
        if should_use_canonical_locale(locale, custom_mapping):
            entry = custom_mapping[locale]
            if isinstance(entry, dict):
                canonical = entry["code"]
                custom_name = get_custom_property(custom_mapping, canonical, "name")
                if custom_name:
                    return custom_name
                locale = canonical

        # Try standardized
        std = standardize_locale(locale)
        if std != locale:
            custom_name = get_custom_property(custom_mapping, std, "name")
            if custom_name:
                return custom_name

    try:
        std_locale = standardize_locale(locale)
        parsed = Locale.parse(std_locale, sep="-")

        # Build underscore tag for CLDR compound name lookup
        underscore_tag = parsed.language
        if parsed.script:
            underscore_tag += f"_{parsed.script}"
        if parsed.territory:
            underscore_tag += f"_{parsed.territory}"

        # Try lookup in display locale's language table for compound names
        try:
            display_locale = Locale.parse(default_locale, sep="-")
            # Compound names like "Austrian German", "American English"
            compound = display_locale.languages.get(underscore_tag)
            if compound:
                return compound
        except Exception:
            pass

        # Fall back to get_display_name
        name = parsed.get_display_name(default_locale)
        if name:
            return name

        return ""
    except Exception:
        return ""
