from __future__ import annotations

from generaltranslation_icu_messageformat_parser import print_ast

from generaltranslation.static._constants import VAR_IDENTIFIER
from generaltranslation.static._traverse_icu import is_gt_indexed_select, traverse_icu


def condense_vars(icu_string: str) -> str:
    """Condense indexed ``_gt_`` selects to simple variable references.

    Transforms ``{_gt_1, select, other {value}}`` into ``{_gt_1}``.

    Args:
        icu_string: An ICU MessageFormat string with indexed GT variables.

    Returns:
        The string with indexed GT selects collapsed to argument references.
    """
    if VAR_IDENTIFIER not in icu_string:
        return icu_string

    def visitor(child: dict) -> None:
        # Mutate select node into a simple variable node
        child.pop("type", None)
        child.pop("options", None)
        child.pop("offset", None)

    ast = traverse_icu(
        icu_string,
        is_gt_indexed_select,
        visitor,
        recurse_into_visited=False,
    )

    return print_ast(ast)
