"""Internal helpers for custom locale mapping lookups.

Ports ``customLocaleMapping.ts`` from the JS core library.
Custom mappings allow users to define locale aliases (e.g. ``"es-LAM"``
→ ``"es-419"``) and override display properties without modifying
standard BCP 47 codes.
"""

from __future__ import annotations

from generaltranslation.locales._types import CustomMapping


def get_custom_property(
    custom_mapping: CustomMapping,
    locale: str,
    property_name: str,
) -> str | None:
    """Look up a single property from a custom mapping entry.

    If the mapping entry for *locale* is a plain string, only ``"name"``
    is available.  If it is a dict, the requested *property_name* key is
    returned when present.

    Args:
        custom_mapping: The custom locale mapping dict.
        locale: The locale key to look up in the mapping.
        property_name: The property to extract (e.g. ``"name"``,
            ``"emoji"``, ``"code"``).

    Returns:
        The property value if found, otherwise ``None``.

    Examples:
        >>> mapping = {"es-LAM": "Latin American Spanish"}
        >>> get_custom_property(mapping, "es-LAM", "name")
        'Latin American Spanish'
        >>> get_custom_property(mapping, "es-LAM", "emoji") is None
        True
    """
    entry = custom_mapping.get(locale)
    if entry is None:
        return None
    if isinstance(entry, str):
        return entry if property_name == "name" else None
    if isinstance(entry, dict):
        return entry.get(property_name)
    return None


def should_use_canonical_locale(
    locale: str,
    custom_mapping: CustomMapping,
) -> bool:
    """Check whether *locale* should be resolved to a canonical locale via the mapping.

    A custom mapping entry triggers canonical resolution when it is a dict
    containing a ``"code"`` key whose value is itself a valid BCP 47 locale.

    Args:
        locale: The locale alias to check.
        custom_mapping: The custom locale mapping dict.

    Returns:
        ``True`` if the mapping redirects *locale* to a canonical code.

    Examples:
        >>> mapping = {"pt-custom": {"code": "pt-BR", "name": "Custom PT"}}
        >>> should_use_canonical_locale("pt-custom", mapping)
        True
        >>> should_use_canonical_locale("en", mapping)
        False
    """
    entry = custom_mapping.get(locale)
    if isinstance(entry, dict) and "code" in entry:
        return True
    return False
