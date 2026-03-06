"""Decode encoded messages from msg()."""

from __future__ import annotations

import base64
import json


def decode_msg(encoded_msg: str) -> str:
    """Extract the interpolated message from an encoded msg() result.

    Splits at the last colon. If no colon is found, returns the input as-is.
    """
    idx = encoded_msg.rfind(":")
    if idx == -1:
        return encoded_msg
    return encoded_msg[:idx]


def decode_options(encoded_msg: str) -> dict[str, object] | None:
    """Extract the options dict from an encoded msg() result.

    Returns None if the message has no colon or the base64 payload is invalid.
    """
    idx = encoded_msg.rfind(":")
    if idx == -1:
        return None
    try:
        return json.loads(base64.b64decode(encoded_msg[idx + 1 :]).decode())
    except Exception:
        return None
