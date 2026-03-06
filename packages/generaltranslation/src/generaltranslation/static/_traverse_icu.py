from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from generaltranslation_icu_messageformat_parser import Parser


def traverse_icu(
    icu_string: str,
    should_visit: Callable[[dict], bool],
    visitor: Callable[[dict], None],
    *,
    recurse_into_visited: bool = True,
    include_indices: bool = False,
    preserve_whitespace: bool = False,
) -> list:
    """Parse an ICU string and traverse the AST, calling *visitor* on matching nodes.

    Args:
        icu_string: The ICU MessageFormat string to traverse.
        should_visit: Predicate returning ``True`` for nodes to visit.
        visitor: Called for each node where *should_visit* returns ``True``.
        recurse_into_visited: If ``False``, skip recursing into children of visited nodes.
        include_indices: If ``True``, include ``start``/``end`` on AST nodes.

    Returns:
        The (possibly mutated) AST.
    """
    parser = Parser(
        {
            "include_indices": include_indices,
            "require_other": False,
            "preserve_whitespace": preserve_whitespace,
        }
    )
    ast = parser.parse(icu_string)

    def handle_children(children: list) -> None:
        for child in children:
            handle_child(child)

    def handle_child(child: str | dict[str, Any]) -> None:
        if isinstance(child, str):
            return

        visited = False
        if should_visit(child):
            visitor(child)
            visited = True

        if not visited or recurse_into_visited:
            node_type = child.get("type")
            if node_type in ("select", "plural", "selectordinal"):
                for key, value in child.get("options", {}).items():
                    if key == "_ws":
                        continue
                    handle_children(value)
            elif node_type == "tag":
                handle_children(child.get("contents", []))

    handle_children(ast)
    return ast


_GT_INDEXED_RE = re.compile(r"^_gt_\d+$")


def is_gt_indexed_select(node: dict) -> bool:
    """Return ``True`` if *node* is a ``_gt_<number>`` select element."""
    return (
        node.get("type") == "select"
        and bool(_GT_INDEXED_RE.match(node.get("name", "")))
        and "other" in node.get("options", {})
        and (len(node["options"]["other"]) == 0 or isinstance(node["options"]["other"][0], str))
    )


def is_gt_unindexed_select(node: dict) -> bool:
    """Return ``True`` if *node* is an exact ``_gt_`` select element."""
    return (
        node.get("type") == "select"
        and node.get("name", "") == "_gt_"
        and "other" in node.get("options", {})
        and (len(node["options"]["other"]) == 0 or isinstance(node["options"]["other"][0], str))
    )
