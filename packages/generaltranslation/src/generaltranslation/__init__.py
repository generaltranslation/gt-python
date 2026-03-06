"""Core Python language toolkit for General Translation."""

from generaltranslation._gt import GT
from generaltranslation._settings import (
    API_VERSION,
    DEFAULT_BASE_URL,
    DEFAULT_CACHE_URL,
    DEFAULT_RUNTIME_API_URL,
    DEFAULT_TIMEOUT,
    LIBRARY_DEFAULT_LOCALE,
)
from generaltranslation.errors import ApiError
from generaltranslation._id import hash_source, hash_string, hash_template
from generaltranslation.formatting import (
    CutoffFormat,
    format_currency,
    format_cutoff,
    format_date_time,
    format_list,
    format_list_to_parts,
    format_message,
    format_num,
    format_relative_time,
)
from generaltranslation.locales import (
    PLURAL_FORMS,
    CustomMapping,
    CustomRegionMapping,
    LocaleProperties,
    PluralType,
    determine_locale,
    get_locale_direction,
    get_locale_emoji,
    get_locale_name,
    get_locale_properties,
    get_plural_form,
    get_region_properties,
    is_accepted_plural_form,
    is_same_dialect,
    is_same_language,
    is_superset_locale,
    is_valid_locale,
    requires_translation,
    resolve_alias_locale,
    resolve_canonical_locale,
    standardize_locale,
)
from generaltranslation.static import (
    VAR_IDENTIFIER,
    VAR_NAME_IDENTIFIER,
    condense_vars,
    decode_vars,
    declare_static,
    declare_var,
    extract_vars,
    index_vars,
    sanitize_var,
)

__all__ = [
    # Core class
    "GT",
    # Constants
    "LIBRARY_DEFAULT_LOCALE",
    "DEFAULT_BASE_URL",
    "DEFAULT_CACHE_URL",
    "DEFAULT_RUNTIME_API_URL",
    "DEFAULT_TIMEOUT",
    "API_VERSION",
    "PLURAL_FORMS",
    # Errors
    "ApiError",
    # ID / Hashing
    "hash_string",
    "hash_source",
    "hash_template",
    # Formatting
    "format_num",
    "format_currency",
    "format_date_time",
    "format_list",
    "format_list_to_parts",
    "format_relative_time",
    "format_message",
    "format_cutoff",
    "CutoffFormat",
    # Locale types
    "LocaleProperties",
    "CustomMapping",
    "CustomRegionMapping",
    "PluralType",
    "is_accepted_plural_form",
    # Locale functions
    "is_valid_locale",
    "standardize_locale",
    "get_locale_properties",
    "get_locale_name",
    "get_locale_emoji",
    "get_locale_direction",
    "get_region_properties",
    "determine_locale",
    "resolve_canonical_locale",
    "resolve_alias_locale",
    "is_same_language",
    "is_same_dialect",
    "is_superset_locale",
    "requires_translation",
    "get_plural_form",
    # Static
    "VAR_IDENTIFIER",
    "VAR_NAME_IDENTIFIER",
    "sanitize_var",
    "declare_var",
    "declare_static",
    "decode_vars",
    "extract_vars",
    "index_vars",
    "condense_vars",
]
