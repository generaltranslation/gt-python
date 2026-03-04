"""Canonical ↔ alias locale resolution.

Ports ``resolveCanonicalLocale.ts`` and ``resolveAliasLocale.ts`` from
the JS core library.  These two functions form an invertible mapping
between user-defined locale aliases and their canonical BCP 47 codes.
"""

from __future__ import annotations

from generaltranslation.locales._types import CustomMapping


def resolve_canonical_locale(
    locale: str,
    custom_mapping: CustomMapping | None = None,
) -> str:
    """Resolve a locale alias to its canonical BCP 47 code.

    If *custom_mapping* contains an entry for *locale* that is a dict
    with a ``"code"`` key pointing to a valid locale, that code is
    returned.  Otherwise *locale* is returned unchanged.

    Args:
        locale: A locale tag or alias to resolve.
        custom_mapping: Optional custom mapping defining aliases.

    Returns:
        The canonical locale code.

    Examples:
        >>> mapping = {"pt-custom": {"code": "pt-BR", "name": "Custom PT"}}
        >>> resolve_canonical_locale("pt-custom", mapping)
        'pt-BR'
        >>> resolve_canonical_locale("en")
        'en'
    """
    if custom_mapping is not None:
        from generaltranslation.locales._custom_locale_mapping import (
            should_use_canonical_locale,
        )

        if should_use_canonical_locale(locale, custom_mapping):
            entry = custom_mapping[locale]
            if isinstance(entry, dict):
                return entry["code"]
    return locale


def resolve_alias_locale(
    locale: str,
    custom_mapping: CustomMapping | None = None,
) -> str:
    """Resolve a canonical locale code back to its alias.

    Builds a reverse index from *custom_mapping* (canonical code →
    alias key) and returns the alias for *locale* if one exists.
    Otherwise returns *locale* unchanged.

    Args:
        locale: A canonical BCP 47 locale code.
        custom_mapping: Optional custom mapping defining aliases.

    Returns:
        The alias locale string, or *locale* if no alias is defined.

    Examples:
        >>> mapping = {"pt-custom": {"code": "pt-BR", "name": "Custom PT"}}
        >>> resolve_alias_locale("pt-BR", mapping)
        'pt-custom'
        >>> resolve_alias_locale("en", mapping)
        'en'
    """
    if custom_mapping is not None:
        from generaltranslation.locales._custom_locale_mapping import (
            should_use_canonical_locale,
        )

        for alias, entry in custom_mapping.items():
            if should_use_canonical_locale(alias, custom_mapping):
                if isinstance(entry, dict) and entry.get("code") == locale:
                    return alias
    return locale
