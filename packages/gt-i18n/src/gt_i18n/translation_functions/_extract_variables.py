"""Filter $-prefixed GT keys from options, returning user variables."""

from __future__ import annotations


def extract_variables(options: dict[str, object]) -> dict[str, object]:
    """Return only user interpolation variables (non-$ keys).

    Args:
        options: The full kwargs dict which may contain ``$context``,
            ``$id``, ``$max_chars``, etc.

    Returns:
        A new dict with only the user-provided variable keys.
    """
    return {k: v for k, v in options.items() if not k.startswith("$")}
