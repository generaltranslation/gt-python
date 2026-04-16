"""Python i18n library for General Translation."""

from generaltranslation.static import declare_static, declare_var, decode_vars, derive

from gt_i18n.helpers._locales import (
    get_default_locale,
    get_locale,
    get_locales,
)
from gt_i18n.helpers._version_id import get_version_id
from gt_i18n.i18n_manager import (
    ContextVarStorageAdapter,
    I18nManager,
    StorageAdapter,
    TranslationsLoader,
    get_i18n_manager,
    set_i18n_manager,
)
from gt_i18n.translation_functions import (
    decode_msg,
    decode_options,
    extract_variables,
    hash_message,
    interpolate_message,
    m_fallback,
    msg,
    t,
    t_fallback,
    tx,
)

__all__ = [
    # I18nManager
    "ContextVarStorageAdapter",
    "I18nManager",
    "StorageAdapter",
    "TranslationsLoader",
    "get_i18n_manager",
    "set_i18n_manager",
    # Translation functions
    "decode_msg",
    "decode_options",
    "extract_variables",
    "hash_message",
    "interpolate_message",
    "m_fallback",
    "msg",
    "t",
    "t_fallback",
    "tx",
    # Locale helpers
    "get_locale",
    "get_locales",
    "get_default_locale",
    # Version
    "get_version_id",
    # Derive / variable helpers
    "declare_var",
    "derive",
    "declare_static",
    "decode_vars",
]
