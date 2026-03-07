"""FastAPI integration for General Translation."""

from gt_i18n import (
  declare_static, declare_var, decode_vars, t, get_locale, get_locales, get_default_locale
)
from gt_fastapi._setup import initialize_gt

__all__ = ["initialize_gt", "t", "declare_var", "declare_static", "decode_vars", "get_locale", "get_locales", "get_default_locale"]
