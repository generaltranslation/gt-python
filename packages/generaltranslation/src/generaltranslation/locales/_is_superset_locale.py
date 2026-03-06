"""Locale hierarchy / superset checking.

Ports ``isSupersetLocale.ts`` from the JS core library.
A locale is a "superset" of another if it is equal to or more general
than the other (e.g. ``"en"`` is a superset of ``"en-US"``).
"""

from __future__ import annotations

from babel import Locale


def is_superset_locale(super_locale: str, sub_locale: str) -> bool:
    """Return ``True`` if *super_locale* is a superset of *sub_locale*.

    *super_locale* is a superset when:

    - Both have the same language code.
    - *super_locale* either has no region or its region matches
      *sub_locale*'s region.
    - *super_locale* either has no script or its script matches
      *sub_locale*'s script.

    In other words, a more general locale (fewer subtags) is always a
    superset of a more specific one with the same language.

    Args:
        super_locale: The potentially more general locale.
        sub_locale: The potentially more specific locale.

    Returns:
        ``True`` if *super_locale* encompasses *sub_locale*,
        ``False`` otherwise (including on parse errors).

    Examples:
        >>> is_superset_locale("en", "en-US")
        True
        >>> is_superset_locale("en-US", "en")
        False
        >>> is_superset_locale("en-US", "en-US")
        True
        >>> is_superset_locale("en-US", "en-GB")
        False
    """
    try:
        from generaltranslation.locales._is_valid_locale import standardize_locale

        sup = Locale.parse(standardize_locale(super_locale), sep="-")
        sub = Locale.parse(standardize_locale(sub_locale), sep="-")

        if sup.language != sub.language:
            return False

        if sup.territory and sup.territory != sub.territory:
            return False

        if sup.script and sup.script != sub.script:
            return False

        # super can't be more specific than sub
        if sup.territory and not sub.territory:
            return False

        if sup.script and not sub.script:
            return False

        return True
    except Exception:
        return False
