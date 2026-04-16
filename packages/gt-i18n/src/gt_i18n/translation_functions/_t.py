"""The ``t()`` function — primary user-facing translation function."""

from __future__ import annotations

from gt_i18n.i18n_manager._singleton import get_i18n_manager
from gt_i18n.translation_functions._interpolate import interpolate_message


def t(message: str, **kwargs: object) -> str:
    """Translate and interpolate a message.

    Looks up the current locale from the I18nManager, finds a cached
    translation via ``lookup_translation``, and interpolates variables.
    Falls back to the source message if no translation is available.

    Args:
        message: The ICU MessageFormat source string.
        **kwargs: Interpolation variables and GT options
            (``_context``, ``_id``, ``_max_chars``).

    Returns:
        The translated and interpolated string.
    """
    manager = get_i18n_manager()
    locale = manager.get_locale()

    if not manager.requires_translation(locale):
        return interpolate_message(message, kwargs, locale)

    translated = manager.lookup_translation(
        message,
        _context=kwargs.get("_context"),
        _id=kwargs.get("_id"),
        _max_chars=kwargs.get("_max_chars"),
        _format="ICU",
    )
    if translated:
        return interpolate_message(translated, {**kwargs, "__fallback": message}, locale)

    # No translation found — use source
    return interpolate_message(message, kwargs, locale)
