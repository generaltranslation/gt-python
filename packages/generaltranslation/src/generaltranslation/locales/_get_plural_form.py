"""Plural form selection for a given number.

Ports ``getPluralForm.ts`` from the JS core library.
Uses CLDR plural rules (via ``babel``) instead of the browser
``Intl.PluralRules`` API.
"""

from __future__ import annotations

from babel import Locale

from generaltranslation.locales._types import PLURAL_FORMS, PluralType

# Aliases between our custom form names and CLDR form names
_ALIASES: dict[str, str] = {
    "one": "singular",
    "singular": "one",
    "two": "dual",
    "dual": "two",
    "other": "plural",
    "plural": "other",
}


def get_plural_form(
    n: int | float,
    forms: list[PluralType] | None = None,
    locales: list[str] | None = None,
) -> PluralType | str:
    """Determine the plural form for number *n*.

    Selects the most appropriate plural branch from *forms* based on
    CLDR plural rules for the given *locales*.

    The selection follows a priority system with overrides:

    - ``n == 0`` and ``"zero"`` is available -> ``"zero"``
    - ``|n| == 1`` and ``"singular"``/``"one"`` is available -> use it
    - ``|n| == 2`` and ``"dual"``/``"two"`` is available -> use it
    - Otherwise, consult CLDR plural rules for the locale and find the
      best available form, with aliases.

    Args:
        n: The number to select a plural form for.
        forms: The allowed plural forms to choose from.
        locales: BCP 47 locale tags for plural rule selection.
            Defaults to ``["en"]``.

    Returns:
        The selected plural form name, or ``""`` if no form fits.
    """
    if forms is None:
        forms = list(PLURAL_FORMS)
    if locales is None:
        locales = ["en"]

    forms_set = set(forms)

    # Override: n == 0 and "zero" is available
    if n == 0 and "zero" in forms_set:
        return "zero"

    # Override: |n| == 1 and "singular" or "one" is available
    if abs(n) == 1:
        if "singular" in forms_set:
            return "singular"
        if "one" in forms_set:
            return "one"

    # Override: |n| == 2 and "dual" or "two" is available
    if abs(n) == 2:
        if "dual" in forms_set:
            return "dual"
        if "two" in forms_set:
            return "two"

    # Get CLDR plural category for the locale
    cldr_category = _get_cldr_category(n, locales)

    # Try to find the best matching form
    return _find_best_form(cldr_category, forms_set, forms)


def _get_cldr_category(n: int | float, locales: list[str]) -> str:
    """Get CLDR plural category for n in the given locale."""
    for locale_tag in locales:
        try:
            parsed = Locale.parse(locale_tag, sep="-")
            rule = parsed.plural_form
            category = rule(abs(n))
            return category
        except Exception:
            continue
    # Default to English rules
    try:
        rule = Locale("en").plural_form
        return rule(abs(n))
    except Exception:
        return "other"


def _find_best_form(
    cldr_category: str,
    forms_set: set[str],
    forms: list[str],
) -> str:
    """Find the best available form matching the CLDR category."""
    # Direct match
    if cldr_category in forms_set:
        return cldr_category

    # Try alias
    alias = _ALIASES.get(cldr_category)
    if alias and alias in forms_set:
        return alias

    # Fallback to "other" or "plural"
    if "other" in forms_set:
        return "other"
    if "plural" in forms_set:
        return "plural"

    # Last resort: return the last form in the list
    if forms:
        return forms[-1]

    return ""
