"""Filter GT-reserved keys from options, returning user variables."""

from __future__ import annotations

_GT_RESERVED_KEYS = frozenset(
    {
        "_context",
        "_id",
        "_max_chars",
        "__hash",
        "__source",
        "__fallback",
    }
)


def extract_variables(options: dict[str, object]) -> dict[str, object]:
    """Return only user interpolation variables.

    Args:
        options: The full kwargs dict which may contain GT-reserved keys
            like ``_context``, ``_id``, ``_max_chars``, etc.

    Returns:
        A new dict with GT-reserved keys removed.
    """
    return {k: v for k, v in options.items() if k not in _GT_RESERVED_KEYS}
