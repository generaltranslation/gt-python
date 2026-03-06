"""Interpolate an ICU message string with variables."""

from __future__ import annotations

from generaltranslation.formatting._format_cutoff import format_cutoff
from generaltranslation.formatting._format_message import format_message
from generaltranslation.static._condense_vars import condense_vars
from generaltranslation.static._extract_vars import extract_vars

from gt_i18n.translation_functions._extract_variables import extract_variables


def interpolate_message(
    message: str,
    options: dict[str, object],
    locale: str | None = None,
) -> str:
    """Interpolate variables into an ICU message string.

    Pipeline:
    1. Extract user variables (filter out ``$``-prefixed keys).
    2. Extract ``_gt_`` declared variables from the message.
    3. Condense ``_gt_`` selects to simple references.
    4. Format with ICU MessageFormat.
    5. Apply ``$max_chars`` cutoff if specified.

    Falls back to the ``$_fallback`` message or original *message*
    on any error.

    Args:
        message: The ICU MessageFormat string to interpolate.
        options: Variables and GT options (``$context``, ``$max_chars``, etc.).
        locale: Optional locale for formatting.

    Returns:
        The interpolated string.
    """
    fallback = options.get("$_fallback", message)
    max_chars = options.get("$max_chars")

    try:
        user_vars = extract_variables(options)

        # Extract declared _gt_ variables from the message
        gt_vars = extract_vars(message)

        # Merge: user variables + extracted _gt_ variables
        all_vars = {**gt_vars, **user_vars} if gt_vars else dict(user_vars)

        # Condense _gt_ selects to simple references
        condensed = condense_vars(message)

        # Format with ICU MessageFormat
        result = format_message(condensed, locale, all_vars or None)

        # Apply max_chars cutoff
        if max_chars is not None:
            result = format_cutoff(
                result, locale, {"max_chars": int(max_chars)}
            )

        return result
    except Exception:
        # Fallback: try to return the fallback message as-is
        if isinstance(fallback, str):
            return fallback
        return str(message)
