"""Flask integration for General Translation."""

from gt_i18n import (
    declare_static,
    declare_var,
    decode_vars,
    derive,
    get_default_locale,
    get_locale,
    get_locales,
    get_version_id,
    t,
    tx,
)

from gt_flask._setup import initialize_gt

__all__ = [
    "initialize_gt",
    "t",
    "tx",
    "declare_var",
    "derive",
    "declare_static",
    "decode_vars",
    "get_locale",
    "get_locales",
    "get_default_locale",
    "get_version_id",
]
