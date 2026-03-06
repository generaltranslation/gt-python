"""Fallback functions: t_fallback() and m_fallback()."""

from __future__ import annotations

from gt_i18n.translation_functions._interpolate import interpolate_message


def t_fallback(message: str, **kwargs: object) -> str:
    """Interpolate variables into a message without translation lookup.

    Useful for fallback rendering or when the user just wants variable
    interpolation without the full translation pipeline.

    Args:
        message: The ICU MessageFormat string.
        **kwargs: Interpolation variables and GT options.

    Returns:
        The interpolated string.
    """
    return interpolate_message(message, kwargs)


def m_fallback(encoded: str) -> str:
    """Fallback for encoded messages — decodes then interpolates.

    Args:
        encoded: A base64-encoded message string from ``msg()``.

    Returns:
        The decoded and interpolated string.
    """
    from gt_i18n.translation_functions._decode import decode_msg

    return decode_msg(encoded)
