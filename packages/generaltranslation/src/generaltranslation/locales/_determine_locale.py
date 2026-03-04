"""Best-match locale resolution.

Ports ``determineLocale.ts`` from the JS core library.
Given a list of requested locales and a list of approved locales,
finds the best available match.
"""

from __future__ import annotations

from babel import Locale

from generaltranslation.locales._types import CustomMapping


def determine_locale(
    locales: str | list[str],
    approved_locales: list[str],
    custom_mapping: CustomMapping | None = None,
) -> str | None:
    """Find the best matching locale from *approved_locales*.

    Iterates through *locales* in preference order and, for each one,
    searches *approved_locales* for:

    1. An exact match (after standardisation).
    2. A match on ``language-region`` or ``language-script``.
    3. A match on the minimised locale code.
    4. A same-language fallback using the base language code.

    Both input lists are filtered to valid locales and standardised
    before comparison.

    Args:
        locales: One or more BCP 47 locale tags the caller prefers,
            in descending priority.
        approved_locales: The set of locales the application supports.
        custom_mapping: Optional custom mapping passed through to
            validation and property resolution.

    Returns:
        The best matching locale from *approved_locales*, or ``None``
        if no match is found.

    Examples:
        >>> determine_locale("en-US", ["en", "fr", "de"])
        'en'
        >>> determine_locale(["ja", "en"], ["en-US", "fr"])
        'en-US'
        >>> determine_locale("ko", ["en", "fr"]) is None
        True
    """
    from generaltranslation.locales._is_valid_locale import (
        is_valid_locale,
        standardize_locale,
    )
    from generaltranslation.locales.utils import minimize_locale

    # Normalize input to list
    if isinstance(locales, str):
        locale_list = [locales]
    else:
        locale_list = list(locales)

    # Filter and standardize requested locales
    valid_requests: list[tuple[str, Locale]] = []
    for loc in locale_list:
        if is_valid_locale(loc, custom_mapping):
            std = standardize_locale(loc)
            try:
                parsed = Locale.parse(std, sep="-")
                valid_requests.append((std, parsed))
            except Exception:
                pass

    # Filter and standardize approved locales, keeping original values
    valid_approved: list[tuple[str, str, Locale]] = []
    for loc in approved_locales:
        if is_valid_locale(loc, custom_mapping):
            std = standardize_locale(loc)
            try:
                parsed = Locale.parse(std, sep="-")
                valid_approved.append((loc, std, parsed))
            except Exception:
                pass

    if not valid_requests or not valid_approved:
        return None

    for req_std, req_parsed in valid_requests:
        # 1. Exact match
        for orig, app_std, app_parsed in valid_approved:
            if req_std == app_std:
                return orig

        # Find same-language candidates
        same_lang = [
            (orig, app_std, app_parsed)
            for orig, app_std, app_parsed in valid_approved
            if app_parsed.language == req_parsed.language
        ]

        if not same_lang:
            continue

        # 2. Match on language-region or language-script
        if req_parsed.territory:
            for orig, app_std, app_parsed in same_lang:
                if app_parsed.territory == req_parsed.territory:
                    return orig

        if req_parsed.script:
            for orig, app_std, app_parsed in same_lang:
                if app_parsed.script == req_parsed.script:
                    return orig

        # 3. Match on minimized locale
        req_min = minimize_locale(req_std)
        for orig, app_std, app_parsed in same_lang:
            app_min = minimize_locale(app_std)
            if req_min == app_min:
                return orig

        # 4. Same-language fallback - return first same-language match
        return same_lang[0][0]

    return None
