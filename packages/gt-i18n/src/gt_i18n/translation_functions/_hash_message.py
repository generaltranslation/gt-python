"""Hash an ICU message string for translation lookup."""

from __future__ import annotations

from generaltranslation._id._hash import hash_source
from generaltranslation.static._index_vars import index_vars


def hash_message(
    message: str,
    *,
    context: str | None = None,
    id: str | None = None,
    max_chars: int | None = None,
) -> str:
    """Hash an ICU message after indexing its variables.

    Args:
        message: The ICU MessageFormat source string.
        context: Optional context string for disambiguation.
        id: Optional explicit message ID.
        max_chars: Optional max character constraint.

    Returns:
        A hex hash string.
    """
    return hash_source(
        index_vars(message),
        context=context,
        id=id,
        max_chars=max_chars,
        data_format="ICU",
    )
