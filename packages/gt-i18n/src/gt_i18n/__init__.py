"""Python i18n library for General Translation."""

from generaltranslation.static import declare_static, declare_var, decode_vars

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
    # Static variable helpers
    "declare_var",
    "declare_static",
    "decode_vars",
]
