"""Region metadata lookup.

Ports ``getRegionProperties.ts`` from the JS core library.
Returns the display name and flag emoji for an ISO 3166-1 alpha-2 or
UN M.49 region code.
"""

from __future__ import annotations

from babel import Locale

from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE
from generaltranslation.locales._get_locale_emoji import DEFAULT_EMOJI, EMOJIS
from generaltranslation.locales._types import CustomRegionMapping


def get_region_properties(
    region: str,
    default_locale: str | None = LIBRARY_DEFAULT_LOCALE,
    custom_mapping: CustomRegionMapping | None = None,
) -> dict[str, str]:
    """Return metadata for a region code.

    Looks up a region by its ISO 3166-1 alpha-2 (e.g. ``"US"``) or
    UN M.49 (e.g. ``"419"``) code and returns its localised display
    name and flag emoji.

    Custom mapping entries override the default name and/or emoji.

    Args:
        region: The region code to look up.
        default_locale: The locale in which to render the region name
            (defaults to ``"en"``).
        custom_mapping: Optional mapping of region codes to custom
            ``{"name": ..., "emoji": ..., "locale": ...}`` overrides.

    Returns:
        A dict with keys ``"code"``, ``"name"``, and ``"emoji"``.
        May also include ``"locale"`` if provided by *custom_mapping*.

    Examples:
        >>> get_region_properties("US")
        {'code': 'US', 'name': 'United States', 'emoji': '🇺🇸'}
        >>> get_region_properties("US", default_locale="fr")
        {'code': 'US', 'name': 'États-Unis', 'emoji': '🇺🇸'}
    """
    result: dict[str, str] = {"code": region}

    # Get emoji from EMOJIS dict
    result["emoji"] = EMOJIS.get(region, DEFAULT_EMOJI)

    # Get region name from Babel
    try:
        display_locale = Locale.parse(default_locale, sep="-")
        name = display_locale.territories.get(region, "")
        result["name"] = name
    except Exception:
        result["name"] = ""

    # Apply custom mapping overrides
    if custom_mapping is not None and region in custom_mapping:
        custom = custom_mapping[region]
        if "name" in custom:
            result["name"] = custom["name"]
        if "emoji" in custom:
            result["emoji"] = custom["emoji"]
        if "locale" in custom:
            result["locale"] = custom["locale"]

    return result
