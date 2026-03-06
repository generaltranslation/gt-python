"""Supported locale mapping and lookup functions."""

from generaltranslation import (
    get_locale_properties,
    is_valid_locale,
    standardize_locale,
)

from generaltranslation_supported_locales._data import _SUPPORTED_LOCALES


def _get_matching_code(
    exact_supported_locales: list[str],
    locale: str,
    language_code: str,
    region_code: str,
    script_code: str,
    minimized_code: str,
) -> str | None:
    """Try to match a locale against the supported list for a language."""
    candidates = [
        locale,
        f"{language_code}-{region_code}",
        f"{language_code}-{script_code}",
        minimized_code,
    ]
    for candidate in candidates:
        if candidate in exact_supported_locales:
            return candidate
    return None


def get_supported_locale(locale: str) -> str | None:
    """Validate and map a locale to a supported locale.

    Args:
        locale: A BCP 47 locale string.

    Returns:
        The supported locale string, or None if not supported.
    """
    if not is_valid_locale(locale):
        return None

    locale = standardize_locale(locale)

    props = get_locale_properties(locale)
    language_code = props.language_code or locale
    region_code = props.region_code
    script_code = props.script_code
    minimized_code = props.minimized_code

    exact_supported_locales = _SUPPORTED_LOCALES.get(language_code)
    if not exact_supported_locales:
        return None

    # First try with the original locale's properties
    match = _get_matching_code(
        exact_supported_locales,
        locale,
        language_code,
        region_code,
        script_code,
        minimized_code,
    )
    if match:
        return match

    # Fall back: try with the language code's own properties
    lang_props = get_locale_properties(language_code)
    return _get_matching_code(
        exact_supported_locales,
        language_code,
        lang_props.language_code,
        lang_props.region_code,
        lang_props.script_code,
        lang_props.minimized_code,
    )


def list_supported_locales() -> list[str]:
    """Get a sorted list of all supported locales.

    Returns:
        A sorted list of supported locale strings.
    """
    result: list[str] = []
    for locale_list in _SUPPORTED_LOCALES.values():
        result.extend(locale_list)
    return sorted(result)
