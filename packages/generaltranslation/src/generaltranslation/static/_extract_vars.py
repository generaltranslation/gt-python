from __future__ import annotations

from generaltranslation.static._constants import VAR_IDENTIFIER
from generaltranslation.static._traverse_icu import traverse_icu, is_gt_unindexed_select


def extract_vars(icu_string: str) -> dict[str, str]:
    """Extract ``_gt_`` variables from an ICU string into an indexed mapping.

    Args:
        icu_string: An ICU MessageFormat string with unindexed GT variables.

    Returns:
        A dict mapping ``_gt_1``, ``_gt_2``, … to their ``other`` option values.
    """
    if VAR_IDENTIFIER not in icu_string:
        return {}

    variables: dict[str, str] = {}
    index = [1]

    def visitor(child: dict) -> None:
        other = child["options"]["other"]
        variables[child["name"] + str(index[0])] = other[0] if other else ""
        index[0] += 1

    traverse_icu(
        icu_string,
        is_gt_unindexed_select,
        visitor,
        recurse_into_visited=False,
    )

    return variables
