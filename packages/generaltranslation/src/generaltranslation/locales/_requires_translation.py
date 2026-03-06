"""Determine whether translation is needed between two locales.

Ports ``requiresTranslation.ts`` from the JS core library.
"""

from __future__ import annotations

from generaltranslation.locales._types import CustomMapping


def requires_translation(
    source_locale: str,
    target_locale: str,
    approved_locales: list[str] | None = None,
    custom_mapping: CustomMapping | None = None,
) -> bool:
    """Return ``True`` if translating from *source_locale* to *target_locale* is needed.

    Translation is **not** required (returns ``False``) when:

    1. Either locale is invalid.
    2. Any entry in *approved_locales* is invalid.
    3. *source_locale* and *target_locale* are the same dialect.
    4. *target_locale* is not represented in *approved_locales*
       (i.e. the application does not support that language at all).

    Otherwise, translation is required.

    Args:
        source_locale: The locale of the source content.
        target_locale: The locale to translate into.
        approved_locales: Optional list of locales the application
            supports.  If provided and *target_locale*'s language is
            not among them, translation is skipped.
        custom_mapping: Optional custom mapping passed through to
            locale validation.

    Returns:
        ``True`` if a translation should be performed.

    Examples:
        >>> requires_translation("en", "fr")
        True
        >>> requires_translation("en-US", "en")
        False
        >>> requires_translation("en", "ja", approved_locales=["fr", "de"])
        False
    """
    from generaltranslation.locales._is_same_dialect import is_same_dialect
    from generaltranslation.locales._is_same_language import is_same_language
    from generaltranslation.locales._is_valid_locale import is_valid_locale

    # Validate both locales
    if not is_valid_locale(source_locale, custom_mapping):
        return False
    if not is_valid_locale(target_locale, custom_mapping):
        return False

    # Same dialect means no translation needed
    if is_same_dialect(source_locale, target_locale):
        return False

    # Check approved locales
    if approved_locales is not None:
        # Validate all approved locales
        for approved in approved_locales:
            if not is_valid_locale(approved, custom_mapping):
                return False

        # Check if target language is represented in approved locales
        target_represented = any(
            is_same_language(target_locale, approved) for approved in approved_locales
        )
        if not target_represented:
            return False

    return True
