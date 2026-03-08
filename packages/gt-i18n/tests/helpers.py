"""Shared test helpers for converting JS-style fixture keys to Python-style."""

from __future__ import annotations

import base64
import json
from typing import Any

# Mapping from JS $-prefixed keys to Python _-prefixed keys
JS_TO_PY_KEY_MAP: dict[str, str] = {
    "$context": "_context",
    "$id": "_id",
    "$max_chars": "_max_chars",
    "$_source": "__source",
    "$_hash": "__hash",
}


def convert_keys(d: dict[str, Any]) -> dict[str, Any]:
    """Convert JS-style $-prefixed keys to Python-style _-prefixed keys."""
    return {JS_TO_PY_KEY_MAP.get(k, k): v for k, v in d.items()}


def convert_encoded_string(encoded: str) -> str:
    """Re-encode a JS-style encoded message with Python-style keys.

    Takes 'message:base64payload', decodes the payload, converts
    $-prefixed keys to _-prefixed, and re-encodes.
    """
    idx = encoded.rfind(":")
    if idx == -1:
        return encoded
    msg_part = encoded[:idx]
    payload = json.loads(base64.b64decode(encoded[idx + 1 :]).decode())
    converted = convert_keys(payload)
    new_b64 = base64.b64encode(json.dumps(converted, separators=(",", ":")).encode()).decode()
    return f"{msg_part}:{new_b64}"
