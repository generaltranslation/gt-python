"""ICU MessageFormat parser and formatter.

Ports ``intl-messageformat`` usage from the JS core library as a
lightweight recursive-descent parser supporting:

1. ``{varName}`` — simple variable interpolation
2. ``{count, plural, one {# item} other {# items}}`` — plural selection
3. ``{gender, select, male {He} female {She} other {They}}`` — select
4. Nested expressions within branches
5. ``#`` replacement with numeric value inside plural branches

Uses Babel's CLDR plural rules for plural category selection.
"""

from __future__ import annotations

from babel import Locale
from babel.core import UnknownLocaleError

from generaltranslation.formatting._helpers import _resolve_babel_locale


def format_message(
    message: str,
    locales: str | list[str] | None = None,
    variables: dict | None = None,
) -> str:
    """Format an ICU MessageFormat string.

    Args:
        message: The ICU message pattern (e.g.
            ``"{count, plural, one {# item} other {# items}}"``).
        locales: BCP 47 locale tag(s) for plural rule selection.
            Defaults to ``"en"``.
        variables: Variable values to substitute.

    Returns:
        The formatted message string.
    """
    if variables is None:
        variables = {}

    locale = _resolve_babel_locale(locales)
    tokens = _tokenize(message)
    result, _ = _parse_message(tokens, 0, variables, locale, None)
    return result


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

def _tokenize(message: str) -> list[str]:
    """Split an ICU message into tokens.

    Tokens are: ``{``, ``}``, ``#``, ``,``, and text runs.
    Escaped characters (``'{...}'``) produce literal text.
    """
    tokens: list[str] = []
    i = 0
    buf: list[str] = []

    def flush():
        if buf:
            tokens.append("".join(buf))
            buf.clear()

    while i < len(message):
        ch = message[i]

        # ICU escape: single-quote delimited literal
        if ch == "'":
            i += 1
            if i < len(message) and message[i] == "'":
                # Escaped single quote ''
                buf.append("'")
                i += 1
            else:
                # Quoted literal: collect until closing '
                while i < len(message) and message[i] != "'":
                    buf.append(message[i])
                    i += 1
                if i < len(message):
                    i += 1  # skip closing '
        elif ch in "{}#,":
            flush()
            tokens.append(ch)
            i += 1
        else:
            buf.append(ch)
            i += 1

    flush()
    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_message(
    tokens: list[str],
    pos: int,
    variables: dict,
    locale: Locale,
    plural_value: float | None,
) -> tuple[str, int]:
    """Parse a message sequence until ``}`` or end of tokens.

    Returns:
        ``(formatted_string, next_position)``
    """
    parts: list[str] = []

    while pos < len(tokens):
        tok = tokens[pos]

        if tok == "}":
            # End of current block
            break

        if tok == "{":
            # Start of an expression
            text, pos = _parse_expression(tokens, pos + 1, variables, locale, plural_value)
            parts.append(text)
            continue

        if tok == "#":
            # # replacement inside plural branches
            if plural_value is not None:
                parts.append(_format_plural_number(plural_value))
            else:
                parts.append("#")
            pos += 1
            continue

        # Plain text or comma
        parts.append(tok)
        pos += 1

    return "".join(parts), pos


def _parse_expression(
    tokens: list[str],
    pos: int,
    variables: dict,
    locale: Locale,
    plural_value: float | None,
) -> tuple[str, int]:
    """Parse an ``{...}`` expression starting after the ``{``.

    Handles:
    - ``{varName}`` — simple substitution
    - ``{varName, plural, ...}`` — plural selection
    - ``{varName, select, ...}`` — select branching
    - ``{varName, selectordinal, ...}`` — ordinal selection

    Returns:
        ``(formatted_string, next_position)``
    """
    # Collect the variable name (skip whitespace tokens)
    var_name = ""
    while pos < len(tokens) and tokens[pos] not in (",", "}"):
        var_name += tokens[pos]
        pos += 1

    var_name = var_name.strip()

    if pos >= len(tokens) or tokens[pos] == "}":
        # Simple variable: {varName}
        val = variables.get(var_name, "")
        return str(val), pos + 1  # skip }

    # Skip comma
    pos += 1

    # Get the type keyword (plural, select, selectordinal, number, etc.)
    type_keyword = ""
    while pos < len(tokens) and tokens[pos] not in (",", "}"):
        type_keyword += tokens[pos]
        pos += 1

    type_keyword = type_keyword.strip().lower()

    if pos >= len(tokens) or tokens[pos] == "}":
        # {varName, type} with no branches — treat as simple variable
        return str(variables.get(var_name, "")), pos + 1

    # Skip comma before branches
    pos += 1

    if type_keyword == "plural" or type_keyword == "selectordinal":
        return _parse_plural(tokens, pos, var_name, variables, locale, type_keyword)
    elif type_keyword == "select":
        return _parse_select(tokens, pos, var_name, variables, locale, plural_value)
    else:
        # Unknown type, just format as simple variable
        # Skip to closing }
        depth = 1
        while pos < len(tokens) and depth > 0:
            if tokens[pos] == "{":
                depth += 1
            elif tokens[pos] == "}":
                depth -= 1
            pos += 1
        return str(variables.get(var_name, "")), pos


def _parse_plural(
    tokens: list[str],
    pos: int,
    var_name: str,
    variables: dict,
    locale: Locale,
    type_keyword: str,
) -> tuple[str, int]:
    """Parse plural/selectordinal branches.

    Branch syntax: ``one {text} other {text}`` with optional ``=N {text}``
    for exact matches and ``offset:N`` for offset.
    """
    var_value = variables.get(var_name, 0)
    try:
        num_value = float(var_value)
    except (TypeError, ValueError):
        num_value = 0

    # Parse offset if present
    offset = 0
    # Check for offset:N
    if pos < len(tokens) and tokens[pos].strip().startswith("offset:"):
        offset_str = tokens[pos].strip()
        try:
            offset = int(offset_str.split(":")[1])
        except (ValueError, IndexError):
            pass
        pos += 1

    adjusted_value = num_value - offset

    # Collect branches: {keyword: (token_start, token_end)}
    branches: dict[str, tuple[int, int]] = {}
    while pos < len(tokens) and tokens[pos] != "}":
        # Get branch keyword (skip whitespace)
        keyword = tokens[pos].strip()
        pos += 1

        if not keyword:
            continue

        if pos >= len(tokens) or tokens[pos] != "{":
            continue

        # Skip the opening {
        pos += 1

        # Record start position of branch content
        start = pos

        # Find the matching closing }
        depth = 1
        while pos < len(tokens) and depth > 0:
            if tokens[pos] == "{":
                depth += 1
            elif tokens[pos] == "}":
                depth -= 1
                if depth == 0:
                    break
            pos += 1

        branches[keyword] = (start, pos)
        pos += 1  # skip closing }

    # Select the right branch
    # 1. Exact match (=N)
    exact_key = f"={int(num_value)}" if num_value == int(num_value) else f"={num_value}"
    if exact_key in branches:
        branch_start, branch_end = branches[exact_key]
        result, _ = _parse_message(
            tokens, branch_start, variables, locale, num_value
        )
        return result, pos + 1  # skip outer }

    # 2. CLDR plural category
    if type_keyword == "selectordinal":
        category = _get_ordinal_category(adjusted_value, locale)
    else:
        category = _get_plural_category(adjusted_value, locale)

    if category in branches:
        branch_start, branch_end = branches[category]
        result, _ = _parse_message(
            tokens, branch_start, variables, locale, num_value
        )
        return result, pos + 1

    # 3. Fallback to "other"
    if "other" in branches:
        branch_start, branch_end = branches["other"]
        result, _ = _parse_message(
            tokens, branch_start, variables, locale, num_value
        )
        return result, pos + 1

    # 4. No matching branch
    return "", pos + 1


def _parse_select(
    tokens: list[str],
    pos: int,
    var_name: str,
    variables: dict,
    locale: Locale,
    plural_value: float | None,
) -> tuple[str, int]:
    """Parse select branches."""
    var_value = str(variables.get(var_name, ""))

    # Collect branches
    branches: dict[str, tuple[int, int]] = {}
    while pos < len(tokens) and tokens[pos] != "}":
        keyword = tokens[pos].strip()
        pos += 1

        if not keyword:
            continue

        if pos >= len(tokens) or tokens[pos] != "{":
            continue

        pos += 1  # skip {
        start = pos

        depth = 1
        while pos < len(tokens) and depth > 0:
            if tokens[pos] == "{":
                depth += 1
            elif tokens[pos] == "}":
                depth -= 1
                if depth == 0:
                    break
            pos += 1

        branches[keyword] = (start, pos)
        pos += 1  # skip }

    # Select matching branch
    if var_value in branches:
        branch_start, branch_end = branches[var_value]
        result, _ = _parse_message(
            tokens, branch_start, variables, locale, plural_value
        )
        return result, pos + 1

    # Fallback to "other"
    if "other" in branches:
        branch_start, branch_end = branches["other"]
        result, _ = _parse_message(
            tokens, branch_start, variables, locale, plural_value
        )
        return result, pos + 1

    return "", pos + 1


# ---------------------------------------------------------------------------
# Plural helpers
# ---------------------------------------------------------------------------

def _get_plural_category(n: float, locale: Locale) -> str:
    """Get CLDR plural category for a cardinal number."""
    try:
        return locale.plural_form(abs(n))
    except Exception:
        # English fallback
        return "one" if abs(n) == 1 else "other"


def _get_ordinal_category(n: float, locale: Locale) -> str:
    """Get CLDR plural category for an ordinal number."""
    try:
        return locale.ordinal_form(abs(n))
    except Exception:
        # English ordinal fallback
        n_int = int(abs(n))
        mod10 = n_int % 10
        mod100 = n_int % 100
        if mod10 == 1 and mod100 != 11:
            return "one"
        if mod10 == 2 and mod100 != 12:
            return "two"
        if mod10 == 3 and mod100 != 13:
            return "few"
        return "other"


def _format_plural_number(value: float) -> str:
    """Format a number for # substitution in plural branches."""
    if value == int(value):
        return str(int(value))
    return str(value)
