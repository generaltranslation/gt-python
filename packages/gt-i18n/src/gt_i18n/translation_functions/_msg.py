"""msg() — register a message with its hash for later retrieval."""

from __future__ import annotations

import base64
import json

from gt_i18n.translation_functions._hash_message import hash_message


def msg(message: str, **kwargs: object) -> str:
    """Register a message and return an encoded string with hash and source.

    The returned string contains a base64-encoded JSON payload with the
    source message, its hash, and any interpolation variables.

    Args:
        message: The ICU MessageFormat source string.
        **kwargs: Interpolation variables and GT options.

    Returns:
        A base64-encoded string.
    """
    context = kwargs.get("$context")
    msg_id = kwargs.get("$id")
    max_chars = kwargs.get("$max_chars")

    h = hash_message(
        message,
        context=context,  # type: ignore[arg-type]
        id=msg_id,  # type: ignore[arg-type]
        max_chars=max_chars,  # type: ignore[arg-type]
    )

    # Filter user variables (non-$ keys)
    variables = {k: v for k, v in kwargs.items() if not k.startswith("$")}

    payload = {
        "$_source": message,
        "$_hash": h,
        **variables,
    }

    encoded = base64.b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode()

    return encoded
