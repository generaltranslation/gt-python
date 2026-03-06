"""Shared types for the locales subpackage.

Ports the locale-related type definitions from the JS core library:
- ``LocaleProperties`` dataclass (from ``getLocaleProperties.ts``)
- ``CustomMapping`` / ``CustomRegionMapping`` type aliases
- ``PluralType`` literal and ``PLURAL_FORMS`` constant (from ``settings/plurals.ts``)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Plural forms
# ---------------------------------------------------------------------------

PluralType = Literal[
    "singular",
    "plural",
    "dual",
    "zero",
    "one",
    "two",
    "few",
    "many",
    "other",
]
"""All recognised plural-form branch names."""

PLURAL_FORMS: list[PluralType] = [
    "singular",
    "plural",
    "dual",
    "zero",
    "one",
    "two",
    "few",
    "many",
    "other",
]
"""Ordered list of accepted plural forms, matching the JS ``pluralForms`` constant."""


def is_accepted_plural_form(form: str) -> bool:
    """Return ``True`` if *form* is a recognised plural-form name."""
    return form in PLURAL_FORMS


# ---------------------------------------------------------------------------
# Locale properties
# ---------------------------------------------------------------------------


@dataclass
class LocaleProperties:
    """Comprehensive metadata about a BCP 47 locale.

    This mirrors the JS ``LocaleProperties`` type from ``getLocaleProperties.ts``.
    All string fields default to ``""`` so callers can rely on safe access.

    Example for ``de-AT`` with *default_locale* ``"en-US"``:

    =========================================  =====================================
    Field                                      Example value
    =========================================  =====================================
    ``code``                                   ``"de-AT"``
    ``name``                                   ``"Austrian German"``
    ``native_name``                            ``"Österreichisches Deutsch"``
    ``language_code``                          ``"de"``
    ``language_name``                          ``"German"``
    ``native_language_name``                   ``"Deutsch"``
    ``name_with_region_code``                  ``"German (AT)"``
    ``native_name_with_region_code``           ``"Deutsch (AT)"``
    ``region_code``                            ``"AT"``
    ``region_name``                            ``"Austria"``
    ``native_region_name``                     ``"Österreich"``
    ``script_code``                            ``"Latn"``
    ``script_name``                            ``"Latin"``
    ``native_script_name``                     ``"Lateinisch"``
    ``maximized_code``                         ``"de-Latn-AT"``
    ``maximized_name``                         ``"Austrian German (Latin)"``
    ``native_maximized_name``                  ``"Österr. Deutsch (Lateinisch)"``
    ``minimized_code``                         ``"de-AT"``
    ``minimized_name``                         ``"Austrian German"``
    ``native_minimized_name``                  ``"Österreichisches Deutsch"``
    ``emoji``                                  ``"🇦🇹"``
    =========================================  =====================================
    """

    code: str = ""
    name: str = ""
    native_name: str = ""

    language_code: str = ""
    language_name: str = ""
    native_language_name: str = ""

    name_with_region_code: str = ""
    native_name_with_region_code: str = ""

    region_code: str = ""
    region_name: str = ""
    native_region_name: str = ""

    script_code: str = ""
    script_name: str = ""
    native_script_name: str = ""

    maximized_code: str = ""
    maximized_name: str = ""
    native_maximized_name: str = ""

    minimized_code: str = ""
    minimized_name: str = ""
    native_minimized_name: str = ""

    emoji: str = ""


# ---------------------------------------------------------------------------
# Custom mapping types
# ---------------------------------------------------------------------------

CustomMapping = dict[str, str | dict[str, str]]
"""Maps locale aliases to either a display name (``str``) or a partial
``LocaleProperties``-like dict.  When the dict contains a ``"code"`` key the
alias is treated as a redirect to that canonical locale.

Examples::

    # String form — just a custom name
    {"es-LAM": "Latin American Spanish"}

    # Dict form — partial properties
    {"en-simple": {"name": "Simple English", "emoji": "🎯"}}

    # Canonical redirect — alias resolves to real locale
    {"pt-BR-custom": {"code": "pt-BR", "name": "Custom Brazilian Portuguese"}}
"""

CustomRegionMapping = dict[str, dict[str, str]]
"""Maps region codes to custom ``{"name": ..., "emoji": ..., "locale": ...}``
overrides used by :func:`get_region_properties`."""
