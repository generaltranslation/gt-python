"""Locale utilities: validation, properties, names, direction, emoji.

This subpackage provides BCP 47 locale handling functions, ported from
the JS ``generaltranslation`` core library.  All public functions are
re-exported here for convenience.
"""

from generaltranslation.locales._custom_locale_mapping import (
    get_custom_property,
    should_use_canonical_locale,
)
from generaltranslation.locales._determine_locale import determine_locale
from generaltranslation.locales._get_locale_direction import get_locale_direction
from generaltranslation.locales._get_locale_emoji import get_locale_emoji
from generaltranslation.locales._get_locale_name import get_locale_name
from generaltranslation.locales._get_locale_properties import (
    get_locale_properties,
)
from generaltranslation.locales._get_plural_form import get_plural_form
from generaltranslation.locales._get_region_properties import get_region_properties
from generaltranslation.locales._is_same_dialect import is_same_dialect
from generaltranslation.locales._is_same_language import is_same_language
from generaltranslation.locales._is_superset_locale import is_superset_locale
from generaltranslation.locales._is_valid_locale import (
    is_valid_locale,
    standardize_locale,
)
from generaltranslation.locales._requires_translation import requires_translation
from generaltranslation.locales._resolve_locale import (
    resolve_alias_locale,
    resolve_canonical_locale,
)
from generaltranslation.locales._types import (
    PLURAL_FORMS,
    CustomMapping,
    CustomRegionMapping,
    LocaleProperties,
    PluralType,
    is_accepted_plural_form,
)

__all__ = [
    # Types & constants
    "LocaleProperties",
    "CustomMapping",
    "CustomRegionMapping",
    "PluralType",
    "PLURAL_FORMS",
    "is_accepted_plural_form",
    # Custom mapping helpers
    "get_custom_property",
    "should_use_canonical_locale",
    # Validation & standardisation
    "is_valid_locale",
    "standardize_locale",
    # Metadata
    "get_locale_properties",
    "get_locale_name",
    "get_locale_emoji",
    "get_locale_direction",
    "get_region_properties",
    # Resolution & matching
    "determine_locale",
    "resolve_canonical_locale",
    "resolve_alias_locale",
    # Comparison
    "is_same_language",
    "is_same_dialect",
    "is_superset_locale",
    # Translation logic
    "requires_translation",
    # Plurals
    "get_plural_form",
]
