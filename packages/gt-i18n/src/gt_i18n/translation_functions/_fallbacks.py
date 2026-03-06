"""Fallback functions: t_fallback() and m_fallback()."""

from __future__ import annotations

from gt_i18n.translation_functions._interpolate import interpolate_message


def t_fallback(message: str, **kwargs: object) -> str:
    """Interpolate variables into a message without translation lookup."""
    return interpolate_message(message, kwargs)


def m_fallback(encoded_msg: str | None, **kwargs: object) -> str | None:
    """Fallback for encoded messages -- decodes if encoded, else delegates."""
    if not encoded_msg:
        return encoded_msg  # type: ignore[return-value]

    from gt_i18n.translation_functions._decode import decode_msg, decode_options
    from gt_i18n.translation_functions._is_encoded import (
        is_encoded_translation_options,
    )

    decoded = decode_options(encoded_msg) or {}
    if is_encoded_translation_options(decoded):
        return decode_msg(encoded_msg)

    return t_fallback(encoded_msg, **kwargs)
