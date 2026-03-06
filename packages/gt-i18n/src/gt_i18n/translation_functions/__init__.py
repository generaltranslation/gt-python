"""Translation functions: t(), msg(), fallbacks, hashing, interpolation."""

from gt_i18n.translation_functions._decode import decode_msg, decode_options
from gt_i18n.translation_functions._extract_variables import extract_variables
from gt_i18n.translation_functions._fallbacks import m_fallback, t_fallback
from gt_i18n.translation_functions._hash_message import hash_message
from gt_i18n.translation_functions._interpolate import interpolate_message
from gt_i18n.translation_functions._msg import msg
from gt_i18n.translation_functions._t import t

__all__ = [
    "decode_msg",
    "decode_options",
    "extract_variables",
    "hash_message",
    "interpolate_message",
    "m_fallback",
    "msg",
    "t",
    "t_fallback",
]
