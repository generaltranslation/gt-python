"""String cutoff formatting with locale-aware terminators.

Ports ``CutoffFormat`` from the JS core library.
"""

from __future__ import annotations

from generaltranslation.formatting._helpers import _get_language_code

# Default style when maxChars is set
DEFAULT_CUTOFF_FORMAT_STYLE = "ellipsis"

# Terminator configurations per style and language
TERMINATOR_MAP: dict[str, dict[str, dict[str, str | None]]] = {
    "ellipsis": {
        "fr": {
            "terminator": "\u2026",  # …
            "separator": "\u202f",  # narrow no-break space
        },
        "zh": {
            "terminator": "\u2026\u2026",  # ……
            "separator": None,
        },
        "ja": {
            "terminator": "\u2026\u2026",  # ……
            "separator": None,
        },
        "_default": {
            "terminator": "\u2026",  # …
            "separator": None,
        },
    },
    "none": {
        "_default": {
            "terminator": None,
            "separator": None,
        },
    },
}


class CutoffFormat:
    """Format strings with cutoff behavior and locale-aware terminators.

    Args:
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options.

            - ``max_chars`` (int | None): Maximum character count.
              ``None`` means no cutoff. Negative values truncate from
              the start.
            - ``style``: ``"ellipsis"`` (default) or ``"none"``.
            - ``terminator``: Override the terminator string.
            - ``separator``: Override the separator between value and
              terminator.
    """

    def __init__(
        self,
        locales: str | list[str] | None = None,
        options: dict | None = None,
    ) -> None:
        if options is None:
            options = {}

        max_chars = options.get("max_chars")
        style_input = options.get("style", DEFAULT_CUTOFF_FORMAT_STYLE)

        # Validate style
        if style_input not in TERMINATOR_MAP:
            raise ValueError(
                f"Invalid cutoff format style: {style_input!r}. "
                f"Must be one of: {', '.join(TERMINATOR_MAP.keys())}"
            )

        # Resolve terminator options
        style: str | None = None
        preset: dict[str, str | None] | None = None
        if max_chars is not None:
            style = style_input
            lang = _get_language_code(locales)
            style_map = TERMINATOR_MAP[style]
            preset = style_map.get(lang, style_map["_default"])

        terminator = options.get(
            "terminator", preset.get("terminator") if preset else None
        )
        separator: str | None = None
        if terminator is not None:
            separator = options.get(
                "separator", preset.get("separator") if preset else None
            )

        # Calculate addition length
        self._addition_length = (len(terminator) if terminator else 0) + (
            len(separator) if separator else 0
        )

        # If maxChars doesn't have enough space for terminator+separator, drop them
        if max_chars is not None and abs(max_chars) < self._addition_length:
            terminator = None
            separator = None
            self._addition_length = 0

        self._options = {
            "max_chars": max_chars,
            "style": style,
            "terminator": terminator,
            "separator": separator,
        }

    def format(self, value: str) -> str:
        """Format a string with cutoff behavior.

        Args:
            value: The string to format.

        Returns:
            The formatted string with terminator applied if cutoff occurs.
        """
        return "".join(self.format_to_parts(value))

    def format_to_parts(self, value: str) -> list[str]:
        """Format a string and return the individual parts.

        Args:
            value: The string to format.

        Returns:
            A list of string parts:
            - Positive max_chars: ``[sliced_value, separator?, terminator?]``
            - Negative max_chars: ``[terminator?, separator?, sliced_value]``
            - No cutoff: ``[original_value]``
        """
        max_chars = self._options["max_chars"]
        terminator = self._options["terminator"]
        separator = self._options["separator"]

        # Calculate adjusted cutoff
        if max_chars is None or abs(max_chars) >= len(value):
            adjusted_chars = max_chars
        elif max_chars >= 0:
            adjusted_chars = max(0, max_chars - self._addition_length)
        else:
            adjusted_chars = min(0, max_chars + self._addition_length)

        # Slice the value
        if adjusted_chars is not None and adjusted_chars > -1:
            sliced_value = value[:adjusted_chars]
        else:
            sliced_value = value[adjusted_chars:]

        # No cutoff / no terminator → value only
        if (
            max_chars is None
            or adjusted_chars is None
            or adjusted_chars == 0
            or terminator is None
            or len(value) <= abs(max_chars)
        ):
            return [sliced_value]

        # Postpended cutoff (positive max_chars)
        if adjusted_chars > 0:
            parts = [sliced_value]
            if separator is not None:
                parts.append(separator)
            parts.append(terminator)
            return parts

        # Prepended cutoff (negative max_chars)
        parts = [terminator]
        if separator is not None:
            parts.append(separator)
        parts.append(sliced_value)
        return parts

    def resolved_options(self) -> dict:
        """Return the resolved formatting options.

        Returns:
            A dict with ``max_chars``, ``style``, ``terminator``,
            ``separator``.
        """
        return dict(self._options)


def format_cutoff(
    value: str,
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> str:
    """Format a string with cutoff behavior.

    Convenience function wrapping :class:`CutoffFormat`.

    Args:
        value: The string to format.
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Cutoff formatting options (see :class:`CutoffFormat`).

    Returns:
        The formatted string with terminator applied if cutoff occurs.
    """
    return CutoffFormat(locales, options).format(value)
