"""ICU MessageFormat formatter.

A Python equivalent of ``intl-messageformat``. Formats ICU MessageFormat
strings with locale-aware plural and select rules using Babel's CLDR data.
"""

from __future__ import annotations

from babel import Locale
from babel.core import UnknownLocaleError
from babel.numbers import format_decimal
from generaltranslation_icu_messageformat_parser import Parser

_parser = Parser()


class IntlMessageFormat:
    """Format ICU MessageFormat strings with variable interpolation.

    Args:
        pattern: An ICU MessageFormat pattern string.
        locale: A BCP 47 locale tag (default ``"en"``).

    Example::

        mf = IntlMessageFormat("{count, plural, one {# item} other {# items}}", "en")
        mf.format({"count": 5})  # "5 items"
    """

    def __init__(self, pattern: str, locale: str = "en") -> None:
        self._pattern = pattern
        self._ast = _parser.parse(pattern)
        try:
            self._locale = Locale.parse(locale, sep="-")
        except (UnknownLocaleError, ValueError):
            self._locale = Locale("en")

    @property
    def pattern(self) -> str:
        """The original pattern string."""
        return self._pattern

    @property
    def locale(self) -> Locale:
        """The resolved Babel locale."""
        return self._locale

    def format(self, values: dict | None = None) -> str:
        """Format the message with the given variable values.

        Args:
            values: A dict mapping variable names to their values.

        Returns:
            The formatted message string.
        """
        return _render(self._ast, values or {}, self._locale)


def _render(
    nodes: list,
    values: dict,
    locale: Locale,
    plural_value: float | None = None,
) -> str:
    """Render an AST node list to a string."""
    parts: list[str] = []
    for node in nodes:
        if isinstance(node, str):
            parts.append(node)
        elif isinstance(node, dict):
            parts.append(_render_node(node, values, locale, plural_value))
    return "".join(parts)


def _render_node(
    node: dict,
    values: dict,
    locale: Locale,
    plural_value: float | None,
) -> str:
    """Render a single AST node."""
    name = node.get("name", "")
    node_type = node.get("type")

    # Hash (#) replacement inside plural branches
    if node.get("hash") and plural_value is not None:
        return _format_number(plural_value, locale)

    # Simple variable: {name}
    if node_type is None:
        return str(values.get(name, ""))

    # Plural / selectordinal
    if node_type in ("plural", "selectordinal"):
        raw = values.get(name, 0)
        try:
            num_value = float(raw) if not isinstance(raw, (int, float)) else raw
        except (TypeError, ValueError):
            num_value = 0

        offset = node.get("offset", 0)
        adjusted = num_value - offset
        options = node.get("options", {})

        # 1. Exact match (=N)
        if num_value == int(num_value):
            exact_key = f"={int(num_value)}"
        else:
            exact_key = f"={num_value}"

        # The value used for # substitution is the offset-adjusted value
        hash_value = adjusted

        if exact_key in options:
            return _render(options[exact_key], values, locale, hash_value)

        # 2. CLDR plural category
        try:
            if node_type == "selectordinal":
                category = locale.ordinal_form(abs(adjusted))
            else:
                category = locale.plural_form(abs(adjusted))
        except Exception:
            category = "one" if abs(adjusted) == 1 else "other"

        if category in options:
            return _render(options[category], values, locale, hash_value)

        # 3. Fallback to "other"
        if "other" in options:
            return _render(options["other"], values, locale, hash_value)

        return ""

    # Select
    if node_type == "select":
        val = str(values.get(name, ""))
        options = node.get("options", {})

        if val in options:
            return _render(options[val], values, locale, plural_value)
        if "other" in options:
            return _render(options["other"], values, locale, plural_value)
        return ""

    # Unknown type — treat as simple variable
    return str(values.get(name, ""))


def _format_number(value: float, locale: Locale) -> str:
    """Format a number for ``#`` substitution in plural branches.

    Uses locale-aware number formatting (with grouping separators)
    to match ICU behavior (e.g. 1000 → "1,000" in English).
    """
    if isinstance(value, float) and value == int(value):
        value = int(value)
    return format_decimal(value, locale=locale)
