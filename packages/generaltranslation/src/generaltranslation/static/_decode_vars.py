from __future__ import annotations

from generaltranslation.static._constants import VAR_IDENTIFIER
from generaltranslation.static._traverse_icu import traverse_icu, is_gt_unindexed_select


def decode_vars(icu_string: str) -> str:
    """Replace ``{_gt_, select, other {value}}`` constructs with their values.

    Args:
        icu_string: An ICU MessageFormat string potentially containing GT variables.

    Returns:
        The string with GT variable selects replaced by their embedded values.
    """
    if VAR_IDENTIFIER not in icu_string:
        return icu_string

    variable_locations: list[tuple[int, int, str]] = []

    def visitor(child: dict) -> None:
        other = child["options"]["other"]
        value = other[0] if other else ""
        variable_locations.append((child.get("start", 0), child.get("end", 0), value))

    traverse_icu(
        icu_string,
        is_gt_unindexed_select,
        visitor,
        recurse_into_visited=False,
        include_indices=True,
    )

    parts: list[str] = []
    prev = 0
    for start, end, value in variable_locations:
        parts.append(icu_string[prev:start])
        parts.append(value)
        prev = end
    if prev < len(icu_string):
        parts.append(icu_string[prev:])

    return "".join(parts)
