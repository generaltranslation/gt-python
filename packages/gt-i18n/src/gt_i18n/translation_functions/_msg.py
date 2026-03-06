"""msg() -- register a message with its hash for later retrieval."""

from __future__ import annotations

import base64
import json

from generaltranslation.formatting._format_message import format_message
from generaltranslation.static._constants import VAR_IDENTIFIER

from gt_i18n.translation_functions._extract_variables import extract_variables
from gt_i18n.translation_functions._hash_message import hash_message


def msg(message: str, **kwargs: object) -> str:
    """Register a message and return an encoded string.

    If no options are provided, returns the message unchanged.
    Otherwise returns ``{interpolated}:{base64options}``.
    """
    if not kwargs:
        return message

    variables = extract_variables(kwargs)

    # Interpolate the message
    try:
        interpolated = format_message(message, None, {**variables, VAR_IDENTIFIER: "other"})
    except Exception:
        return message

    # Build encoded options (preserve all kwargs including $-prefixed)
    h = kwargs.get("$_hash") or hash_message(
        message,
        context=kwargs.get("$context"),  # type: ignore[arg-type]
        id=kwargs.get("$id"),  # type: ignore[arg-type]
        max_chars=kwargs.get("$max_chars"),  # type: ignore[arg-type]
    )

    encoded_options = {**kwargs, "$_source": message, "$_hash": h}
    options_encoding = base64.b64encode(json.dumps(encoded_options, separators=(",", ":")).encode()).decode()

    return f"{interpolated}:{options_encoding}"
