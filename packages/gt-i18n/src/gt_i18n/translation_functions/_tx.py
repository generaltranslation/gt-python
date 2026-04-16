"""The ``tx()`` function — runtime translation via GT.translate_many.

Mirror of the JS ``tx()`` added in gt PR #1207: an async string translator
that fetches a translation on cache miss, caches it, and falls back to the
source on any failure. Default data format is ``STRING``.
"""

from __future__ import annotations

from typing import Any

from gt_i18n.i18n_manager._singleton import get_i18n_manager
from gt_i18n.translation_functions._interpolate import interpolate_message


async def tx(content: str, **kwargs: Any) -> str:
    """Runtime translate a string, then interpolate variables.

    On cache miss, batches into a ``GT.translate_many`` call (via the active
    I18nManager's TranslationsCache). Returns the interpolated source if the
    target locale matches the source locale, or if runtime translation fails.

    Args:
        content: The source message.
        **kwargs: Interpolation variables and GT options
            (``_locale``, ``_format``, ``_context``, ``_id``, ``_max_chars``).

    Returns:
        The translated and interpolated string, or interpolated source on failure.
    """
    manager = get_i18n_manager()
    kwargs.setdefault("_format", "STRING")

    translation = await manager.lookup_translation_with_fallback(content, **kwargs)
    target = translation if translation is not None else content
    locale = kwargs.get("_locale") or manager.get_locale()
    return interpolate_message(target, kwargs, locale)
