"""Decode encoded messages from msg()."""

from __future__ import annotations

import base64
import json

from gt_i18n.translation_functions._interpolate import interpolate_message


def decode_options(encoded: str) -> dict[str, object]:
    """Decode a base64-encoded message payload from ``msg()``.

    Args:
        encoded: The base64 string.

    Returns:
        The decoded dict with ``$_source``, ``$_hash``, and variables.
    """
    raw = base64.b64decode(encoded).decode()
    return json.loads(raw)


def decode_msg(encoded: str) -> str:
    """Decode and interpolate a base64-encoded message from ``msg()``.

    Args:
        encoded: The base64 string.

    Returns:
        The interpolated source message.
    """
    options = decode_options(encoded)
    source = options.get("$_source", "")
    if not isinstance(source, str):
        source = str(source)
    return interpolate_message(source, options)
