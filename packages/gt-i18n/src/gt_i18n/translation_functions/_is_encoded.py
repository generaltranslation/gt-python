"""Check if decoded options represent an encoded translation."""

from __future__ import annotations


def is_encoded_translation_options(decoded_options: dict[str, object]) -> bool:
    """Return True if the dict contains both ``__hash`` and ``__source``."""
    return bool(decoded_options.get("__hash") and decoded_options.get("__source"))
