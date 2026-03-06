"""Interpolate an ICU message string with variables.

Port of ``interpolateMessage.ts`` from the JS gt-i18n package.
"""

from __future__ import annotations

from generaltranslation.formatting._format_cutoff import format_cutoff
from generaltranslation.formatting._format_message import format_message
from generaltranslation.static._condense_vars import condense_vars
from generaltranslation.static._constants import VAR_IDENTIFIER
from generaltranslation.static._extract_vars import extract_vars

from gt_i18n.translation_functions._extract_variables import extract_variables


def interpolate_message(
    message: str,
    options: dict[str, object],
    locale: str | None = None,
) -> str:
    """Interpolate variables into an ICU message string.

    Mirrors JS ``interpolateMessage()`` behavior:

    1. Extract user variables (filter out ``$``-prefixed keys).
    2. Extract ``_gt_`` declared variables from the source/fallback.
    3. Condense ``_gt_`` selects to simple refs (only if declared vars exist).
    4. Format with ICU MessageFormat.
    5. Apply ``$max_chars`` cutoff if specified.

    On error:
    - If ``$_fallback`` (source) is available, recursively retry with
      the source message (clearing ``$_fallback`` to prevent infinite loop).
    - Otherwise, return the raw message with cutoff applied.

    Args:
        message: The ICU MessageFormat string to interpolate.
        options: Variables and GT options.
        locale: Optional locale for formatting.

    Returns:
        The interpolated string.
    """
    source = options.get("$_fallback")
    max_chars = options.get("$max_chars")

    # Remove GT-related options, keep user variables
    variables = extract_variables(options)

    try:
        # Extract declared _gt_ variable values from the source/fallback
        declared_vars = extract_vars(source if isinstance(source, str) else "")

        # Condense indexed selects to simple argument refs only if
        # declared vars exist
        if declared_vars:
            condensed = condense_vars(message)
        else:
            condensed = message

        # Build the full variables dict: user vars + declared vars + _gt_ sentinel
        all_vars = {
            **variables,
            **declared_vars,
            VAR_IDENTIFIER: "other",
        }

        # Format with ICU MessageFormat
        result = format_message(condensed, locale, all_vars)

        # Apply cutoff formatting
        if max_chars is not None:
            result = format_cutoff(
                result, locale, {"max_chars": int(max_chars)}
            )

        return result

    except Exception:
        # If formatting the translation failed and we have a fallback,
        # try formatting the source instead (recursive retry)
        if source is not None and isinstance(source, str):
            return interpolate_message(
                source,
                {**options, "$_fallback": None},
                locale,
            )

        # No fallback — return the raw message with cutoff applied
        if max_chars is not None:
            return format_cutoff(
                message, locale, {"max_chars": int(max_chars)}
            )

        return message
