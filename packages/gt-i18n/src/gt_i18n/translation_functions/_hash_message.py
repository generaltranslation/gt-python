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
    format: str = "ICU",
) -> str:
    """Hash a message for translation lookup.

    For ICU-format messages, variables are first normalized via ``index_vars``
    so two templates differing only in variable names collide. For STRING and
    I18NEXT formats, the raw source is hashed verbatim — the wire representation
    is the user's literal template.

    Args:
        message: The message source string.
        context: Optional context string for disambiguation.
        id: Optional explicit message ID.
        max_chars: Optional max character constraint.
        format: Data format — ``"ICU"`` (default), ``"STRING"``, or ``"I18NEXT"``.

    Returns:
        A hex hash string.
    """
    source = index_vars(message) if format == "ICU" else message
    return hash_source(
        source,
        context=context,
        id=id,
        max_chars=max_chars,
        data_format=format,
    )
