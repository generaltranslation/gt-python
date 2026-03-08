"""The ``t()`` function — primary user-facing translation function."""

from __future__ import annotations

from gt_i18n.i18n_manager._singleton import get_i18n_manager
from gt_i18n.translation_functions._hash_message import hash_message
from gt_i18n.translation_functions._interpolate import interpolate_message


def t(message: str, **kwargs: object) -> str:
    """Translate and interpolate a message.

    Looks up the current locale from the I18nManager, finds a cached
    translation by hash, and interpolates variables. Falls back to the
    source message if no translation is available.

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

    translations = manager.get_translations_sync(locale)
    h = hash_message(
        message,
        context=kwargs.get("_context"),  # type: ignore[arg-type]
        id=kwargs.get("_id"),  # type: ignore[arg-type]
        max_chars=kwargs.get("_max_chars"),  # type: ignore[arg-type]
    )
    translated = translations.get(h)
    if translated:
        return interpolate_message(translated, {**kwargs, "__fallback": message}, locale)

    # No translation found — use source
    return interpolate_message(message, kwargs, locale)
