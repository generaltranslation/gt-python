from __future__ import annotations

from generaltranslation.static._constants import VAR_IDENTIFIER
from generaltranslation.static._traverse_icu import is_gt_unindexed_select, traverse_icu


def _find_other_span(
    icu_string: str, node_start: int, node_end: int
) -> tuple[int, int]:
    """Find the ``{content}`` span of the ``other`` option within a select node.

    Returns ``(brace_open, brace_close_exclusive)`` — the positions of the
    opening ``{`` and one past the closing ``}`` of the ``other`` option's content
    block in *icu_string*.
    """
    s = icu_string
    i = node_start

    # Skip opening '{'
    i += 1

    # Skip whitespace
    while i < node_end and s[i] in " \t\n\r":
        i += 1

    # Skip variable name
    while i < node_end and s[i] not in " \t\n\r,{}":
        i += 1

    # Skip whitespace
    while i < node_end and s[i] in " \t\n\r":
        i += 1

    # Skip comma after name
    if i < node_end and s[i] == ",":
        i += 1

    # Skip whitespace
    while i < node_end and s[i] in " \t\n\r":
        i += 1

    # Skip type name (e.g., "select")
    while i < node_end and s[i] not in " \t\n\r,{}":
        i += 1

    # Skip whitespace
    while i < node_end and s[i] in " \t\n\r":
        i += 1

    # Skip comma after type
    if i < node_end and s[i] == ",":
        i += 1

    # Now we're in the submessage area — parse selector {content} pairs
    while i < node_end:
        # Skip whitespace
        while i < node_end and s[i] in " \t\n\r":
            i += 1

        if i >= node_end or s[i] == "}":
            break

        # Read selector name
        sel_start = i
        while i < node_end and s[i] not in " \t\n\r{}":
            i += 1
        selector = s[sel_start:i]

        # Skip whitespace before '{'
        while i < node_end and s[i] in " \t\n\r":
            i += 1

        if i >= node_end or s[i] != "{":
            break

        # Find matching '}'
        brace_start = i
        depth = 1
        i += 1
        while i < node_end and depth > 0:
            c = s[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == "'":
                # ICU escape — skip past escaped content
                i += 1
                if i < node_end and s[i] == "'":
                    # Doubled quote ''
                    pass
                else:
                    # Escaped block until next unescaped single quote
                    while i < node_end and s[i] != "'":
                        i += 1
            i += 1
        brace_end = i  # one past closing '}'

        if selector == "other":
            return (brace_start, brace_end)

    # Fallback — should not happen for valid GT selects
    return (node_end, node_end)


def index_vars(icu_string: str) -> str:
    """Add numeric indices to unindexed ``_gt_`` selects and collapse their ``other`` content.

    Transforms ``{_gt_, select, other {value}}`` into ``{_gt_1, select, other {}}``.

    Args:
        icu_string: An ICU MessageFormat string with unindexed GT variables.

    Returns:
        The string with indexed GT variables and empty ``other`` options.
    """
    if VAR_IDENTIFIER not in icu_string:
        return icu_string

    locations: list[tuple[int, int, int, int]] = []

    def visitor(child: dict) -> None:
        node_start = child.get("start", 0)
        node_end = child.get("end", 0)
        other_start, other_end = _find_other_span(icu_string, node_start, node_end)
        locations.append((node_start, node_end, other_start, other_end))

    traverse_icu(
        icu_string,
        is_gt_unindexed_select,
        visitor,
        recurse_into_visited=False,
        include_indices=True,
    )

    result: list[str] = []
    current = 0
    for i, (start, end, other_start, other_end) in enumerate(locations):
        # Before the variable
        result.append(icu_string[current:start])
        # {_gt_ (opening brace + identifier)
        result.append(icu_string[start : start + len(VAR_IDENTIFIER) + 1])
        # Index number
        result.append(str(i + 1))
        # From after the identifier to start of other's {content}
        result.append(icu_string[start + len(VAR_IDENTIFIER) + 1 : other_start])
        # Collapsed other
        result.append("{}")
        # After other's {content} to end of select
        result.append(icu_string[other_end:end])
        current = end

    result.append(icu_string[current:])

    return "".join(result)
