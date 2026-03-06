"""Check if decoded options represent an encoded translation."""

from __future__ import annotations


def is_encoded_translation_options(decoded_options: dict[str, object]) -> bool:
    """Return True if the dict contains both ``$_hash`` and ``$_source``."""
    return bool(decoded_options.get("$_hash") and decoded_options.get("$_source"))
